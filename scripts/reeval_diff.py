#!/usr/bin/env python3
"""
reeval_diff.py — compare two evaluation states of the same repo.

Usage:
    # Compare working tree against a past commit
    scripts/reeval_diff.py repos/owner--repo --from HEAD~5 --to working

    # Compare two commits
    scripts/reeval_diff.py repos/owner--repo --from 45d6c91 --to HEAD

    # Write diff artifacts to a directory
    scripts/reeval_diff.py repos/owner--repo --from HEAD~5 --to working \\
        --output repos/owner--repo/diffs/2026-04-07-HEAD~5_to_working

    # Output formats
    scripts/reeval_diff.py ... --md       # human-readable markdown on stdout
    scripts/reeval_diff.py ... --json     # machine-readable JSON on stdout
    scripts/reeval_diff.py ... --yaml     # YAML on stdout (default)

A snapshot is a tuple of (repo_meta, claims, verdict_bucket, runs,
provenance_quality, coverage_gap_report) for a given reference point.
Reference points are either git refs (`HEAD`, `45d6c91`, `main`) or
the literal string `working` which reads the current filesystem state.

Design principles:
- Git is the source of truth. Historical state is read via
  `git show <ref>:<path>`, not reconstructed from anywhere else.
- The tool never mutates anything. All output is to stdout or to
  files the caller explicitly names via --output.
- Missing data is preserved truthfully. If a baseline has no
  provenance or no verdict, the diff says so instead of guessing.
- Every comparison carries a `comparison_confidence` field so
  readers know whether to trust the result.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("reeval_diff.py: PyYAML required", file=sys.stderr)
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Import coverage gap detector so we can compute gap state per snapshot.
sys.path.insert(0, str(ROOT / "scripts"))
import coverage_gap_detector as cgd  # noqa: E402


# --- Domain model ---------------------------------------------------------


BUCKETS = ["unknown", "unusable", "usable", "reusable", "recommendable"]
BUCKET_RANK = {b: i for i, b in enumerate(BUCKETS)}

# Claim status normalization — must match verdict_calculator.py's table
PASS_STATUSES = {"passed", "pass", "passed_with_concerns", "pass-with-concerns"}
FAIL_STATUSES = {"failed", "fail", "failed_partial", "fail-partial"}
UNTESTED_STATUSES = {"untested", "pending", "unknown", ""}


def normalize_status(s: Any) -> str:
    if s is None:
        return "untested"
    norm = str(s).lower().replace(" ", "_")
    if norm in PASS_STATUSES:
        return "passed"
    if norm in FAIL_STATUSES:
        return "failed"
    if norm in UNTESTED_STATUSES:
        return "untested"
    return "unknown"


# --- Transition classification -------------------------------------------


# Every (from, to) pair of normalized statuses maps to one of:
#   improvement  — clearly better
#   regression   — clearly worse
#   newly_failing — was untested, now failing (new bad news, but real info)
#   unchanged    — no meaningful change
TRANSITION_TABLE: dict[tuple[str, str], str] = {
    ("untested", "untested"): "unchanged",
    ("untested", "passed"): "improvement",
    ("untested", "failed"): "newly_failing",
    ("passed", "passed"): "unchanged",
    ("passed", "untested"): "regression",
    ("passed", "failed"): "regression",
    ("failed", "failed"): "unchanged",
    ("failed", "passed"): "improvement",
    ("failed", "untested"): "regression",
}


def classify_transition(from_status: str, to_status: str) -> str:
    f = normalize_status(from_status)
    t = normalize_status(to_status)
    key = (f, t)
    return TRANSITION_TABLE.get(key, "unknown")


def classify_bucket_change(
    from_bucket: str | None, to_bucket: str | None
) -> str:
    f = str(from_bucket or "unknown").lower()
    t = str(to_bucket or "unknown").lower()
    if f not in BUCKET_RANK:
        f = "unknown"
    if t not in BUCKET_RANK:
        t = "unknown"
    if f == t:
        return "unchanged"
    if f == "unknown" or t == "unknown":
        return "unclassifiable"
    fr = BUCKET_RANK[f]
    tr = BUCKET_RANK[t]
    if tr > fr:
        return "improvement"
    if tr < fr:
        return "regression"
    return "unchanged"


# --- Snapshot loading ----------------------------------------------------


@dataclass
class Snapshot:
    ref: str                             # "working" or git ref
    repo_meta: dict = field(default_factory=dict)
    claims: list[dict] = field(default_factory=list)
    verdict_bucket: str | None = None
    verdict_path: str | None = None
    runs: list[dict] = field(default_factory=list)
    provenance_quality: str = "missing"  # full | partial | missing
    gap_report: dict | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def exists(self) -> bool:
        return bool(self.repo_meta or self.claims or self.verdict_bucket)


class SnapshotLoader:
    """Loads repo state at a given ref using Git when possible."""

    def __init__(self, repo_evals_root: pathlib.Path, repo_dir: pathlib.Path):
        # Resolve both sides. On macOS, /var is a symlink to /private/var,
        # so tmp paths produced via tempfile often need canonicalization
        # before relative_to() will succeed.
        self.root = repo_evals_root.resolve()
        self.repo_dir = repo_dir.resolve()
        self.rel = self.repo_dir.relative_to(self.root)

    def resolve_ref(self, ref: str) -> str | None:
        """Resolve a symbolic git ref (HEAD, HEAD~2, branch, short sha)
        to a full short sha. Returns None for 'working' or when git rev-parse
        fails. Used to stamp committed diff artifacts with a reproducible
        reference even when the caller used a relative ref."""
        if ref == "working":
            return None
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--short", ref],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                check=False,
            )
            if r.returncode != 0:
                return None
            return r.stdout.strip() or None
        except (FileNotFoundError, OSError):
            return None

    # --- low level -------------------------------------------------------

    def _git_show(self, ref: str, path: pathlib.PurePosixPath) -> str | None:
        """Return the file content at `ref:path`, or None if missing."""
        try:
            r = subprocess.run(
                ["git", "show", f"{ref}:{path.as_posix()}"],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                check=False,
            )
            if r.returncode != 0:
                return None
            return r.stdout
        except (FileNotFoundError, OSError):
            return None

    def _git_ls_tree(self, ref: str, path: pathlib.PurePosixPath) -> list[str]:
        """List files under path at ref. Returns posix paths (relative to repo-evals root)."""
        try:
            r = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", ref, path.as_posix()],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                check=False,
            )
            if r.returncode != 0:
                return []
            return [line.strip() for line in r.stdout.splitlines() if line.strip()]
        except (FileNotFoundError, OSError):
            return []

    def _read(self, ref: str, rel_path: pathlib.PurePosixPath) -> str | None:
        """Read file content at ref (or working tree if ref == 'working')."""
        if ref == "working":
            p = self.root / rel_path.as_posix()
            if not p.exists():
                return None
            try:
                return p.read_text()
            except (OSError, UnicodeDecodeError):
                return None
        return self._git_show(ref, rel_path)

    def _list_files(self, ref: str, rel_dir: pathlib.PurePosixPath) -> list[pathlib.PurePosixPath]:
        if ref == "working":
            d = self.root / rel_dir.as_posix()
            if not d.exists():
                return []
            return [
                pathlib.PurePosixPath(str(p.relative_to(self.root)))
                for p in d.rglob("*") if p.is_file()
            ]
        return [pathlib.PurePosixPath(p) for p in self._git_ls_tree(ref, rel_dir)]

    # --- high level ------------------------------------------------------

    def load(self, ref: str) -> Snapshot:
        snap = Snapshot(ref=ref)
        rel = pathlib.PurePosixPath(self.rel.as_posix())

        # repo.yaml
        text = self._read(ref, rel / "repo.yaml")
        if text:
            try:
                snap.repo_meta = yaml.safe_load(text) or {}
            except yaml.YAMLError as e:
                snap.errors.append(f"repo.yaml parse error at {ref}: {e}")
        else:
            snap.errors.append(f"repo.yaml not found at {ref}")

        # claim-map.yaml
        text = self._read(ref, rel / "claims" / "claim-map.yaml")
        if text:
            try:
                cm = yaml.safe_load(text) or {}
                snap.claims = cm.get("claims") or []
            except yaml.YAMLError as e:
                snap.errors.append(f"claim-map.yaml parse error at {ref}: {e}")
        else:
            snap.errors.append(f"claim-map.yaml not found at {ref}")

        # Verdict bucket: prefer repo.yaml's current_bucket; fall back to
        # parsing the latest verdict file.
        current_bucket = str(snap.repo_meta.get("current_bucket", "")).lower() if snap.repo_meta else ""
        if current_bucket and current_bucket in BUCKET_RANK:
            snap.verdict_bucket = current_bucket

        # Latest verdict file
        verdict_files = sorted(
            f for f in self._list_files(ref, rel / "verdicts")
            if f.name.endswith("-final-verdict.md")
        )
        if verdict_files:
            latest_verdict = verdict_files[-1]
            snap.verdict_path = latest_verdict.as_posix()
            vtext = self._read(ref, latest_verdict)
            if vtext and not snap.verdict_bucket:
                parsed = _parse_verdict_bucket(vtext)
                if parsed:
                    snap.verdict_bucket = parsed

        # Runs
        run_files = sorted(
            f for f in self._list_files(ref, rel / "runs")
            if f.name == "run-summary.yaml"
        )
        # Also pick up runs under areas/
        area_runs = sorted(
            f for f in self._list_files(ref, rel / "areas")
            if f.name == "run-summary.yaml"
        )
        for rf in run_files + area_runs:
            rtext = self._read(ref, rf)
            if not rtext:
                continue
            try:
                rdata = yaml.safe_load(rtext) or {}
                rdata["_path"] = rf.as_posix()
                snap.runs.append(rdata)
            except yaml.YAMLError as e:
                snap.errors.append(f"{rf} parse error at {ref}: {e}")

        snap.provenance_quality = _provenance_quality(snap.runs)

        # Gap report: computed live against THIS snapshot's claims + plan + runs.
        # We need to write a minimal temp tree for the gap detector, OR
        # call a pure function. The detector's build_report takes a repo
        # dir path, so for git-ref snapshots we skip the live gap report
        # and rely on committed gap-reports/ files. For working-tree
        # snapshots we run it live.
        if ref == "working":
            try:
                snap.gap_report = cgd.build_report(self.root / rel.as_posix())
            except Exception as e:
                snap.errors.append(f"gap detector failed: {e}")
        else:
            # Look for a committed gap report in this snapshot
            gap_files = sorted(
                f for f in self._list_files(ref, rel / "gap-reports")
                if f.name.endswith(".md")
            )
            if gap_files:
                snap.gap_report = {
                    "committed_report_path": gap_files[-1].as_posix(),
                    "summary": None,  # not parsed from markdown
                    "gaps": [],
                }

        return snap


VERDICT_BUCKET_RE = __import__("re").compile(
    r"(?:Final\s+bucket|final_bucket)[\s:`*]*[\`\*]*(unusable|usable|reusable|recommendable)",
    __import__("re").IGNORECASE,
)


def _parse_verdict_bucket(text: str) -> str | None:
    m = VERDICT_BUCKET_RE.search(text)
    if not m:
        return None
    return m.group(1).lower()


def _provenance_quality(runs: list[dict]) -> str:
    """Classify baseline provenance quality:
        full    — every run has provenance.captured == True AND
                  provenance.partial != True
        partial — at least one run has captured=True but others are
                  missing or marked partial
        missing — no runs, or no run has captured=True
    """
    if not runs:
        return "missing"
    captured_full = 0
    captured_partial = 0
    uncaptured = 0
    for r in runs:
        prov = r.get("provenance") or {}
        if prov.get("captured"):
            if prov.get("partial"):
                captured_partial += 1
            else:
                captured_full += 1
        else:
            uncaptured += 1
    if captured_full and not (captured_partial or uncaptured):
        return "full"
    if captured_full or captured_partial:
        return "partial"
    return "missing"


# --- Diff logic ----------------------------------------------------------


def _index_claims(claims: list[dict]) -> dict[str, dict]:
    return {str(c.get("id", "")): c for c in claims if c.get("id")}


def diff_claims(from_claims: list[dict], to_claims: list[dict]) -> dict:
    """Return a dict with keys: added, removed, status_changes,
    priority_changes, title_changes, area_changes."""
    fi = _index_claims(from_claims)
    ti = _index_claims(to_claims)

    fkeys = set(fi)
    tkeys = set(ti)

    added_ids = sorted(tkeys - fkeys)
    removed_ids = sorted(fkeys - tkeys)
    common = sorted(fkeys & tkeys)

    status_changes: list[dict] = []
    priority_changes: list[dict] = []
    title_changes: list[dict] = []
    area_changes: list[dict] = []

    for cid in common:
        fc = fi[cid]
        tc = ti[cid]

        f_status = normalize_status(fc.get("status"))
        t_status = normalize_status(tc.get("status"))
        if f_status != t_status:
            status_changes.append({
                "id": cid,
                "title": tc.get("title") or fc.get("title") or "",
                "priority": tc.get("priority") or fc.get("priority") or "medium",
                "from": f_status,
                "to": t_status,
                "transition": classify_transition(f_status, t_status),
            })

        if str(fc.get("priority", "")).lower() != str(tc.get("priority", "")).lower():
            priority_changes.append({
                "id": cid,
                "from": fc.get("priority"),
                "to": tc.get("priority"),
            })

        if str(fc.get("title", "")).strip() != str(tc.get("title", "")).strip():
            title_changes.append({
                "id": cid,
                "from": fc.get("title"),
                "to": tc.get("title"),
            })

        if str(fc.get("area", "")).strip() != str(tc.get("area", "")).strip():
            area_changes.append({
                "id": cid,
                "from": fc.get("area"),
                "to": tc.get("area"),
            })

    return {
        "added": [_claim_summary(ti[c]) for c in added_ids],
        "removed": [_claim_summary(fi[c]) for c in removed_ids],
        "status_changes": status_changes,
        "priority_changes": priority_changes,
        "title_changes": title_changes,
        "area_changes": area_changes,
    }


def _claim_summary(c: dict) -> dict:
    return {
        "id": c.get("id"),
        "title": c.get("title", ""),
        "priority": c.get("priority", "medium"),
        "status": normalize_status(c.get("status")),
    }


def diff_runs(from_runs: list[dict], to_runs: list[dict]) -> dict:
    """Runs are identified by their _path (relative location).
    We return added/removed/in-both so a reviewer can see which runs
    are new or gone."""
    fp = {r.get("_path"): r for r in from_runs if r.get("_path")}
    tp = {r.get("_path"): r for r in to_runs if r.get("_path")}
    added = sorted(set(tp) - set(fp))
    removed = sorted(set(fp) - set(tp))
    return {
        "from_count": len(fp),
        "to_count": len(tp),
        "added": added,
        "removed": removed,
    }


def diff_gap_reports(
    from_gr: dict | None, to_gr: dict | None
) -> dict:
    """Compare coverage gap reports from the two snapshots.

    When a gap report is a committed markdown file (git-ref snapshots),
    we cannot compute a structured diff — we just expose the path. For
    working-tree snapshots we compare the actual gaps set."""
    out: dict = {
        "baseline_kind": None,
        "head_kind": None,
        "closed": [],
        "opened": [],
        "summary_delta": None,
    }

    def kind(gr):
        if not gr:
            return "missing"
        if "committed_report_path" in gr and not gr.get("gaps"):
            return "committed-markdown"
        return "structured"

    out["baseline_kind"] = kind(from_gr)
    out["head_kind"] = kind(to_gr)

    if out["baseline_kind"] != "structured" or out["head_kind"] != "structured":
        return out  # no fine-grained comparison possible

    def gap_key(g: dict) -> tuple:
        return (g.get("code"), g.get("claim_id"))

    f_set = {gap_key(g): g for g in (from_gr.get("gaps") or [])}
    t_set = {gap_key(g): g for g in (to_gr.get("gaps") or [])}

    closed_keys = set(f_set) - set(t_set)
    opened_keys = set(t_set) - set(f_set)
    out["closed"] = [f_set[k] for k in sorted(closed_keys, key=lambda x: (x[0] or "", x[1] or ""))]
    out["opened"] = [t_set[k] for k in sorted(opened_keys, key=lambda x: (x[0] or "", x[1] or ""))]

    fs = from_gr.get("summary") or {}
    ts = to_gr.get("summary") or {}
    out["summary_delta"] = {
        "total":    (ts.get("total", 0) - fs.get("total", 0)),
        "critical": (ts.get("critical", 0) - fs.get("critical", 0)),
        "warning":  (ts.get("warning", 0) - fs.get("warning", 0)),
        "info":     (ts.get("info", 0) - fs.get("info", 0)),
    }
    return out


# --- Comparison confidence -----------------------------------------------


def assess_confidence(from_snap: Snapshot, to_snap: Snapshot) -> dict:
    """Return a confidence record for the diff itself.

    Fields:
      level:  high | medium | low
      reasons: list of human-readable strings explaining any downgrade
    """
    reasons: list[str] = []
    level = "high"

    if not from_snap.exists:
        reasons.append(f"baseline snapshot at '{from_snap.ref}' has no usable data")
        level = "low"
    if not to_snap.exists:
        reasons.append(f"head snapshot at '{to_snap.ref}' has no usable data")
        level = "low"

    if from_snap.exists and to_snap.exists:
        if from_snap.provenance_quality != "full":
            reasons.append(
                f"baseline provenance quality is '{from_snap.provenance_quality}' "
                f"— changes attributed to '{from_snap.ref}' may be historical "
                f"artifacts, not genuine eval movement"
            )
            if level == "high":
                level = "medium"
        if to_snap.provenance_quality == "missing":
            reasons.append(
                f"head snapshot at '{to_snap.ref}' has no run-level provenance"
            )
            if level == "high":
                level = "medium"

        if not from_snap.claims:
            reasons.append("baseline has zero claims — diff is effectively one-sided")
            level = "low"

        # Baseline lacks a bucket at all
        if from_snap.verdict_bucket in (None, "unknown"):
            reasons.append(
                f"baseline verdict bucket is '{from_snap.verdict_bucket or 'unknown'}'"
                " — bucket delta is not meaningful"
            )
            if level == "high":
                level = "medium"

    if from_snap.errors:
        reasons.extend(f"baseline: {e}" for e in from_snap.errors)
    if to_snap.errors:
        reasons.extend(f"head: {e}" for e in to_snap.errors)

    return {"level": level, "reasons": reasons}


# --- Summaries -----------------------------------------------------------


def summarize(diff: dict) -> dict:
    """High-level movement counts — 'did it get better?' in numbers."""
    s_changes = diff["claims"]["status_changes"]
    improvements = sum(1 for c in s_changes if c["transition"] == "improvement")
    regressions = sum(1 for c in s_changes if c["transition"] == "regression")
    newly_failing = sum(1 for c in s_changes if c["transition"] == "newly_failing")
    unchanged = sum(1 for c in s_changes if c["transition"] == "unchanged")

    return {
        "claims_added": len(diff["claims"]["added"]),
        "claims_removed": len(diff["claims"]["removed"]),
        "status_improvements": improvements,
        "status_regressions": regressions,
        "status_newly_failing": newly_failing,
        "status_unchanged": unchanged,
        "bucket_change": diff["verdict"]["bucket_change"],
        "runs_added": len(diff["runs"]["added"]),
        "runs_removed": len(diff["runs"]["removed"]),
        "gaps_closed": len(diff["gap_report"]["closed"]),
        "gaps_opened": len(diff["gap_report"]["opened"]),
    }


# --- Main diff ------------------------------------------------------------


def build_diff(
    repo_dir: pathlib.Path,
    from_ref: str,
    to_ref: str,
    root: pathlib.Path | None = None,
) -> dict:
    root = root or ROOT
    loader = SnapshotLoader(root, repo_dir)
    from_snap = loader.load(from_ref)
    to_snap = loader.load(to_ref)
    from_sha = loader.resolve_ref(from_ref)
    to_sha = loader.resolve_ref(to_ref)

    claims_diff = diff_claims(from_snap.claims, to_snap.claims)
    runs_diff = diff_runs(from_snap.runs, to_snap.runs)
    gap_diff = diff_gap_reports(from_snap.gap_report, to_snap.gap_report)

    archetype_from = (from_snap.repo_meta or {}).get("archetype")
    archetype_to = (to_snap.repo_meta or {}).get("archetype")

    verdict_block = {
        "from_bucket": from_snap.verdict_bucket,
        "to_bucket": to_snap.verdict_bucket,
        "bucket_change": classify_bucket_change(
            from_snap.verdict_bucket, to_snap.verdict_bucket
        ),
    }

    diff = {
        "repo": str(repo_dir.name),
        "from_ref": from_ref,
        "from_sha": from_sha,
        "to_ref": to_ref,
        "to_sha": to_sha,
        "baseline": {
            "exists": from_snap.exists,
            "provenance_quality": from_snap.provenance_quality,
            "claim_count": len(from_snap.claims),
            "verdict_bucket": from_snap.verdict_bucket,
            "archetype": archetype_from,
            "errors": from_snap.errors,
        },
        "head": {
            "exists": to_snap.exists,
            "provenance_quality": to_snap.provenance_quality,
            "claim_count": len(to_snap.claims),
            "verdict_bucket": to_snap.verdict_bucket,
            "archetype": archetype_to,
            "errors": to_snap.errors,
        },
        "archetype_change": {
            "from": archetype_from,
            "to": archetype_to,
            "changed": archetype_from != archetype_to,
        },
        "verdict": verdict_block,
        "claims": claims_diff,
        "runs": runs_diff,
        "gap_report": gap_diff,
    }
    diff["summary"] = summarize(diff)
    diff["comparison_confidence"] = assess_confidence(from_snap, to_snap)
    return diff


# --- Markdown renderer ---------------------------------------------------


def render_markdown(diff: dict) -> str:
    s = diff["summary"]
    conf = diff["comparison_confidence"]
    def ref_label(ref: str, sha: str | None) -> str:
        if ref == "working":
            return "`working`"
        if sha and sha != ref:
            return f"`{ref}` (`{sha}`)"
        return f"`{ref}`"

    lines = [
        f"# Re-Eval Diff — {diff['repo']}",
        "",
        f"**from:** {ref_label(diff['from_ref'], diff.get('from_sha'))} "
        f"→ **to:** {ref_label(diff['to_ref'], diff.get('to_sha'))}",
        "",
        f"**Comparison confidence:** {conf['level']}",
    ]
    if conf["reasons"]:
        for r in conf["reasons"]:
            lines.append(f"  - {r}")
    lines += [
        "",
        "## Headline",
        "",
        _headline(diff),
        "",
        "## Verdict",
        "",
        f"- bucket: `{diff['verdict']['from_bucket']}` → `{diff['verdict']['to_bucket']}` ({diff['verdict']['bucket_change']})",
        f"- archetype: `{diff['archetype_change']['from']}` → `{diff['archetype_change']['to']}` ({'changed' if diff['archetype_change']['changed'] else 'unchanged'})",
        "",
        "## Claim movement",
        "",
        f"- improvements: **{s['status_improvements']}**",
        f"- regressions: **{s['status_regressions']}**",
        f"- newly failing (was untested): **{s['status_newly_failing']}**",
        f"- claims added: {s['claims_added']}",
        f"- claims removed: {s['claims_removed']}",
        "",
    ]

    status_changes = diff["claims"]["status_changes"]
    if status_changes:
        lines += ["### Status changes", ""]
        improvements = [c for c in status_changes if c["transition"] == "improvement"]
        regressions = [c for c in status_changes if c["transition"] == "regression"]
        newly = [c for c in status_changes if c["transition"] == "newly_failing"]

        def render_group(title: str, items: list[dict]) -> None:
            if not items:
                return
            lines.append(f"**{title}** ({len(items)})")
            lines.append("")
            for c in items:
                lines.append(
                    f"- `{c['id']}` ({c['priority']}) — {c['from']} → {c['to']} "
                    f"— {c['title']}"
                )
            lines.append("")

        render_group("Improvements", improvements)
        render_group("Regressions", regressions)
        render_group("Newly failing (was untested)", newly)

    if diff["claims"]["added"]:
        lines += ["### Added claims", ""]
        for c in diff["claims"]["added"]:
            lines.append(
                f"- `{c['id']}` ({c['priority']}, status={c['status']}) — {c['title']}"
            )
        lines.append("")

    if diff["claims"]["removed"]:
        lines += ["### Removed claims", ""]
        for c in diff["claims"]["removed"]:
            lines.append(
                f"- `{c['id']}` ({c['priority']}, was status={c['status']}) — {c['title']}"
            )
        lines.append("")

    lines += [
        "## Runs",
        "",
        f"- baseline runs: {diff['runs']['from_count']}",
        f"- head runs: {diff['runs']['to_count']}",
    ]
    if diff["runs"]["added"]:
        lines.append(f"- new runs added:")
        for r in diff["runs"]["added"]:
            lines.append(f"  - `{r}`")
    if diff["runs"]["removed"]:
        lines.append(f"- runs removed:")
        for r in diff["runs"]["removed"]:
            lines.append(f"  - `{r}`")
    lines.append("")

    gd = diff["gap_report"]
    lines += ["## Coverage gaps", ""]
    if gd["baseline_kind"] != "structured" or gd["head_kind"] != "structured":
        lines.append(
            f"- structured gap diff unavailable "
            f"(baseline: {gd['baseline_kind']}, head: {gd['head_kind']})"
        )
        lines.append(
            "  - committed gap reports under `gap-reports/` are still "
            "human-readable, and a live run via `coverage_gap_detector.py` "
            "can produce the structured form."
        )
    else:
        sd = gd["summary_delta"] or {}
        lines.append(f"- total gap delta: **{sd.get('total', 0):+d}**")
        lines.append(f"- critical gap delta: **{sd.get('critical', 0):+d}**")
        lines.append(f"- warning gap delta: **{sd.get('warning', 0):+d}**")
        lines.append(f"- info gap delta: **{sd.get('info', 0):+d}**")
        if gd["closed"]:
            lines.append("")
            lines.append(f"**Closed ({len(gd['closed'])})**")
            lines.append("")
            for g in gd["closed"]:
                lines.append(f"- `{g.get('code')}` `{g.get('claim_id','-')}` — {g.get('message','')}")
        if gd["opened"]:
            lines.append("")
            lines.append(f"**Opened ({len(gd['opened'])})**")
            lines.append("")
            for g in gd["opened"]:
                lines.append(f"- `{g.get('code')}` `{g.get('claim_id','-')}` — {g.get('message','')}")
    lines.append("")
    lines += ["## Snapshot integrity", ""]
    lines.append(f"- baseline provenance: `{diff['baseline']['provenance_quality']}`")
    lines.append(f"- head provenance: `{diff['head']['provenance_quality']}`")
    if diff["baseline"]["errors"]:
        lines.append("- baseline errors:")
        for e in diff["baseline"]["errors"]:
            lines.append(f"  - {e}")
    if diff["head"]["errors"]:
        lines.append("- head errors:")
        for e in diff["head"]["errors"]:
            lines.append(f"  - {e}")
    return "\n".join(lines) + "\n"


def _headline(diff: dict) -> str:
    s = diff["summary"]
    bc = diff["verdict"]["bucket_change"]
    if not diff["baseline"]["exists"]:
        return "_Baseline has no data — this is a first-time evaluation, not a diff._"
    if not diff["head"]["exists"]:
        return "_Head snapshot is empty — check your --to reference._"

    if bc == "improvement":
        verb = "improved"
    elif bc == "regression":
        verb = "regressed"
    elif bc == "unclassifiable":
        verb = "changed in ways that cannot be ranked"
    else:
        verb = "did not change bucket"

    parts = [f"Verdict {verb} (`{diff['verdict']['from_bucket']}` → `{diff['verdict']['to_bucket']}`)."]
    if s["status_improvements"] or s["status_regressions"] or s["status_newly_failing"]:
        parts.append(
            f"Claim movement: +{s['status_improvements']} improved, "
            f"-{s['status_regressions']} regressed, "
            f"?{s['status_newly_failing']} newly failing."
        )
    if s["claims_added"] or s["claims_removed"]:
        parts.append(
            f"Claim set: +{s['claims_added']} added, -{s['claims_removed']} removed."
        )
    if s["runs_added"] or s["runs_removed"]:
        parts.append(f"Runs: +{s['runs_added']} / -{s['runs_removed']}.")
    return " ".join(parts)


# --- CLI -----------------------------------------------------------------


def _write_artifacts(diff: dict, output_dir: pathlib.Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "diff.yaml").write_text(
        yaml.safe_dump(diff, sort_keys=False, allow_unicode=True)
    )
    (output_dir / "diff.json").write_text(
        json.dumps(diff, indent=2, ensure_ascii=False) + "\n"
    )
    (output_dir / "summary.md").write_text(render_markdown(diff))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("repo_dir", type=pathlib.Path)
    parser.add_argument("--from", dest="from_ref", required=True)
    parser.add_argument("--to", dest="to_ref", default="working")
    parser.add_argument("--output", type=pathlib.Path, default=None,
                        help="directory to write diff.yaml + diff.json + summary.md")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--yaml", action="store_true")
    group.add_argument("--json", action="store_true")
    group.add_argument("--md", action="store_true")
    parser.add_argument(
        "--fail-on",
        choices=["regression", "any-change"],
        default=None,
        help="exit non-zero if the diff shows regressions (or any change)",
    )
    args = parser.parse_args(argv)

    if not args.repo_dir.exists():
        print(f"no such repo dir: {args.repo_dir}", file=sys.stderr)
        return 2

    try:
        diff = build_diff(args.repo_dir.resolve(), args.from_ref, args.to_ref)
    except Exception as e:
        print(f"reeval_diff: {e}", file=sys.stderr)
        return 2

    if args.output:
        _write_artifacts(diff, args.output)
        print(f"wrote {args.output}/diff.yaml, diff.json, summary.md")

    # Only write to stdout if the caller explicitly asked for a format
    # OR there is no --output (so the caller needs *something* back).
    want_stdout = args.json or args.md or args.yaml or not args.output
    if want_stdout:
        if args.md:
            sys.stdout.write(render_markdown(diff))
        elif args.json:
            print(json.dumps(diff, indent=2, ensure_ascii=False))
        else:
            sys.stdout.write(yaml.safe_dump(diff, sort_keys=False, allow_unicode=True))

    if args.fail_on:
        s = diff["summary"]
        if args.fail_on == "regression":
            if s["status_regressions"] > 0 or s["gaps_opened"] > 0 \
                    or diff["verdict"]["bucket_change"] == "regression":
                return 1
        elif args.fail_on == "any-change":
            any_change = (
                s["status_improvements"] or s["status_regressions"]
                or s["status_newly_failing"] or s["claims_added"]
                or s["claims_removed"] or s["runs_added"] or s["runs_removed"]
                or diff["verdict"]["bucket_change"] not in ("unchanged",)
            )
            if any_change:
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
