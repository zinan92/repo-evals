#!/usr/bin/env python3
"""
coverage_gap_detector.py — find claims the eval is about to ignore.

An eval plan can look solid while still skipping critical claims.
This tool compares the claim map and the eval plan (and any available
run summaries) and surfaces gaps with severity levels.

Usage:
    scripts/coverage_gap_detector.py <repo-dir>                    # YAML
    scripts/coverage_gap_detector.py <repo-dir> --json
    scripts/coverage_gap_detector.py <repo-dir> --md               # Markdown
    scripts/coverage_gap_detector.py <repo-dir> --fail-on critical # CI-friendly

The tool is deliberately conservative: it flags things a human should
review, not things it refuses to let ship.

Severity levels:
    critical  — would block a strong verdict; must be addressed
    warning   — likely weakens the eval; should be addressed
    info      — worth noting for plan review

Sources used:
    <repo-dir>/claims/claim-map.yaml       — required
    <repo-dir>/plans/*-eval-plan.md        — optional; latest by name
    <repo-dir>/runs/**/run-summary.yaml    — optional; informs "run coverage"
    <repo-dir>/repo.yaml                   — optional; reads `archetype`

The report is file-based — it does not mutate anything.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("coverage_gap_detector.py: PyYAML required", file=sys.stderr)
    sys.exit(2)


# --- Data loading ---------------------------------------------------------


def load_claim_map(repo_dir: pathlib.Path) -> list[dict]:
    cm = repo_dir / "claims" / "claim-map.yaml"
    if not cm.exists():
        raise FileNotFoundError(f"no claim-map.yaml at {cm}")
    data = yaml.safe_load(cm.read_text()) or {}
    claims = data.get("claims") or []
    if not isinstance(claims, list):
        raise ValueError(f"{cm}: 'claims' must be a list")
    return claims


def load_latest_plan(repo_dir: pathlib.Path) -> tuple[pathlib.Path | None, str]:
    plans_dir = repo_dir / "plans"
    if not plans_dir.exists():
        return None, ""
    candidates = sorted(plans_dir.glob("*-eval-plan.md"))
    if not candidates:
        return None, ""
    latest = candidates[-1]
    return latest, latest.read_text()


def load_repo_meta(repo_dir: pathlib.Path) -> dict:
    p = repo_dir / "repo.yaml"
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text()) or {}


def load_run_summaries(repo_dir: pathlib.Path) -> list[dict]:
    out: list[dict] = []
    runs_dir = repo_dir / "runs"
    if not runs_dir.exists():
        return out
    for rs in runs_dir.rglob("run-summary.yaml"):
        try:
            data = yaml.safe_load(rs.read_text()) or {}
            data["_path"] = str(rs.relative_to(repo_dir))
            out.append(data)
        except Exception:
            continue
    return out


# --- Claim / plan analysis ------------------------------------------------


PASS_STATUSES = {"passed", "pass", "passed_with_concerns", "pass-with-concerns"}
FAIL_STATUSES = {"failed", "fail", "failed_partial", "fail-partial"}
UNTESTED_STATUSES = {"untested", "pending", "unknown", ""}

CLAIM_ID_RE = re.compile(r"claim-\d{3,}")


def normalize_status(s: str | None) -> str:
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


def claim_referenced_in_plan(claim: dict, plan_text: str) -> bool:
    """A claim is 'in the plan' if its id OR its title (case-insensitive)
    appears somewhere in the plan body.

    We are deliberately loose here — the detector is a prompt for human
    review, not a strict gate.
    """
    if not plan_text:
        return False
    cid = str(claim.get("id", ""))
    if cid and cid in plan_text:
        return True
    title = str(claim.get("title", "")).strip()
    if title and title.lower() in plan_text.lower():
        return True
    return False


def orphan_plan_refs(plan_text: str, claim_ids: set[str]) -> list[str]:
    """Claim ids mentioned in the plan that are NOT in the claim map."""
    if not plan_text:
        return []
    ids_in_plan = set(CLAIM_ID_RE.findall(plan_text))
    return sorted(ids_in_plan - claim_ids)


def claim_covered_by_runs(
    claim: dict, runs: list[dict]
) -> tuple[bool, list[str]]:
    """Return (covered, list-of-run-paths-where-it-appears)."""
    cid = str(claim.get("id", ""))
    found: list[str] = []
    for r in runs:
        rbc = r.get("results_by_claim") or {}
        if not isinstance(rbc, dict):
            continue
        for key in rbc.keys():
            # runs often use e.g. "claim-001" or "claim-001-install"
            if key == cid or str(key).startswith(cid + "-"):
                found.append(r.get("_path", "?"))
                break
    return bool(found), found


# --- Rule table -----------------------------------------------------------


def detect_gaps(
    claims: list[dict],
    plan_text: str,
    runs: list[dict],
    archetype: str,
) -> list[dict]:
    """Return a list of gap records, each:
        {
          "severity": "critical" | "warning" | "info",
          "code": "MACHINE_READABLE_CODE",
          "claim_id": "claim-XXX" (or None),
          "message": "human-readable explanation",
        }
    """
    gaps: list[dict] = []
    claim_ids = {str(c.get("id", "")) for c in claims if c.get("id")}

    for c in claims:
        cid = str(c.get("id", "?"))
        prio = str(c.get("priority", "medium")).lower()
        status = normalize_status(c.get("status"))
        title = str(c.get("title", "")).strip()

        # R1: blank evidence_needed on any priority is a warning;
        #     on critical it is a critical gap
        if not str(c.get("evidence_needed", "")).strip():
            gaps.append({
                "severity": "critical" if prio == "critical" else "warning",
                "code": "EVIDENCE_NEEDED_BLANK",
                "claim_id": cid,
                "message": (
                    f"{cid} ({prio}) has no evidence_needed; reviewers "
                    "cannot judge whether it was actually validated"
                ),
            })

        # R2: critical claim not referenced by the eval plan (if a plan exists)
        if prio == "critical" and plan_text and not claim_referenced_in_plan(c, plan_text):
            gaps.append({
                "severity": "critical",
                "code": "CRITICAL_CLAIM_MISSING_FROM_PLAN",
                "claim_id": cid,
                "message": (
                    f"{cid} is critical but is not mentioned (by id or "
                    f"title) in the latest eval plan"
                ),
            })

        # R3: critical claim still untested
        # A legitimate skip requires a populated skip_reason. Without it,
        # the claim looks identical to "we forgot" — which is the bug.
        if prio == "critical" and status == "untested":
            skip_reason = str(c.get("skip_reason", "")).strip()
            if skip_reason:
                gaps.append({
                    "severity": "warning",
                    "code": "CRITICAL_CLAIM_SKIPPED",
                    "claim_id": cid,
                    "message": (
                        f"{cid} is critical but intentionally skipped "
                        f"(reason recorded). Verdict ceiling still applies."
                    ),
                })
            else:
                gaps.append({
                    "severity": "critical",
                    "code": "CRITICAL_CLAIM_UNTESTED",
                    "claim_id": cid,
                    "message": (
                        f"{cid} is critical and still untested. "
                        f"If this is a deliberate skip, add a skip_reason "
                        f"field to the claim."
                    ),
                })

        # R4: critical claim failed → surface (still a critical gap)
        if prio == "critical" and status == "failed":
            gaps.append({
                "severity": "critical",
                "code": "CRITICAL_CLAIM_FAILED",
                "claim_id": cid,
                "message": f"{cid} is critical and marked failed — must be resolved before a strong verdict",
            })

        # R5: high claim untested → warning
        if prio == "high" and status == "untested":
            gaps.append({
                "severity": "warning",
                "code": "HIGH_CLAIM_UNTESTED",
                "claim_id": cid,
                "message": f"{cid} is high-priority and still untested",
            })

        # R6: claim has statuses but no run actually listed it in results_by_claim
        covered, _paths = claim_covered_by_runs(c, runs)
        if prio in ("critical", "high") and runs and not covered and status != "untested":
            gaps.append({
                "severity": "warning",
                "code": "CLAIM_STATUS_BUT_NO_RUN_EVIDENCE",
                "claim_id": cid,
                "message": (
                    f"{cid} has status={status} but no run's "
                    f"results_by_claim references it"
                ),
            })

    # R7: orphan claim ids in plan (plan mentions an id that is not in claim map)
    for oid in orphan_plan_refs(plan_text, claim_ids):
        gaps.append({
            "severity": "info",
            "code": "ORPHAN_PLAN_REFERENCE",
            "claim_id": oid,
            "message": (
                f"plan mentions {oid} but it is not defined in claim-map.yaml"
            ),
        })

    # R8: hybrid archetype with no claim in any *core-* area
    if archetype in {"hybrid-skill", "prompt-skill"}:
        has_core_layer_claim = any(
            "core" in str(c.get("area", "")).lower() or "llm" in str(c.get("area", "")).lower()
            for c in claims
        )
        if not has_core_layer_claim:
            gaps.append({
                "severity": "warning",
                "code": "HYBRID_ARCHETYPE_NO_CORE_CLAIMS",
                "claim_id": None,
                "message": (
                    f"archetype={archetype} but no claim has an area containing "
                    f"'core' or 'llm'; the verdict cap will apply but the "
                    f"claim map does not explicitly track the core layer"
                ),
            })

    return gaps


# --- Reporting ------------------------------------------------------------


def summarize(gaps: list[dict]) -> dict:
    return {
        "total": len(gaps),
        "critical": sum(1 for g in gaps if g["severity"] == "critical"),
        "warning": sum(1 for g in gaps if g["severity"] == "warning"),
        "info": sum(1 for g in gaps if g["severity"] == "info"),
    }


def render_markdown(repo_dir: pathlib.Path, report: dict) -> str:
    s = report["summary"]
    lines = [
        f"# Coverage Gap Report — {repo_dir.name}",
        "",
        f"- archetype: `{report['archetype']}`",
        f"- plan: `{report['plan_path'] or '(no plan found)'}`",
        f"- runs scanned: {report['runs_scanned']}",
        f"- claims scanned: {report['claims_scanned']}",
        "",
        f"**Gaps:** {s['total']}  "
        f"(critical: {s['critical']}, warning: {s['warning']}, info: {s['info']})",
        "",
    ]

    def section(title: str, level: str) -> None:
        items = [g for g in report["gaps"] if g["severity"] == level]
        if not items:
            return
        lines.append(f"## {title} ({len(items)})")
        lines.append("")
        for g in items:
            cid = g.get("claim_id") or "-"
            lines.append(f"- **[{g['code']}]** `{cid}` — {g['message']}")
        lines.append("")

    section("Critical", "critical")
    section("Warnings", "warning")
    section("Info", "info")

    if s["total"] == 0:
        lines.append("_No gaps detected. This does not mean the eval is complete — "
                     "it means the current claim map + plan + runs are internally consistent._")
    return "\n".join(lines) + "\n"


# --- CLI ------------------------------------------------------------------


def build_report(repo_dir: pathlib.Path) -> dict:
    meta = load_repo_meta(repo_dir)
    archetype = str(meta.get("archetype") or "unknown")
    claims = load_claim_map(repo_dir)
    plan_path, plan_text = load_latest_plan(repo_dir)
    runs = load_run_summaries(repo_dir)
    gaps = detect_gaps(claims, plan_text, runs, archetype)
    return {
        "repo": repo_dir.name,
        "archetype": archetype,
        "plan_path": str(plan_path.relative_to(repo_dir)) if plan_path else None,
        "runs_scanned": len(runs),
        "claims_scanned": len(claims),
        "summary": summarize(gaps),
        "gaps": gaps,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("repo_dir", type=pathlib.Path)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--md", action="store_true", help="emit Markdown")
    parser.add_argument(
        "--fail-on",
        choices=["critical", "warning", "info"],
        default=None,
        help="exit non-zero if any gap at or above this severity exists",
    )
    args = parser.parse_args(argv)

    if not args.repo_dir.exists():
        print(f"no such repo dir: {args.repo_dir}", file=sys.stderr)
        return 2

    try:
        report = build_report(args.repo_dir)
    except (FileNotFoundError, ValueError) as e:
        print(f"coverage-gap-detector: {e}", file=sys.stderr)
        return 2

    if args.md:
        sys.stdout.write(render_markdown(args.repo_dir, report))
    elif args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        sys.stdout.write(yaml.safe_dump(report, sort_keys=False, allow_unicode=True))

    if args.fail_on:
        order = ["info", "warning", "critical"]
        threshold = order.index(args.fail_on)
        for g in report["gaps"]:
            if order.index(g["severity"]) >= threshold:
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
