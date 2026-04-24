#!/usr/bin/env python3
"""render_verdict_html.py — render a repo's verdict as a single-file HTML page.

The output is a self-contained HTML document (no build step, only CDN deps
for Chart.js and Mermaid). It replaces "open the YAML and the MD side-by-side
in my editor" with "open one file in a browser".

Inputs
------

- ``repos/<slug>/repo.yaml``                     — display name + archetype
- ``repos/<slug>/claims/claim-map.yaml``         — claim table
- ``repos/<slug>/verdicts/<date>-final-verdict.md``        — narrative
- ``repos/<slug>/verdicts/<date>-verdict-input.yaml`` (optional)
- ``repos/<slug>/runs/<date>/*/run-summary.yaml``          — metrics per run

Output
------

- ``repos/<slug>/verdicts/<date>-verdict.html`` (absolute path printed on exit)

Usage
-----

    scripts/render_verdict_html.py <owner>--<repo>
    scripts/render_verdict_html.py <owner>--<repo> --date 2026-04-24
    scripts/render_verdict_html.py <owner>--<repo> --open    # open in browser

Design notes
------------

The layout is adapted from nicobailon/visual-explainer (IBM Plex typography,
warm/dark theme pair, accent-bordered cards). Everything above the fold is
the bucket + confidence; details progressively disclose below.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML required — pip install pyyaml", file=sys.stderr)
    sys.exit(2)


REPO_EVALS_ROOT = Path(__file__).resolve().parent.parent

BUCKET_EMOJI = {
    "unusable": "🔴",
    "usable": "⚪",
    "reusable": "🟡",
    "recommendable": "🟢",
}

BUCKET_COLOR = {
    "unusable": "#b91c1c",
    "usable": "#78716c",
    "reusable": "#ca8a04",
    "recommendable": "#15803d",
}

STATUS_EMOJI = {
    "passed": "✅",
    "failed": "❌",
    "partial": "🟡",
    "passed_with_concerns": "🟡",
    "untested": "⏭️",
    "unknown": "·",
}


# ---- i18n ---------------------------------------------------------------
#
# Every UI chrome string lives here. Rendered HTML uses ``<span class="i18n"
# data-en="..." data-zh="...">`` and CSS picks the right one based on
# ``<html lang="...">``. This keeps both languages in one file with no
# duplicated markup.
#
# The authored content inside the eval (claim titles, verdict markdown,
# archetype name, bucket names) stays untranslated — those are canonical
# strings written by the evaluator in whatever language they chose.

I18N: dict[str, dict[str, str]] = {
    "crumb":             {"en": "repo-evals · verdict",       "zh": "repo-evals · 评测结论"},
    "confidence":        {"en": "confidence",                 "zh": "置信度"},
    "archetype":         {"en": "archetype",                  "zh": "archetype"},
    "claims":            {"en": "claims",                     "zh": "claim 数"},
    "critical_covered":  {"en": "critical covered",           "zh": "critical 覆盖"},
    "runs":              {"en": "runs",                       "zh": "runs"},
    "ceilings_section":  {"en": "Ceilings & blocking issues", "zh": "Ceiling 与 Blocking"},
    "ceiling_reasons":   {"en": "Ceiling reasons",            "zh": "Ceiling 理由"},
    "blocking_issues":   {"en": "Blocking issues",            "zh": "Blocking 问题"},
    "none":              {"en": "none",                       "zh": "无"},
    "derivation":        {"en": "Derivation",                 "zh": "推导路径"},
    "claims_section":    {"en": "Claims",                     "zh": "Claim 清单"},
    "col_id":            {"en": "ID",                         "zh": "ID"},
    "col_title":         {"en": "Title",                      "zh": "标题"},
    "col_priority":      {"en": "Priority",                   "zh": "优先级"},
    "col_area":          {"en": "Area",                       "zh": "领域"},
    "col_status":        {"en": "Status",                     "zh": "状态"},
    "col_skip":          {"en": "Skip reason",                "zh": "跳过原因"},
    "runs_section":      {"en": "Runs & metrics",             "zh": "Runs 与指标"},
    "verdict_section":   {"en": "Full verdict (markdown)",    "zh": "完整 verdict（markdown）"},
    "footer":            {"en": "Rendered by repo-evals render_verdict_html.py · source",
                          "zh": "由 repo-evals render_verdict_html.py 生成 · 源"},
    "with_repo":         {"en": "with repo",                  "zh": "有该 repo"},
    "baseline":          {"en": "baseline (no repo)",         "zh": "baseline（无该 repo）"},
    "no_metrics":        {"en": "no metrics recorded",        "zh": "无指标记录"},
    "baseline_label":    {"en": "baseline (without repo):",   "zh": "baseline（无该 repo）："},
    "run_on":            {"en": "run on",                     "zh": "执行于"},
    "metric_pass":       {"en": "pass",                       "zh": "通过率"},
    "metric_time":       {"en": "time",                       "zh": "耗时"},
    "metric_tokens":     {"en": "tokens",                     "zh": "tokens"},
    "lang_toggle_zh":    {"en": "中文",                        "zh": "中文"},
    "lang_toggle_en":    {"en": "EN",                         "zh": "EN"},
}


def i18n(key: str) -> str:
    """Emit a dual-language span. CSS picks which half to show."""
    pair = I18N.get(key)
    if not pair:
        return key
    en = html.escape(pair["en"], quote=True)
    zh = html.escape(pair["zh"], quote=True)
    return f'<span class="i18n" data-en="{en}" data-zh="{zh}"></span>'


# ---- data loading --------------------------------------------------------


@dataclass
class RunData:
    name: str
    date: str
    path: Path
    summary: dict[str, Any]


@dataclass
class VerdictData:
    repo: dict[str, Any]
    claims: list[dict[str, Any]]
    verdict_md: str
    verdict_input: dict[str, Any]
    runs: list[RunData] = field(default_factory=list)
    date: str = ""

    @property
    def bucket(self) -> str:
        return str(self.verdict_input.get("final_bucket") or "unknown")

    @property
    def recommended_bucket(self) -> str:
        return str(self.verdict_input.get("recommended_bucket") or self.bucket)

    @property
    def archetype(self) -> str:
        return str(self.repo.get("archetype") or "unknown")

    @property
    def display_name(self) -> str:
        return str(self.repo.get("display_name") or self.repo.get("repo") or "")

    @property
    def owner_repo(self) -> str:
        return f"{self.repo.get('owner','?')}/{self.repo.get('repo','?')}"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _latest_verdict_files(repo_dir: Path, date: str | None) -> tuple[Path, Path | None]:
    verdicts_dir = repo_dir / "verdicts"
    if not verdicts_dir.exists():
        return None, None  # type: ignore

    md_files = sorted(verdicts_dir.glob("*-final-verdict.md"), reverse=True)
    if date:
        md_files = [p for p in md_files if p.name.startswith(date)]
    md_path = md_files[0] if md_files else None

    input_files = sorted(verdicts_dir.glob("*-verdict-input.yaml"), reverse=True)
    if date:
        input_files = [p for p in input_files if p.name.startswith(date)]
    input_path = input_files[0] if input_files else None

    return md_path, input_path


def load_verdict(slug: str, date: str | None) -> VerdictData:
    repo_dir = REPO_EVALS_ROOT / "repos" / slug
    if not repo_dir.exists():
        print(f"No scaffold at {repo_dir}", file=sys.stderr)
        sys.exit(2)

    repo = _read_yaml(repo_dir / "repo.yaml")
    claim_map = _read_yaml(repo_dir / "claims" / "claim-map.yaml")
    claims = list(claim_map.get("claims") or [])

    md_path, input_path = _latest_verdict_files(repo_dir, date)
    verdict_md = md_path.read_text() if md_path and md_path.exists() else ""
    verdict_input = _read_yaml(input_path) if input_path else {}

    # Derive date from whatever's available
    derived_date = ""
    if md_path:
        derived_date = md_path.stem.split("-final-verdict")[0]
    elif input_path:
        derived_date = input_path.stem.split("-verdict-input")[0]

    runs: list[RunData] = []
    runs_root = repo_dir / "runs"
    if runs_root.exists():
        for date_dir in sorted(runs_root.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            for run_dir in sorted(date_dir.iterdir()):
                if not run_dir.is_dir():
                    continue
                summary_path = run_dir / "run-summary.yaml"
                summary = _read_yaml(summary_path)
                if not summary:
                    continue
                runs.append(
                    RunData(
                        name=run_dir.name,
                        date=date_dir.name,
                        path=run_dir,
                        summary=summary,
                    )
                )

    return VerdictData(
        repo=repo,
        claims=claims,
        verdict_md=verdict_md,
        verdict_input=verdict_input,
        runs=runs,
        date=derived_date,
    )


# ---- HTML rendering ------------------------------------------------------


def _esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


def render_claim_row(claim: dict[str, Any]) -> str:
    cid = _esc(claim.get("id", ""))
    title = _esc(claim.get("title", ""))
    prio = _esc(claim.get("priority", "medium"))
    status = str(claim.get("status", "unknown"))
    emoji = STATUS_EMOJI.get(status, "·")
    skip = claim.get("skip_reason", "")
    area = _esc(claim.get("area", ""))
    return (
        f"<tr class=\"prio-{prio}\">"
        f"<td class=\"cid\">{cid}</td>"
        f"<td>{title}</td>"
        f"<td><span class=\"badge prio-{prio}\">{prio}</span></td>"
        f"<td>{area}</td>"
        f"<td class=\"status\">{emoji} {_esc(status)}</td>"
        f"<td class=\"skip\">{_esc(skip) if skip else ''}</td>"
        f"</tr>"
    )


def render_run_card(run: RunData) -> str:
    metrics = run.summary.get("metrics") or {}
    baseline_metrics = run.summary.get("metrics_baseline") or {}
    rbc = run.summary.get("results_by_claim") or {}

    def _fmt_metrics(m: dict[str, Any]) -> str:
        if not m:
            return f"<span class=\"dim\">{i18n('no_metrics')}</span>"
        pr = m.get("pass_rate")
        el = m.get("elapsed_time_sec")
        tok = m.get("token_usage") or {}
        pr_s = f"{pr:.0%}" if isinstance(pr, (int, float)) else "?"
        el_s = f"{el:.1f}s" if isinstance(el, (int, float)) else "?"
        tok_s = f"in {tok.get('input','?')} / out {tok.get('output','?')}"
        return (
            f"<span class=\"metric\"><b>{i18n('metric_pass')}</b> {pr_s}</span>"
            f"<span class=\"metric\"><b>{i18n('metric_time')}</b> {el_s}</span>"
            f"<span class=\"metric\"><b>{i18n('metric_tokens')}</b> {tok_s}</span>"
        )

    rbc_html = ""
    if rbc:
        items = [
            f"<li>{STATUS_EMOJI.get(str(v), '·')} <code>{_esc(k)}</code> {_esc(v)}</li>"
            for k, v in rbc.items()
        ]
        rbc_html = f"<ul class=\"rbc\">{''.join(items)}</ul>"

    baseline_html = ""
    if baseline_metrics:
        baseline_html = (
            f"<div class=\"baseline\"><b>{i18n('baseline_label')}</b> "
            f"{_fmt_metrics(baseline_metrics)}</div>"
        )

    return (
        f"<article class=\"run-card\">"
        f"<h3>{_esc(run.name)}</h3>"
        f"<p class=\"dim\">{i18n('run_on')} {_esc(run.date)}</p>"
        f"<div class=\"metrics-row\">{_fmt_metrics(metrics)}</div>"
        f"{baseline_html}"
        f"{rbc_html}"
        f"</article>"
    )


def mermaid_ceiling_diagram(vd: VerdictData) -> str:
    inputs = vd.verdict_input.get("inputs_summary") or {}
    ceilings = vd.verdict_input.get("ceiling_reasons") or []
    core_tested = inputs.get("core_layer_tested")
    evidence = inputs.get("evidence_completeness") or "unknown"

    lines = [
        "graph LR",
        f"  A[archetype: {vd.archetype}] --> B{{core_layer_tested?}}",
        f"  B -->|{core_tested}| C[evidence: {evidence}]",
        f"  C --> D([recommended: {vd.recommended_bucket}])",
    ]
    if ceilings:
        lines.append(f"  D --> E([final: {vd.bucket}])")
        for i, reason in enumerate(ceilings):
            safe = str(reason).replace('"', "'")[:60]
            lines.append(f"  D -.ceiling {i+1}: {safe}.-> E")
    else:
        lines.append(f"  D --> E([final: {vd.bucket}])")
    return "\n".join(lines)


def render_html(vd: VerdictData, initial_lang: str = "auto") -> str:
    bucket = vd.bucket
    emoji = BUCKET_EMOJI.get(bucket, "·")
    bucket_color = BUCKET_COLOR.get(bucket, "#64748b")

    inputs = vd.verdict_input.get("inputs_summary") or {}
    confidence = _esc(vd.verdict_input.get("confidence") or "unknown")
    ceilings = vd.verdict_input.get("ceiling_reasons") or []
    blocking = vd.verdict_input.get("blocking_issues") or []

    none_li = f'<li class="dim">{i18n("none")}</li>'
    ceilings_html = "".join(f"<li>{_esc(r)}</li>" for r in ceilings) or none_li
    blocking_html = "".join(f"<li>{_esc(b)}</li>" for b in blocking) or none_li

    claim_rows = "".join(render_claim_row(c) for c in vd.claims)
    run_cards = "".join(render_run_card(r) for r in vd.runs)

    # Aggregate metrics for chart (first run only — simplest honest view)
    first_run_metrics = (vd.runs[0].summary.get("metrics") if vd.runs else {}) or {}
    baseline_metrics = (
        vd.runs[0].summary.get("metrics_baseline") if vd.runs else {}
    ) or {}
    chart_data = {
        "labels": ["pass_rate", "elapsed_time_sec", "token_output"],
        "with": [
            float(first_run_metrics.get("pass_rate") or 0),
            float(first_run_metrics.get("elapsed_time_sec") or 0),
            float((first_run_metrics.get("token_usage") or {}).get("output") or 0),
        ],
        "baseline": [
            float(baseline_metrics.get("pass_rate") or 0),
            float(baseline_metrics.get("elapsed_time_sec") or 0),
            float((baseline_metrics.get("token_usage") or {}).get("output") or 0),
        ],
    }

    verdict_md_escaped = _esc(vd.verdict_md)
    mermaid_body = mermaid_ceiling_diagram(vd)

    # Pre-paint lang attribute: avoids the "flash of wrong language" when
    # the CLI caller pre-picks a language. "auto" still works but will
    # flip to the correct one as soon as the <script> runs.
    server_lang = initial_lang if initial_lang in ("en", "zh") else "en"

    return f"""<!DOCTYPE html>
<html lang="{server_lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{emoji} {_esc(vd.owner_repo)} — verdict</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
:root {{
  --font-body: 'IBM Plex Sans', system-ui, sans-serif;
  --font-mono: 'IBM Plex Mono', 'SF Mono', Consolas, monospace;
  --bg: #faf7f5; --surface: #ffffff; --surface2: #f5f0ec;
  --border: rgba(0,0,0,.08); --border-bright: rgba(0,0,0,.15);
  --text: #292017; --text-dim: #8a7e72; --accent: {bucket_color};
  --accent-dim: {bucket_color}15;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #1a1412; --surface: #231d1a; --surface2: #2e2622;
    --border: rgba(255,255,255,.07); --border-bright: rgba(255,255,255,.14);
    --text: #ede5dd; --text-dim: #a69889;
  }}
}}
* {{ box-sizing: border-box; }}
body {{ font-family: var(--font-body); background: var(--bg); color: var(--text); margin: 0; padding: 32px 24px; line-height: 1.55; }}
main {{ max-width: 1080px; margin: 0 auto; }}
.hero {{ padding: 40px 32px; border-radius: 18px; background: var(--surface); border: 1px solid var(--border); margin-bottom: 32px; position: relative; overflow: hidden; }}
.hero::before {{ content: ""; position: absolute; inset: 0; background: radial-gradient(circle at 80% 20%, var(--accent-dim), transparent 60%); pointer-events: none; }}
.hero > * {{ position: relative; }}
.hero .crumb {{ font-family: var(--font-mono); font-size: 13px; color: var(--text-dim); text-transform: uppercase; letter-spacing: .08em; }}
.hero h1 {{ font-size: 42px; margin: 12px 0 8px; font-weight: 700; }}
.hero .owner-repo {{ font-family: var(--font-mono); font-size: 16px; color: var(--text-dim); margin-bottom: 28px; }}
.bucket-banner {{ display: inline-flex; align-items: baseline; gap: 14px; padding: 18px 28px; border-radius: 14px; background: var(--accent-dim); border: 2px solid var(--accent); font-weight: 600; }}
.bucket-banner .emoji {{ font-size: 48px; line-height: 1; }}
.bucket-banner .name {{ font-size: 28px; color: var(--accent); font-weight: 700; }}
.bucket-banner .conf {{ font-size: 14px; color: var(--text-dim); font-family: var(--font-mono); }}
.meta {{ display: flex; gap: 24px; margin-top: 22px; flex-wrap: wrap; font-family: var(--font-mono); font-size: 13px; color: var(--text-dim); }}
.meta b {{ color: var(--text); font-weight: 500; }}
section {{ margin-bottom: 40px; }}
h2 {{ font-size: 22px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }}
.grid-two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
@media (max-width: 720px) {{ .grid-two {{ grid-template-columns: 1fr; }} }}
.card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
.card h3 {{ font-size: 15px; margin: 0 0 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--text-dim); font-weight: 600; }}
.card ul {{ margin: 0; padding-left: 20px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); }}
th {{ font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--text-dim); font-weight: 600; background: var(--surface2); }}
.cid {{ font-family: var(--font-mono); font-size: 13px; color: var(--text-dim); }}
.badge {{ display: inline-block; padding: 3px 10px; border-radius: 99px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; }}
.badge.prio-critical {{ background: #dc262620; color: #dc2626; }}
.badge.prio-high     {{ background: #d9770620; color: #d97706; }}
.badge.prio-medium   {{ background: #0891b220; color: #0891b2; }}
.badge.prio-low      {{ background: #64748b20; color: #64748b; }}
.skip {{ font-size: 12px; color: var(--text-dim); font-style: italic; }}
.run-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 16px; }}
.run-card h3 {{ font-family: var(--font-mono); font-size: 15px; margin: 0; }}
.run-card p.dim {{ margin: 4px 0 12px; color: var(--text-dim); font-size: 13px; }}
.metrics-row {{ display: flex; gap: 16px; flex-wrap: wrap; font-family: var(--font-mono); font-size: 13px; }}
.metric {{ background: var(--surface2); padding: 6px 12px; border-radius: 8px; }}
.metric b {{ color: var(--text-dim); font-weight: 500; margin-right: 6px; }}
.baseline {{ margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--border); font-size: 13px; color: var(--text-dim); }}
.rbc {{ list-style: none; padding: 0; margin: 12px 0 0; display: flex; flex-wrap: wrap; gap: 8px; font-size: 13px; }}
.rbc li {{ background: var(--surface2); padding: 4px 10px; border-radius: 6px; }}
.rbc code {{ font-family: var(--font-mono); font-size: 12px; }}
.mermaid {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
pre.md {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 20px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; font-family: var(--font-mono); font-size: 13px; line-height: 1.6; }}
footer {{ margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--border); font-size: 12px; color: var(--text-dim); font-family: var(--font-mono); }}
.dim {{ color: var(--text-dim); }}

/* ---- bilingual UI chrome (en / zh) ---- */
.i18n::before {{ content: attr(data-en); }}
html[lang="zh"] .i18n::before {{ content: attr(data-zh); }}
.lang-toggle {{ position: fixed; top: 20px; right: 20px; background: var(--surface); border: 1px solid var(--border-bright); border-radius: 999px; padding: 4px; display: inline-flex; gap: 2px; font-family: var(--font-mono); font-size: 12px; z-index: 100; box-shadow: 0 2px 10px rgba(0,0,0,.06); }}
.lang-toggle button {{ background: transparent; border: none; color: var(--text-dim); padding: 6px 14px; border-radius: 999px; cursor: pointer; font-family: inherit; font-size: inherit; transition: background .15s, color .15s; }}
.lang-toggle button:hover {{ color: var(--text); }}
html[lang="en"] .lang-toggle button[data-lang="en"],
html[lang="zh"] .lang-toggle button[data-lang="zh"] {{
  background: var(--accent); color: white;
}}
</style>
</head>
<body>
<main>

  <div class="lang-toggle" aria-label="language toggle">
    <button data-lang="en" onclick="setLang('en')">EN</button>
    <button data-lang="zh" onclick="setLang('zh')">中文</button>
  </div>

  <div class="hero">
    <div class="crumb">{i18n("crumb")} · {_esc(vd.date)}</div>
    <h1>{_esc(vd.display_name)}</h1>
    <div class="owner-repo">{_esc(vd.owner_repo)}</div>
    <div class="bucket-banner">
      <span class="emoji">{emoji}</span>
      <span class="name">{_esc(bucket)}</span>
      <span class="conf">{i18n("confidence")}: {confidence}</span>
    </div>
    <div class="meta">
      <span><b>{i18n("archetype")}</b> {_esc(vd.archetype)}</span>
      <span><b>{i18n("claims")}</b> {len(vd.claims)}</span>
      <span><b>{i18n("critical_covered")}</b> {inputs.get('critical_covered','?')}/{inputs.get('critical_total','?')}</span>
      <span><b>{i18n("runs")}</b> {len(vd.runs)}</span>
    </div>
  </div>

  <section>
    <h2>{i18n("ceilings_section")}</h2>
    <div class="grid-two">
      <div class="card">
        <h3>{i18n("ceiling_reasons")}</h3>
        <ul>{ceilings_html}</ul>
      </div>
      <div class="card">
        <h3>{i18n("blocking_issues")}</h3>
        <ul>{blocking_html}</ul>
      </div>
    </div>
  </section>

  <section>
    <h2>{i18n("derivation")}</h2>
    <div class="mermaid">
{mermaid_body}
    </div>
  </section>

  <section>
    <h2>{i18n("claims_section")}</h2>
    <table>
      <thead><tr><th>{i18n("col_id")}</th><th>{i18n("col_title")}</th><th>{i18n("col_priority")}</th><th>{i18n("col_area")}</th><th>{i18n("col_status")}</th><th>{i18n("col_skip")}</th></tr></thead>
      <tbody>{claim_rows}</tbody>
    </table>
  </section>

  <section>
    <h2>{i18n("runs_section")}</h2>
    <canvas id="metrics-chart" width="400" height="200"></canvas>
    {run_cards}
  </section>

  <section>
    <h2>{i18n("verdict_section")}</h2>
    <pre class="md">{verdict_md_escaped}</pre>
  </section>

  <footer>
    <span class="i18n" data-en="Rendered by repo-evals render_verdict_html.py · source" data-zh="由 repo-evals render_verdict_html.py 生成 · 源"></span>: {_esc(vd.repo.get('repo_url') or '—')}
  </footer>

</main>

<script>
const LANG_KEY = 'repoEvalsVerdictLang';
const INITIAL_LANG = {json.dumps(initial_lang)};

function detectLang() {{
  // Priority: explicit URL ?lang=xx > localStorage > CLI/initial > navigator.language > 'en'
  try {{
    const p = new URLSearchParams(location.search).get('lang');
    if (p === 'en' || p === 'zh') return p;
  }} catch (_) {{}}
  const stored = localStorage.getItem(LANG_KEY);
  if (stored === 'en' || stored === 'zh') return stored;
  if (INITIAL_LANG === 'en' || INITIAL_LANG === 'zh') return INITIAL_LANG;
  if ((navigator.language || '').toLowerCase().startsWith('zh')) return 'zh';
  return 'en';
}}

function setLang(lang) {{
  document.documentElement.lang = lang;
  try {{ localStorage.setItem(LANG_KEY, lang); }} catch (_) {{}}
  if (window._metricsChart) {{
    const labels = lang === 'zh'
      ? {{ with: '有该 repo', baseline: 'baseline（无该 repo）' }}
      : {{ with: 'with repo',  baseline: 'baseline (no repo)' }};
    window._metricsChart.data.datasets[0].label = labels.with;
    window._metricsChart.data.datasets[1].label = labels.baseline;
    window._metricsChart.update();
  }}
}}

setLang(detectLang());

mermaid.initialize({{
  startOnLoad: true,
  theme: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default',
  securityLevel: 'loose'
}});

const chartData = {json.dumps(chart_data)};
const ctx = document.getElementById('metrics-chart');
if (ctx) {{
  const startLang = document.documentElement.lang;
  const startLabels = startLang === 'zh'
    ? {{ with: '有该 repo', baseline: 'baseline（无该 repo）' }}
    : {{ with: 'with repo',  baseline: 'baseline (no repo)' }};
  window._metricsChart = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: chartData.labels,
      datasets: [
        {{ label: startLabels.with, data: chartData.with, backgroundColor: '{bucket_color}cc' }},
        {{ label: startLabels.baseline, data: chartData.baseline, backgroundColor: '#94a3b8aa' }}
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ position: 'top' }} }},
      scales: {{ y: {{ beginAtZero: true }} }}
    }}
  }});
}}
</script>

</body>
</html>
"""


# ---- main ---------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="Repo slug, e.g. owner--repo")
    parser.add_argument(
        "--date",
        default=None,
        help="Date prefix of the verdict to render; default = latest",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the rendered HTML in the default browser",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path override; default = verdicts/<date>-verdict.html",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "zh", "auto"],
        default="auto",
        help=(
            "Initial language for UI chrome. 'auto' (default) detects from "
            "navigator.language at load time; 'en' or 'zh' forces the pre-"
            "paint language. Users can always toggle at runtime; choice "
            "persists in localStorage."
        ),
    )
    args = parser.parse_args()

    vd = load_verdict(args.slug, args.date)
    if not vd.verdict_input and not vd.claims:
        print(
            f"No verdict input and no claims found for {args.slug} — "
            f"run scripts/verdict_calculator.py first.",
            file=sys.stderr,
        )
        return 2

    if args.output:
        out_path = Path(args.output).resolve()
    else:
        repo_dir = REPO_EVALS_ROOT / "repos" / args.slug
        date = vd.date or "latest"
        out_path = repo_dir / "verdicts" / f"{date}-verdict.html"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_text = render_html(vd, initial_lang=args.lang)
    out_path.write_text(html_text)
    print(f"Wrote {out_path}")

    if args.open:
        webbrowser.open(f"file://{out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
