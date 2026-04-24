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
            return "<span class=\"dim\">no metrics recorded</span>"
        pr = m.get("pass_rate")
        el = m.get("elapsed_time_sec")
        tok = m.get("token_usage") or {}
        pr_s = f"{pr:.0%}" if isinstance(pr, (int, float)) else "?"
        el_s = f"{el:.1f}s" if isinstance(el, (int, float)) else "?"
        tok_s = f"in {tok.get('input','?')} / out {tok.get('output','?')}"
        return (
            f"<span class=\"metric\"><b>pass</b> {pr_s}</span>"
            f"<span class=\"metric\"><b>time</b> {el_s}</span>"
            f"<span class=\"metric\"><b>tokens</b> {tok_s}</span>"
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
            f"<div class=\"baseline\"><b>baseline (without repo):</b> "
            f"{_fmt_metrics(baseline_metrics)}</div>"
        )

    return (
        f"<article class=\"run-card\">"
        f"<h3>{_esc(run.name)}</h3>"
        f"<p class=\"dim\">run on {_esc(run.date)}</p>"
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


def render_html(vd: VerdictData) -> str:
    bucket = vd.bucket
    emoji = BUCKET_EMOJI.get(bucket, "·")
    bucket_color = BUCKET_COLOR.get(bucket, "#64748b")

    inputs = vd.verdict_input.get("inputs_summary") or {}
    confidence = _esc(vd.verdict_input.get("confidence") or "unknown")
    ceilings = vd.verdict_input.get("ceiling_reasons") or []
    blocking = vd.verdict_input.get("blocking_issues") or []

    ceilings_html = "".join(f"<li>{_esc(r)}</li>" for r in ceilings) or "<li class=\"dim\">none</li>"
    blocking_html = "".join(f"<li>{_esc(b)}</li>" for b in blocking) or "<li class=\"dim\">none</li>"

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

    return f"""<!DOCTYPE html>
<html lang="en">
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
</style>
</head>
<body>
<main>

  <div class="hero">
    <div class="crumb">repo-evals · verdict · {_esc(vd.date)}</div>
    <h1>{_esc(vd.display_name)}</h1>
    <div class="owner-repo">{_esc(vd.owner_repo)}</div>
    <div class="bucket-banner">
      <span class="emoji">{emoji}</span>
      <span class="name">{_esc(bucket)}</span>
      <span class="conf">confidence: {confidence}</span>
    </div>
    <div class="meta">
      <span><b>archetype</b> {_esc(vd.archetype)}</span>
      <span><b>claims</b> {len(vd.claims)}</span>
      <span><b>critical covered</b> {inputs.get('critical_covered','?')}/{inputs.get('critical_total','?')}</span>
      <span><b>runs</b> {len(vd.runs)}</span>
    </div>
  </div>

  <section>
    <h2>Ceilings &amp; blocking issues</h2>
    <div class="grid-two">
      <div class="card">
        <h3>Ceiling reasons</h3>
        <ul>{ceilings_html}</ul>
      </div>
      <div class="card">
        <h3>Blocking issues</h3>
        <ul>{blocking_html}</ul>
      </div>
    </div>
  </section>

  <section>
    <h2>Derivation</h2>
    <div class="mermaid">
{mermaid_body}
    </div>
  </section>

  <section>
    <h2>Claims</h2>
    <table>
      <thead><tr><th>ID</th><th>Title</th><th>Priority</th><th>Area</th><th>Status</th><th>Skip reason</th></tr></thead>
      <tbody>{claim_rows}</tbody>
    </table>
  </section>

  <section>
    <h2>Runs &amp; metrics</h2>
    <canvas id="metrics-chart" width="400" height="200"></canvas>
    {run_cards}
  </section>

  <section>
    <h2>Full verdict (markdown)</h2>
    <pre class="md">{verdict_md_escaped}</pre>
  </section>

  <footer>
    Rendered by repo-evals render_verdict_html.py · source: {_esc(vd.repo.get('repo_url') or '—')}
  </footer>

</main>

<script>
mermaid.initialize({{
  startOnLoad: true,
  theme: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default',
  securityLevel: 'loose'
}});

const chartData = {json.dumps(chart_data)};
const ctx = document.getElementById('metrics-chart');
if (ctx) {{
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: chartData.labels,
      datasets: [
        {{ label: 'with repo', data: chartData.with, backgroundColor: '{bucket_color}cc' }},
        {{ label: 'baseline (no repo)', data: chartData.baseline, backgroundColor: '#94a3b8aa' }}
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
    html_text = render_html(vd)
    out_path.write_text(html_text)
    print(f"Wrote {out_path}")

    if args.open:
        webbrowser.open(f"file://{out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
