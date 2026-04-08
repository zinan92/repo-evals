#!/usr/bin/env python3
"""
generate_dashboard.py — build a static operator dashboard for repo-evals.

Reads repo-evals' file-based source of truth from `repos/` and generates a
committable static dashboard under `dashboard/`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import pathlib
import re
import subprocess
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit("generate_dashboard.py: PyYAML required")


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOS_DIR = ROOT / "repos"
DASHBOARD_DIR = ROOT / "dashboard"

BUCKET_ORDER = ["recommendable", "reusable", "usable", "unusable", "unknown"]
BUCKET_RANK = {bucket: idx for idx, bucket in enumerate(reversed(BUCKET_ORDER))}
GAP_COUNT_RE = re.compile(
    r"\*\*Gaps:\*\*\s*(\d+)\s+\(critical:\s*(\d+),\s*warning:\s*(\d+),\s*info:\s*(\d+)\)",
    re.IGNORECASE,
)
GAP_ITEM_RE = re.compile(
    r"-\s+\*\*\[([A-Z_]+)\]\*\*\s+`([^`]*)`\s+—\s+(.+)$"
)
CONFIDENCE_RE = re.compile(r"\*\*Comparison confidence:\*\*\s+([a-z]+)", re.IGNORECASE)
SHA_REF_RE = re.compile(r"\*\*from:\*\*\s+`([^`]+)`(?:\s+\(`([^`]+)`\))?\s+→\s+\*\*to:\*\*\s+`([^`]+)`")


STYLE_CSS = """
:root {
  --bg: #f4efe6;
  --panel: #fffaf2;
  --panel-strong: #f8f1e4;
  --ink: #102329;
  --muted: #5a6c73;
  --line: #d9cdb7;
  --accent: #0d6b64;
  --accent-soft: #d5efeb;
  --warning: #b36b00;
  --warning-soft: #fff0d6;
  --danger: #a13d30;
  --danger-soft: #fde5df;
  --success: #286c49;
  --success-soft: #dff5e8;
  --shadow: 0 18px 50px rgba(16, 35, 41, 0.08);
}

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(13, 107, 100, 0.10), transparent 28%),
    radial-gradient(circle at top right, rgba(179, 107, 0, 0.08), transparent 22%),
    linear-gradient(180deg, #f7f1e8 0%, var(--bg) 100%);
  min-height: 100vh;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

.shell {
  width: min(1240px, calc(100vw - 40px));
  margin: 0 auto;
  padding: 28px 0 48px;
}

.hero {
  background: linear-gradient(135deg, rgba(13, 107, 100, 0.92), rgba(22, 54, 73, 0.92));
  color: #f9f7f2;
  border-radius: 28px;
  padding: 30px 32px;
  box-shadow: var(--shadow);
  overflow: hidden;
  position: relative;
}

.hero::after {
  content: "";
  position: absolute;
  inset: auto -40px -70px auto;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.10);
}

.hero h1, .hero h2 { margin: 0 0 10px; font-weight: 700; letter-spacing: -0.02em; }
.hero p { margin: 0; max-width: 74ch; line-height: 1.55; color: rgba(249, 247, 242, 0.88); }
.meta-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 18px;
}

.chip, .badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 13px;
  line-height: 1;
  border: 1px solid transparent;
  white-space: nowrap;
}

.chip {
  background: rgba(255, 255, 255, 0.12);
  color: #f8f3ea;
}

.grid {
  display: grid;
  gap: 18px;
  margin-top: 24px;
}

.grid.stats { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
.grid.cards { grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
.grid.detail { grid-template-columns: 1.15fr 0.85fr; align-items: start; }

.panel {
  background: var(--panel);
  border: 1px solid rgba(217, 205, 183, 0.7);
  border-radius: 24px;
  padding: 22px;
  box-shadow: var(--shadow);
}

.stat-card {
  background: var(--panel);
  border: 1px solid rgba(217, 205, 183, 0.7);
  border-radius: 22px;
  padding: 18px;
  box-shadow: var(--shadow);
}

.stat-card h3, .panel h3, .panel h4 {
  margin: 0 0 8px;
  font-size: 16px;
}

.stat-value {
  font-size: 34px;
  line-height: 1;
  letter-spacing: -0.04em;
  margin-bottom: 8px;
}

.muted { color: var(--muted); }
.small { font-size: 13px; }
.mono { font-family: "SFMono-Regular", "Menlo", "Consolas", monospace; }

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
  padding: 16px 18px;
  background: rgba(255, 250, 242, 0.92);
  border: 1px solid rgba(217, 205, 183, 0.7);
  border-radius: 22px;
  box-shadow: var(--shadow);
}

.toolbar input, .toolbar select {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px 12px;
  background: #fffdf8;
  color: var(--ink);
  font-size: 14px;
}

.repo-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.repo-card header {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: start;
}

.repo-card h3 {
  margin: 0;
  font-size: 24px;
  letter-spacing: -0.02em;
}

.repo-card p {
  margin: 0;
  line-height: 1.55;
}

.kv {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
}

.kv div {
  border-top: 1px solid rgba(217, 205, 183, 0.7);
  padding-top: 10px;
}

.kv strong {
  display: block;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin-bottom: 4px;
}

.flag-list, .bullet-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.6;
}

.flag-list li, .bullet-list li { margin-bottom: 6px; }

.badge.bucket-recommendable { background: var(--success-soft); color: var(--success); border-color: rgba(40, 108, 73, 0.18); }
.badge.bucket-reusable { background: var(--accent-soft); color: var(--accent); border-color: rgba(13, 107, 100, 0.18); }
.badge.bucket-usable { background: var(--warning-soft); color: var(--warning); border-color: rgba(179, 107, 0, 0.18); }
.badge.bucket-unusable, .badge.bucket-unknown { background: var(--danger-soft); color: var(--danger); border-color: rgba(161, 61, 48, 0.18); }

.badge.conf-high, .badge.prov-full { background: var(--success-soft); color: var(--success); border-color: rgba(40, 108, 73, 0.18); }
.badge.conf-medium, .badge.prov-partial { background: var(--warning-soft); color: var(--warning); border-color: rgba(179, 107, 0, 0.18); }
.badge.conf-low, .badge.conf-unknown, .badge.prov-missing { background: var(--danger-soft); color: var(--danger); border-color: rgba(161, 61, 48, 0.18); }

.attention-high { border-color: rgba(161, 61, 48, 0.24); }
.attention-medium { border-color: rgba(179, 107, 0, 0.24); }

.headline {
  padding: 12px 14px;
  border-radius: 16px;
  background: var(--panel-strong);
  border: 1px solid rgba(217, 205, 183, 0.7);
}

.section-title {
  margin-top: 36px;
  margin-bottom: 12px;
}

.source-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.source-links a {
  padding: 8px 12px;
  border-radius: 12px;
  background: #fffdf8;
  border: 1px solid rgba(217, 205, 183, 0.8);
}

.empty-state {
  padding: 18px;
  border-radius: 18px;
  background: rgba(248, 241, 228, 0.9);
  border: 1px dashed var(--line);
  color: var(--muted);
}

footer {
  margin-top: 36px;
  color: var(--muted);
  font-size: 13px;
}

@media (max-width: 980px) {
  .grid.detail { grid-template-columns: 1fr; }
}

@media (max-width: 720px) {
  .shell { width: min(100vw - 24px, 1240px); }
  .hero { padding: 24px 22px; border-radius: 24px; }
  .toolbar { padding: 14px; }
  .kv { grid-template-columns: 1fr; }
}
""".strip() + "\n"


APP_JS = """
const searchInput = document.querySelector('[data-role="search"]');
const bucketSelect = document.querySelector('[data-role="bucket-filter"]');
const confidenceSelect = document.querySelector('[data-role="confidence-filter"]');
const cards = Array.from(document.querySelectorAll('[data-role="repo-card"]'));

function applyFilters() {
  const q = (searchInput?.value || '').trim().toLowerCase();
  const bucket = bucketSelect?.value || '';
  const confidence = confidenceSelect?.value || '';

  for (const card of cards) {
    const hay = (card.dataset.search || '').toLowerCase();
    const matchesSearch = !q || hay.includes(q);
    const matchesBucket = !bucket || card.dataset.bucket === bucket;
    const matchesConfidence = !confidence || card.dataset.confidence === confidence;
    card.style.display = (matchesSearch && matchesBucket && matchesConfidence) ? '' : 'none';
  }
}

for (const el of [searchInput, bucketSelect, confidenceSelect]) {
  if (el) el.addEventListener('input', applyFilters);
}
""".strip() + "\n"


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def latest_file(directory: pathlib.Path, pattern: str) -> pathlib.Path | None:
    files = sorted(directory.glob(pattern)) if directory.exists() else []
    return files[-1] if files else None


def latest_dir(directory: pathlib.Path) -> pathlib.Path | None:
    dirs = sorted(p for p in directory.iterdir() if p.is_dir()) if directory.exists() else []
    return dirs[-1] if dirs else None


def summarize_claims(claims: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total": len(claims),
        "passed": 0,
        "failed": 0,
        "untested": 0,
        "critical_total": 0,
        "critical_passed": 0,
        "critical_failed": 0,
        "critical_untested": 0,
        "high_total": 0,
    }
    for claim in claims:
        status = str(claim.get("status", "untested")).lower().replace(" ", "_")
        priority = str(claim.get("priority", "medium")).lower()
        if status in {"passed", "pass", "passed_with_concerns", "pass-with-concerns"}:
            normalized = "passed"
        elif status in {"failed", "fail", "failed_partial", "fail-partial"}:
            normalized = "failed"
        else:
            normalized = "untested"
        summary[normalized] += 1
        if priority == "critical":
            summary["critical_total"] += 1
            summary[f"critical_{normalized}"] += 1
        if priority == "high":
            summary["high_total"] += 1
    return summary


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"full": 0, "partial": 0, "missing": 0}
    for run in runs:
        prov = run.get("provenance") or {}
        if prov.get("captured") and not prov.get("partial"):
            counts["full"] += 1
        elif prov.get("captured") or prov.get("partial"):
            counts["partial"] += 1
        else:
            counts["missing"] += 1

    if runs and counts["full"] == len(runs):
        quality = "full"
    elif counts["full"] or counts["partial"]:
        quality = "partial"
    else:
        quality = "missing"

    return {"count": len(runs), "provenance_quality": quality, "counts": counts}


def parse_gap_report(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "counts": {"total": 0, "critical": 0, "warning": 0, "info": 0},
        "critical_items": [],
        "warning_items": [],
        "info_items": [],
    }
    match = GAP_COUNT_RE.search(text)
    if match:
        out["counts"] = {
            "total": int(match.group(1)),
            "critical": int(match.group(2)),
            "warning": int(match.group(3)),
            "info": int(match.group(4)),
        }

    section = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## Critical"):
            section = "critical_items"
            continue
        if stripped.startswith("## Warnings"):
            section = "warning_items"
            continue
        if stripped.startswith("## Info"):
            section = "info_items"
            continue
        item = GAP_ITEM_RE.match(stripped)
        if item and section:
            out[section].append(
                {
                    "code": item.group(1),
                    "claim_id": item.group(2),
                    "message": item.group(3),
                }
            )
    return out


def extract_headline_from_summary(text: str) -> str | None:
    if "## Headline" not in text:
        return None
    section = text.split("## Headline", 1)[1].split("\n## ", 1)[0]
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    return " ".join(lines) if lines else None


def parse_diff_summary_markdown(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {"headline": extract_headline_from_summary(text), "comparison_confidence": None, "from_ref": None, "from_sha": None, "to_ref": None}
    confidence = CONFIDENCE_RE.search(text)
    if confidence:
        out["comparison_confidence"] = confidence.group(1).lower()
    refs = SHA_REF_RE.search(text)
    if refs:
        out["from_ref"] = refs.group(1)
        out["from_sha"] = refs.group(2)
        out["to_ref"] = refs.group(3)
    return out


def git_head_short(root: pathlib.Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, FileNotFoundError):  # pragma: no cover
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def collect_area_metadata(repo_dir: pathlib.Path) -> list[dict[str, Any]]:
    areas_dir = repo_dir / "areas"
    if not areas_dir.exists():
        return []
    areas = []
    for area in sorted(p for p in areas_dir.iterdir() if p.is_dir()):
        area_yaml = area / "area.yaml"
        claim_map = area / "claims" / "claim-map.yaml"
        areas.append(
            {
                "slug": area.name,
                "area_path": area_yaml.relative_to(ROOT).as_posix() if area_yaml.exists() else None,
                "claim_map_path": claim_map.relative_to(ROOT).as_posix() if claim_map.exists() else None,
            }
        )
    return areas


def load_latest_gap(repo_dir: pathlib.Path) -> dict[str, Any] | None:
    gap_file = latest_file(repo_dir / "gap-reports", "*.md")
    if not gap_file:
        return None
    parsed = parse_gap_report(gap_file.read_text())
    parsed["path"] = gap_file.relative_to(ROOT).as_posix()
    return parsed


def load_latest_diff(repo_dir: pathlib.Path) -> dict[str, Any] | None:
    diff_dir = latest_dir(repo_dir / "diffs")
    if not diff_dir:
        return None
    diff_yaml = diff_dir / "diff.yaml"
    summary_md = diff_dir / "summary.md"
    diff = load_yaml(diff_yaml) if diff_yaml.exists() else {}
    summary_meta = parse_diff_summary_markdown(summary_md.read_text()) if summary_md.exists() else {}
    confidence = (diff.get("comparison_confidence") or {}).get("level") or summary_meta.get("comparison_confidence") or "unknown"
    return {
        "path": diff_dir.relative_to(ROOT).as_posix(),
        "headline": summary_meta.get("headline"),
        "comparison_confidence": {
            "level": confidence,
            "reasons": (diff.get("comparison_confidence") or {}).get("reasons", []),
        },
        "summary": diff.get("summary", {}),
        "verdict": diff.get("verdict", {}),
        "archetype_change": diff.get("archetype_change", {}),
        "from_ref": diff.get("from_ref") or summary_meta.get("from_ref"),
        "from_sha": diff.get("from_sha") or summary_meta.get("from_sha"),
        "to_ref": diff.get("to_ref") or summary_meta.get("to_ref"),
    }


def repo_attention_level(repo: dict[str, Any]) -> str:
    gap = (repo.get("latest_gap_report") or {}).get("counts", {})
    confidence = ((repo.get("latest_diff") or {}).get("comparison_confidence") or {}).get("level", "unknown")
    provenance = (repo.get("runs_summary") or {}).get("provenance_quality", "missing")
    bucket = repo.get("current_bucket", "unknown")
    if bucket in {"unknown", "unusable"} or gap.get("critical", 0) > 0 or confidence == "low":
        return "high"
    if gap.get("warning", 0) > 0 or confidence == "medium" or provenance != "full":
        return "medium"
    return "low"


def notes_excerpt(text: str, limit: int = 280) -> str:
    compact = " ".join((text or "").split())
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"


def collect_repo_record(repo_dir: pathlib.Path) -> dict[str, Any]:
    repo_meta = load_yaml(repo_dir / "repo.yaml")
    claim_map = load_yaml(repo_dir / "claims" / "claim-map.yaml")
    claims = claim_map.get("claims", [])
    runs = [load_yaml(path) for path in sorted(repo_dir.rglob("run-summary.yaml"))]
    record = {
        "slug": repo_dir.name,
        "display_name": repo_meta.get("display_name", repo_meta.get("repo", repo_dir.name)),
        "owner": repo_meta.get("owner"),
        "repo": repo_meta.get("repo"),
        "repo_url": repo_meta.get("repo_url"),
        "repo_type": repo_meta.get("repo_type", "skill"),
        "archetype": repo_meta.get("archetype", "unknown"),
        "status": repo_meta.get("status", "unknown"),
        "current_bucket": repo_meta.get("current_bucket", "unknown"),
        "uses_areas": bool(repo_meta.get("uses_areas")),
        "notes_excerpt": notes_excerpt(repo_meta.get("notes", "")),
        "repo_path": repo_dir.relative_to(ROOT).as_posix(),
        "claims_summary": summarize_claims(claims),
        "runs_summary": summarize_runs(runs),
        "latest_gap_report": load_latest_gap(repo_dir),
        "latest_diff": load_latest_diff(repo_dir),
        "areas": collect_area_metadata(repo_dir),
    }

    plan_file = latest_file(repo_dir / "plans", "*.md")
    verdict_file = latest_file(repo_dir / "verdicts", "*-final-verdict.md")
    record["plan_path"] = plan_file.relative_to(ROOT).as_posix() if plan_file else None
    record["verdict_path"] = verdict_file.relative_to(ROOT).as_posix() if verdict_file else None
    record["attention_level"] = repo_attention_level(record)
    return record


def sort_repos(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        repos,
        key=lambda repo: (
            {"high": 0, "medium": 1, "low": 2}.get(repo["attention_level"], 3),
            -((repo.get("latest_gap_report") or {}).get("counts", {}).get("critical", 0)),
            -BUCKET_RANK.get(repo.get("current_bucket", "unknown"), -1),
            repo["slug"],
        ),
    )


def collect_dashboard_data(root: pathlib.Path = ROOT) -> dict[str, Any]:
    repos_dir = root / "repos"
    repo_records = []
    for repo_dir in sorted(repos_dir.iterdir()):
        if not repo_dir.is_dir():
            continue
        if not (repo_dir / "repo.yaml").exists():
            continue
        repo_records.append(collect_repo_record(repo_dir))
    repos = sort_repos(repo_records)
    stats = {
        "repo_count": len(repos),
        "evaluated_count": sum(1 for repo in repos if repo.get("status") == "evaluated"),
        "planned_count": sum(1 for repo in repos if repo.get("status") == "planned"),
        "critical_gap_total": sum((repo.get("latest_gap_report") or {}).get("counts", {}).get("critical", 0) for repo in repos),
        "warning_gap_total": sum((repo.get("latest_gap_report") or {}).get("counts", {}).get("warning", 0) for repo in repos),
        "full_provenance_repos": sum(1 for repo in repos if (repo.get("runs_summary") or {}).get("provenance_quality") == "full"),
        "medium_or_low_confidence_diffs": sum(
            1
            for repo in repos
            if ((repo.get("latest_diff") or {}).get("comparison_confidence") or {}).get("level") in {"medium", "low"}
        ),
        "bucket_counts": {bucket: sum(1 for repo in repos if repo.get("current_bucket") == bucket) for bucket in BUCKET_ORDER},
    }
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_from_commit": git_head_short(root),
        "repos": repos,
        "stats": stats,
    }


def badge(label: str, css_class: str) -> str:
    return f'<span class="badge {css_class}">{html.escape(label)}</span>'


def bucket_badge(bucket: str) -> str:
    return badge(f"bucket: {bucket}", f"bucket-{bucket}")


def confidence_badge(level: str) -> str:
    return badge(f"diff confidence: {level}", f"conf-{level}")


def provenance_badge(level: str) -> str:
    return badge(f"provenance: {level}", f"prov-{level}")


def rel_source(detail: bool, path: str | None) -> str | None:
    if not path:
        return None
    prefix = "../../" if detail else "../"
    return prefix + path


def render_gap_items(items: list[dict[str, Any]], empty_label: str) -> str:
    if not items:
        return f'<div class="empty-state">{html.escape(empty_label)}</div>'
    lis = "\n".join(
        f"<li><span class=\"mono\">{html.escape(item.get('code', ''))}</span> <strong>{html.escape(item.get('claim_id', '-'))}</strong> — {html.escape(item.get('message', ''))}</li>"
        for item in items
    )
    return f"<ul class=\"flag-list\">{lis}</ul>"


def render_source_links(repo: dict[str, Any]) -> str:
    links = [
        ("repo.yaml", rel_source(True, f"{repo['repo_path']}/repo.yaml")),
        ("claim-map", rel_source(True, f"{repo['repo_path']}/claims/claim-map.yaml")),
        ("latest plan", rel_source(True, repo.get("plan_path"))),
        ("latest verdict", rel_source(True, repo.get("verdict_path"))),
    ]
    if repo.get("latest_gap_report"):
        links.append(("latest gap report", rel_source(True, repo["latest_gap_report"]["path"])))
    if repo.get("latest_diff"):
        links.append(("latest diff folder", rel_source(True, repo["latest_diff"]["path"])))
    tags = "\n".join(
        f'<a href="{html.escape(href)}">{html.escape(label)}</a>'
        for label, href in links
        if href
    )
    return f'<div class="source-links">{tags}</div>'


def render_repo_card(repo: dict[str, Any]) -> str:
    gap = repo.get("latest_gap_report") or {"counts": {"critical": 0, "warning": 0, "info": 0}}
    diff = repo.get("latest_diff") or {}
    claims = repo["claims_summary"]
    confidence = ((diff.get("comparison_confidence") or {}).get("level")) or "unknown"
    search_blob = " ".join(
        filter(
            None,
            [
                repo["slug"],
                repo.get("display_name"),
                repo.get("repo"),
                repo.get("owner"),
                repo.get("archetype"),
                repo.get("current_bucket"),
                repo.get("status"),
            ],
        )
    )
    headline = diff.get("headline") or "No committed re-eval diff yet."
    gap_bits = []
    if gap["counts"]["critical"]:
        gap_bits.append(f"{gap['counts']['critical']} critical gaps")
    if gap["counts"]["warning"]:
        gap_bits.append(f"{gap['counts']['warning']} warnings")
    if not gap_bits:
        gap_bits.append("No gap report yet")
    areas_count = len(repo.get("areas", [])) if repo.get("uses_areas") else 0
    return f"""
    <article class="panel repo-card attention-{repo['attention_level']}" data-role="repo-card"
      data-search="{html.escape(search_blob)}"
      data-bucket="{html.escape(repo.get('current_bucket', 'unknown'))}"
      data-confidence="{html.escape(confidence)}">
      <header>
        <div>
          <h3><a href="repos/{html.escape(repo['slug'])}.html">{html.escape(repo['display_name'])}</a></h3>
          <p class="muted small">{html.escape(repo['owner'])}/{html.escape(repo['repo'])} · {html.escape(repo['repo_type'])} · {html.escape(repo['archetype'])}</p>
        </div>
        <div>{bucket_badge(repo.get("current_bucket", "unknown"))}</div>
      </header>
      <div class="meta-row">
        {provenance_badge((repo.get("runs_summary") or {}).get("provenance_quality", "missing"))}
        {confidence_badge(confidence)}
        <span class="badge bucket-usable">status: {html.escape(repo.get("status", "unknown"))}</span>
      </div>
      <p>{html.escape(repo.get('notes_excerpt', ''))}</p>
      <div class="headline">{html.escape(headline)}</div>
      <div class="kv">
        <div><strong>Claims</strong>{claims['passed']} passed / {claims['failed']} failed / {claims['untested']} untested</div>
        <div><strong>Runs</strong>{repo['runs_summary']['count']} total</div>
        <div><strong>Unresolved Gaps</strong>{html.escape(', '.join(gap_bits))}</div>
        <div><strong>Areas</strong>{areas_count}</div>
      </div>
      <div class="source-links">
        <a href="repos/{html.escape(repo['slug'])}.html">Open detail</a>
        <a href="{html.escape(rel_source(False, f"{repo['repo_path']}/repo.yaml") or '')}">repo.yaml</a>
      </div>
    </article>
    """.strip()


def render_index_html(site: dict[str, Any]) -> str:
    stats = site["stats"]
    repo_cards = "\n".join(render_repo_card(repo) for repo in site["repos"])
    top_attention = [repo for repo in site["repos"] if repo["attention_level"] == "high"][:3]
    top_attention_html = "\n".join(
        f"""
        <div class="panel">
          <h3><a href="repos/{html.escape(repo['slug'])}.html">{html.escape(repo['display_name'])}</a></h3>
          <p class="muted small">{html.escape(repo['owner'])}/{html.escape(repo['repo'])} · {html.escape(repo['archetype'])}</p>
          <div class="meta-row">
            {bucket_badge(repo.get("current_bucket", "unknown"))}
            {provenance_badge(repo['runs_summary']['provenance_quality'])}
          </div>
          <p>{html.escape((repo.get('latest_diff') or {}).get('headline') or repo.get('notes_excerpt') or 'No summary yet.')}</p>
        </div>
        """.strip()
        for repo in top_attention
    ) or '<div class="empty-state">No urgent repos right now.</div>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>repo-evals dashboard</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>repo-evals operator dashboard</h1>
      <p>One place to see what is usable, what is still shaky, and what changed recently — without hiding low-confidence baselines or missing provenance.</p>
      <div class="meta-row">
        <span class="chip">generated at {html.escape(site['generated_at'])}</span>
        <span class="chip">source commit {html.escape(site.get('generated_from_commit') or 'unknown')}</span>
        <a class="chip" href="data/index.json">raw dashboard data</a>
      </div>
    </section>

    <section class="grid stats">
      <div class="stat-card"><h3>Evaluated repos</h3><div class="stat-value">{stats['evaluated_count']}</div><div class="muted small">out of {stats['repo_count']} total repos</div></div>
      <div class="stat-card"><h3>Critical unresolved gaps</h3><div class="stat-value">{stats['critical_gap_total']}</div><div class="muted small">from latest committed gap reports</div></div>
      <div class="stat-card"><h3>Full provenance repos</h3><div class="stat-value">{stats['full_provenance_repos']}</div><div class="muted small">repos whose current runs are fully captured</div></div>
      <div class="stat-card"><h3>Medium/low diff confidence</h3><div class="stat-value">{stats['medium_or_low_confidence_diffs']}</div><div class="muted small">latest committed diffs needing careful reading</div></div>
    </section>

    <h2 class="section-title">Bucket distribution</h2>
    <section class="grid stats">
      <div class="stat-card"><h3>Recommendable</h3><div class="stat-value">{stats['bucket_counts']['recommendable']}</div></div>
      <div class="stat-card"><h3>Reusable</h3><div class="stat-value">{stats['bucket_counts']['reusable']}</div></div>
      <div class="stat-card"><h3>Usable</h3><div class="stat-value">{stats['bucket_counts']['usable']}</div></div>
      <div class="stat-card"><h3>Unusable / Unknown</h3><div class="stat-value">{stats['bucket_counts']['unusable'] + stats['bucket_counts']['unknown']}</div></div>
    </section>

    <h2 class="section-title">Needs attention first</h2>
    <section class="grid cards">{top_attention_html}</section>

    <div class="toolbar">
      <input type="search" data-role="search" placeholder="Search repo, archetype, owner...">
      <select data-role="bucket-filter">
        <option value="">All buckets</option>
        <option value="recommendable">recommendable</option>
        <option value="reusable">reusable</option>
        <option value="usable">usable</option>
        <option value="unusable">unusable</option>
        <option value="unknown">unknown</option>
      </select>
      <select data-role="confidence-filter">
        <option value="">All diff confidence</option>
        <option value="high">high</option>
        <option value="medium">medium</option>
        <option value="low">low</option>
        <option value="unknown">unknown</option>
      </select>
      <span class="muted small">Dashboard is intentionally conservative: missing provenance stays visible.</span>
    </div>

    <h2 class="section-title">All repos</h2>
    <section class="grid cards">{repo_cards}</section>

    <footer>
      Generated from repo-evals' committed files. Low-confidence diffs, missing provenance, and markdown-only baseline gap reports are shown as-is rather than normalized away.
    </footer>
  </main>
  <script src="assets/app.js"></script>
</body>
</html>
"""


def render_repo_html(repo: dict[str, Any]) -> str:
    gap = repo.get("latest_gap_report") or {"counts": {"total": 0, "critical": 0, "warning": 0, "info": 0}}
    diff = repo.get("latest_diff") or {"comparison_confidence": {"level": "unknown", "reasons": []}, "summary": {}}
    claims = repo["claims_summary"]
    runs = repo["runs_summary"]
    areas_html = (
        "<ul class=\"bullet-list\">"
        + "".join(
            f"<li><span class=\"mono\">{html.escape(area['slug'])}</span>"
            + (f' — <a href="{html.escape(rel_source(True, area["claim_map_path"]))}">claim-map</a>' if area.get("claim_map_path") else "")
            + "</li>"
            for area in repo.get("areas", [])
        )
        + "</ul>"
    ) if repo.get("areas") else '<div class="empty-state">No area-level scaffolds for this repo.</div>'
    confidence_reasons = "\n".join(
        f"<li>{html.escape(reason)}</li>" for reason in (diff.get("comparison_confidence") or {}).get("reasons", [])
    ) or "<li>No diff confidence downgrade reasons recorded.</li>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(repo['display_name'])} · repo-evals dashboard</title>
  <link rel="stylesheet" href="../assets/style.css">
</head>
<body>
  <main class="shell">
    <section class="hero">
      <p class="small"><a href="../index.html" style="color: #fff9f2;">← Back to dashboard</a></p>
      <h1>{html.escape(repo['display_name'])}</h1>
      <p>{html.escape(repo.get('notes_excerpt', ''))}</p>
      <div class="meta-row">
        {bucket_badge(repo.get("current_bucket", "unknown"))}
        {provenance_badge(runs['provenance_quality'])}
        {confidence_badge((diff.get("comparison_confidence") or {}).get("level", "unknown"))}
        <span class="chip">{html.escape(repo['owner'])}/{html.escape(repo['repo'])}</span>
        <span class="chip">{html.escape(repo['archetype'])}</span>
      </div>
    </section>

    <section class="grid detail">
      <div class="panel">
        <h3>Current health</h3>
        <div class="kv">
          <div><strong>Bucket</strong>{html.escape(repo.get('current_bucket', 'unknown'))}</div>
          <div><strong>Status</strong>{html.escape(repo.get('status', 'unknown'))}</div>
          <div><strong>Claim coverage</strong>{claims['passed']} passed / {claims['failed']} failed / {claims['untested']} untested</div>
          <div><strong>Runs</strong>{runs['count']} total ({runs['counts']['full']} full, {runs['counts']['partial']} partial, {runs['counts']['missing']} missing)</div>
          <div><strong>Gap counts</strong>{gap['counts']['critical']} critical / {gap['counts']['warning']} warning / {gap['counts']['info']} info</div>
          <div><strong>Areas</strong>{len(repo.get('areas', []))}</div>
        </div>
        <h4 style="margin-top: 22px;">Latest diff headline</h4>
        <div class="headline">{html.escape(diff.get('headline') or 'No committed re-eval diff yet.')}</div>
        <p class="muted small" style="margin-top: 12px;">From {html.escape(diff.get('from_ref') or 'n/a')} {html.escape(diff.get('from_sha') or '')} to {html.escape(diff.get('to_ref') or 'n/a')}.</p>
        {render_source_links(repo)}
      </div>

      <div class="panel">
        <h3>Trust signals</h3>
        <ul class="flag-list">
          <li>Run-level provenance quality: <strong>{html.escape(runs['provenance_quality'])}</strong></li>
          <li>Latest diff confidence: <strong>{html.escape((diff.get('comparison_confidence') or {}).get('level', 'unknown'))}</strong></li>
          <li>Critical unresolved gaps: <strong>{gap['counts']['critical']}</strong></li>
        </ul>
        <h4 style="margin-top: 18px;">Why confidence is limited</h4>
        <ul class="flag-list">{confidence_reasons}</ul>
      </div>
    </section>

    <h2 class="section-title">Unresolved critical gaps</h2>
    <section class="panel">
      {render_gap_items(gap.get('critical_items', []), 'No critical gap items recorded in the latest committed gap report.')}
    </section>

    <h2 class="section-title">Warnings</h2>
    <section class="panel">
      {render_gap_items(gap.get('warning_items', []), 'No warning items recorded in the latest committed gap report.')}
    </section>

    <h2 class="section-title">Claim coverage snapshot</h2>
    <section class="grid stats">
      <div class="stat-card"><h3>Total claims</h3><div class="stat-value">{claims['total']}</div><div class="muted small">root claim-map only</div></div>
      <div class="stat-card"><h3>Critical claims</h3><div class="stat-value">{claims['critical_total']}</div><div class="muted small">{claims['critical_passed']} passed / {claims['critical_failed']} failed / {claims['critical_untested']} untested</div></div>
      <div class="stat-card"><h3>Passed</h3><div class="stat-value">{claims['passed']}</div></div>
      <div class="stat-card"><h3>Untested</h3><div class="stat-value">{claims['untested']}</div></div>
    </section>

    <h2 class="section-title">Diff movement</h2>
    <section class="grid stats">
      <div class="stat-card"><h3>Improved</h3><div class="stat-value">{(diff.get('summary') or {}).get('status_improvements', 0)}</div></div>
      <div class="stat-card"><h3>Regressed</h3><div class="stat-value">{(diff.get('summary') or {}).get('status_regressions', 0)}</div></div>
      <div class="stat-card"><h3>Newly failing</h3><div class="stat-value">{(diff.get('summary') or {}).get('status_newly_failing', 0)}</div></div>
      <div class="stat-card"><h3>Gap delta</h3><div class="stat-value">{(diff.get('summary') or {}).get('gaps_closed', 0)} closed / {(diff.get('summary') or {}).get('gaps_opened', 0)} opened</div></div>
    </section>

    <h2 class="section-title">Area drill-down</h2>
    <section class="panel">
      {areas_html}
    </section>

    <footer>
      Generated from current repo-evals files. Raw JSON: <a href="../data/repos/{html.escape(repo['slug'])}.json">repo data</a>
    </footer>
  </main>
</body>
</html>
"""


def write_dashboard(site: dict[str, Any], output_dir: pathlib.Path) -> None:
    assets_dir = output_dir / "assets"
    repos_dir = output_dir / "repos"
    data_repos_dir = output_dir / "data" / "repos"
    assets_dir.mkdir(parents=True, exist_ok=True)
    repos_dir.mkdir(parents=True, exist_ok=True)
    data_repos_dir.mkdir(parents=True, exist_ok=True)

    (assets_dir / "style.css").write_text(STYLE_CSS)
    (assets_dir / "app.js").write_text(APP_JS)
    (output_dir / "index.html").write_text(render_index_html(site))
    (output_dir / "data" / "index.json").write_text(json.dumps(site, indent=2, ensure_ascii=False) + "\n")

    for repo in site["repos"]:
        (repos_dir / f"{repo['slug']}.html").write_text(render_repo_html(repo))
        (data_repos_dir / f"{repo['slug']}.json").write_text(json.dumps(repo, indent=2, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--output", type=pathlib.Path, default=DASHBOARD_DIR)
    parser.add_argument("--json", action="store_true", help="print aggregated site data JSON to stdout")
    args = parser.parse_args(argv)

    site = collect_dashboard_data(ROOT)
    write_dashboard(site, args.output)
    if args.json:
        print(json.dumps(site, indent=2, ensure_ascii=False))
    print(f"wrote dashboard to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
