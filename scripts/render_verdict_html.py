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
import importlib.util
import json
import os
import subprocess
import sys
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _load_verdict_calculator():
    """Import verdict_calculator.py as a sibling script so we can run
    the same compute_verdict() the CLI uses. Avoids drift where the HTML
    shows different numbers than the calculator prints."""
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(
        "_rv_calc", here / "verdict_calculator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot locate verdict_calculator.py next to render_verdict_html.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_VC = _load_verdict_calculator()
compute_verdict = _VC.compute_verdict

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
    # product-facing sections (new)
    "what_it_does":      {"en": "What this repo does",        "zh": "这个 repo 是做什么的"},
    "capabilities":      {"en": "Capabilities",               "zh": "能做什么"},
    "verified":          {"en": "verified",                   "zh": "已验证"},
    "failed_verification":{"en":"failed verification",        "zh": "验证失败"},
    "untested_label":    {"en": "not tested",                 "zh": "未测试"},
    "skip_note":         {"en": "skip reason",                "zh": "跳过原因"},
    "evidence":          {"en": "evidence",                   "zh": "证据"},
    "quality":           {"en": "Quality at a glance",        "zh": "质量速览"},
    "q_coverage":        {"en": "Coverage",                   "zh": "覆盖度"},
    "q_reliability":     {"en": "Reliability",                "zh": "可靠性"},
    "q_risk":            {"en": "Residual risk",              "zh": "剩余风险"},
    "technical_details": {"en": "Technical details (expand to see)",
                          "zh": "技术细节（展开查看）"},
    "test_log":          {"en": "Test log — all probes we ran",
                          "zh": "测试日志 — 我们跑过的所有探针"},
    "eval_log":          {"en": "Eval probes",                "zh": "Eval 探针"},
    "trigger_log":       {"en": "Trigger tests",              "zh": "触发测试"},
    "source_raw":        {"en": "Raw verdict archive (authored by evaluator)",
                          "zh": "原始 verdict 存档（评测者原文）"},
    "best_for":          {"en": "Best for",                   "zh": "最适合谁用"},
    "watch_out":         {"en": "Watch out",                  "zh": "注意事项"},
    "we_verified":       {"en": "What we verified",           "zh": "我们验证了什么"},
    "verdict_pill":      {"en": "verdict",                    "zh": "评测结果"},
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


def dual_lang(val: Any, fallback: str = "") -> str:
    """Render an authored value (possibly a {en, zh} dict) as a bilingual
    span. If the value is a plain string, both data-en and data-zh hold
    that same string — honest representation of 'authored in one language'.
    """
    if isinstance(val, dict):
        en_text = str(val.get("en") or val.get("zh") or fallback)
        zh_text = str(val.get("zh") or val.get("en") or fallback)
    else:
        s = str(val or fallback)
        en_text = zh_text = s
    en = html.escape(en_text, quote=True)
    zh = html.escape(zh_text, quote=True)
    if not en_text and not zh_text:
        return ""
    return f'<span class="i18n" data-en="{en}" data-zh="{zh}"></span>'


def dual_lang_plain(val: Any) -> str:
    """Extract the English variant from a possibly-bilingual value, for
    use inside <title>, Mermaid text, etc. where span elements won't
    render. Returns a plain string."""
    if isinstance(val, dict):
        return str(val.get("en") or val.get("zh") or "")
    return str(val or "")


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

    # --- Merge eval results into claim statuses -------------------------
    # If any run has results_by_claim filled in (either by hand or by
    # run_evals.py), those override the claim-map's initial status. This
    # is why "I said it was passed but the run said failed" → we trust
    # the run.
    claim_status_override: dict[str, str] = {}
    for r in runs:
        rbc = r.summary.get("results_by_claim") or {}
        for cid, status in rbc.items():
            if cid and status:
                claim_status_override[str(cid)] = str(status)
    for c in claims:
        cid = str(c.get("id", ""))
        if cid in claim_status_override:
            c["status"] = claim_status_override[cid]

    # --- Compute the verdict live (don't read a stale final bucket) -----
    # verdict_input is the *input* to verdict_calculator, not its output.
    # We call compute_verdict() at render time so the HTML always matches
    # the latest claim statuses (including any just-merged eval results).
    verdict_output: dict[str, Any] = {}
    if verdict_input:
        try:
            verdict_output = compute_verdict(verdict_input)
        except Exception as exc:  # fail soft — still render the page
            print(f"(warn) verdict_calculator failed: {exc}", file=sys.stderr)
            verdict_output = {}

    return VerdictData(
        repo=repo,
        claims=claims,
        verdict_md=verdict_md,
        verdict_input=verdict_output or verdict_input,
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


def product_one_liner(vd: VerdictData) -> str:
    """One-sentence 'what this repo does' as a bilingual span. Picks
    from repo.yaml.product_view.one_liner first (the best source),
    falls back to the first line of notes."""
    pv = vd.repo.get("product_view") or {}
    if pv.get("one_liner"):
        return dual_lang(pv["one_liner"])
    for key in ("one_liner", "product_summary", "description"):
        val = vd.repo.get(key)
        if val:
            return dual_lang(val)
    notes = vd.repo.get("notes") or ""
    if isinstance(notes, str) and notes.strip():
        first_line = notes.strip().splitlines()[0][:280]
        return dual_lang(first_line)
    return dual_lang(f"An {vd.archetype} repo.")


def render_capability_cards(vd: VerdictData) -> str:
    """One visual card per critical/high claim — product-facing.

    Uses claim.user_title / user_description / user_icon if present
    (these are typically bilingual {en, zh} dicts). Falls back to the
    technical claim.title / business_expectation when user fields are
    missing, which keeps old claim-maps rendering, just less beautifully.
    """
    VISIBLE_PRIORITIES = {"critical", "high"}
    visible = [c for c in vd.claims if str(c.get("priority", "")) in VISIBLE_PRIORITIES]
    if not visible:
        visible = vd.claims  # tiny scaffolds — show them all

    def _card(c: dict[str, Any]) -> str:
        status = str(c.get("status", "unknown"))
        status_emoji = STATUS_EMOJI.get(status, "·")
        cid = _esc(c.get("id", ""))

        icon = str(c.get("user_icon") or "").strip() or status_emoji

        user_title_val = c.get("user_title") or c.get("title") or c.get("id", "")
        user_desc_val = (
            c.get("user_description")
            or c.get("business_expectation")
            or ""
        )

        title_span = dual_lang(user_title_val)
        desc_span = dual_lang(user_desc_val)

        status_label_key = {
            "passed": "verified",
            "passed_with_concerns": "verified",
            "partial": "verified",
            "failed": "failed_verification",
            "failed_partial": "failed_verification",
            "untested": "untested_label",
        }.get(status, "untested_label")

        # Skip reason — surface only when untested (it's the reason we didn't
        # verify). For passed claims this field is usually absent anyway.
        skip_html = ""
        if status == "untested":
            skip_val = c.get("skip_reason")
            if skip_val:
                skip_html = (
                    f'<p class="cap-skip">{dual_lang(skip_val)}</p>'
                )

        desc_html = f'<p class="cap-description">{desc_span}</p>' if desc_span else ""

        return (
            f'<article class="capability-card status-{status}">'
            f'<div class="cap-icon-wrap"><span class="cap-icon">{icon}</span></div>'
            f'<div class="cap-body">'
            f'  <header class="cap-header">'
            f'    <span class="cap-status-badge cap-status-{status}">{status_emoji} {i18n(status_label_key)}</span>'
            f'    <span class="cap-id">{cid}</span>'
            f'  </header>'
            f'  <h3 class="cap-title">{title_span}</h3>'
            f'  {desc_html}'
            f'  {skip_html}'
            f'</div>'
            f'</article>'
        )

    return "\n".join(_card(c) for c in visible)


def render_best_for(vd: VerdictData) -> str:
    """Who should adopt this repo — a pull-quote style block."""
    pv = vd.repo.get("product_view") or {}
    val = pv.get("best_for")
    if not val:
        return ""
    return (
        f'<section class="best-for">'
        f'<div class="best-for-label">{i18n("best_for")}</div>'
        f'<div class="best-for-body">{dual_lang(val)}</div>'
        f'</section>'
    )


def render_watch_out(vd: VerdictData) -> str:
    """Known risks / caveats — pull-quote style, accent warning color."""
    pv = vd.repo.get("product_view") or {}
    val = pv.get("watch_out")
    if not val:
        return ""
    return (
        f'<section class="watch-out">'
        f'<div class="watch-out-label">{i18n("watch_out")}</div>'
        f'<div class="watch-out-body">{dual_lang(val)}</div>'
        f'</section>'
    )


def render_quality_summary(vd: VerdictData) -> str:
    """Three one-line answers a non-technical reader cares about."""
    inputs = vd.verdict_input.get("inputs_summary") or {}
    crit_covered = inputs.get("critical_covered")
    crit_total = inputs.get("critical_total")
    coverage = f"{crit_covered}/{crit_total} critical" if (
        crit_covered is not None and crit_total is not None
    ) else "—"

    ceilings = vd.verdict_input.get("ceiling_reasons") or []
    reliability = ceilings[0] if ceilings else (
        "no major ceilings triggered" if vd.bucket in ("reusable", "recommendable")
        else "not evaluated"
    )
    reliability = str(reliability)[:120]

    blocking = vd.verdict_input.get("blocking_issues") or []
    residual_risk = blocking[0] if blocking else "—"
    residual_risk = str(residual_risk)[:120]

    def _row(label_key: str, value: str) -> str:
        return (
            f'<div class="quality-row">'
            f'<span class="quality-label">{i18n(label_key)}</span>'
            f'<span class="quality-value">{_esc(value)}</span>'
            f'</div>'
        )

    return (
        _row("q_coverage", coverage)
        + _row("q_reliability", reliability)
        + _row("q_risk", residual_risk)
    )


def render_test_log(vd: VerdictData) -> str:
    """Full log of every probe we ran — collapsible in the UI."""
    if not vd.runs:
        return f"<p class=\"dim\">{i18n('none')}</p>"

    blocks: list[str] = []
    for run in vd.runs:
        summary = run.summary
        metrics = summary.get("metrics") or {}
        rbc = summary.get("results_by_claim") or {}
        pr = metrics.get("pass_rate")
        pr_s = f"{pr:.0%}" if isinstance(pr, (int, float)) else "—"

        rbc_items = "".join(
            f'<li>{STATUS_EMOJI.get(str(v),"·")} <code>{_esc(k)}</code> {_esc(v)}</li>'
            for k, v in rbc.items()
        )
        rbc_block = f'<ul class="log-rbc">{rbc_items}</ul>' if rbc_items else ""

        blocks.append(
            f'<article class="log-run">'
            f'<h4><code>{_esc(run.name)}</code> · {_esc(run.date)} · pass_rate={pr_s}</h4>'
            f'{rbc_block}'
            f'</article>'
        )
    return "\n".join(blocks)


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

    # Product-facing pieces (built from structured data, so they respect
    # whatever language the evaluator authored claim-map and repo.yaml in).
    # product_one_liner returns a bilingual span already — do NOT escape.
    product_one_liner_html = product_one_liner(vd)
    capability_cards_html = render_capability_cards(vd)
    best_for_html = render_best_for(vd)
    watch_out_html = render_watch_out(vd)
    quality_summary_html = render_quality_summary(vd)
    test_log_html = render_test_log(vd)

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
.hero {{ padding: 56px 44px 44px; border-radius: 24px; background: var(--surface); border: 1px solid var(--border); margin-bottom: 40px; position: relative; overflow: hidden; }}
.hero::before {{ content: ""; position: absolute; inset: 0; background: radial-gradient(circle at 80% 20%, var(--accent-dim), transparent 60%); pointer-events: none; }}
.hero > * {{ position: relative; }}
.hero .crumb {{ font-family: var(--font-mono); font-size: 13px; color: var(--text-dim); text-transform: uppercase; letter-spacing: .08em; }}
.hero h1 {{ font-size: 56px; margin: 14px 0 6px; font-weight: 700; letter-spacing: -.02em; line-height: 1.05; }}
.hero .owner-repo {{ font-family: var(--font-mono); font-size: 14px; color: var(--text-dim); margin-bottom: 24px; }}
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

/* ---- product-facing sections ---- */
.what-does-it-do {{ font-size: 21px; line-height: 1.5; margin: 10px 0 30px; color: var(--text); max-width: 68ch; font-weight: 400; }}

/* Capability cards — product-page feel, not report feel */
.capabilities-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 20px; }}
.capability-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 18px; padding: 24px; display: flex; gap: 18px; transition: transform .15s, box-shadow .15s; }}
.capability-card:hover {{ transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0,0,0,.06); }}
.capability-card.status-untested {{ background: var(--surface2); opacity: .85; }}
.capability-card .cap-icon-wrap {{ flex: 0 0 auto; width: 48px; height: 48px; border-radius: 12px; background: var(--accent-dim); display: flex; align-items: center; justify-content: center; }}
.capability-card.status-untested .cap-icon-wrap {{ background: rgba(168,162,158,.15); }}
.capability-card.status-failed .cap-icon-wrap, .capability-card.status-failed_partial .cap-icon-wrap {{ background: rgba(185,28,28,.1); }}
.capability-card .cap-icon {{ font-size: 28px; line-height: 1; }}
.capability-card .cap-body {{ flex: 1 1 auto; min-width: 0; }}
.capability-card .cap-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
.capability-card .cap-status-badge {{ font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; padding: 3px 10px; border-radius: 999px; background: var(--surface2); color: var(--text-dim); }}
.capability-card .cap-status-passed, .capability-card .cap-status-passed_with_concerns, .capability-card .cap-status-partial {{ background: rgba(21,128,61,.12); color: #15803d; }}
.capability-card .cap-status-failed, .capability-card .cap-status-failed_partial {{ background: rgba(185,28,28,.12); color: #b91c1c; }}
.capability-card .cap-status-untested {{ background: rgba(168,162,158,.18); color: #57534e; }}
.capability-card .cap-id {{ margin-left: auto; font-family: var(--font-mono); font-size: 11px; color: var(--text-dim); }}
.capability-card .cap-title {{ margin: 0 0 8px; font-size: 17px; font-weight: 600; color: var(--text); line-height: 1.3; }}
.capability-card .cap-description {{ margin: 0; font-size: 14px; color: var(--text-dim); line-height: 1.55; }}
.capability-card .cap-skip {{ margin: 10px 0 0; font-size: 13px; color: var(--text-dim); font-style: italic; padding-left: 10px; border-left: 2px solid var(--border-bright); }}

/* Best-for / Watch-out — pull-quote style blocks */
.best-for, .watch-out {{ padding: 22px 26px; border-radius: 14px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 6px; }}
.best-for {{ background: rgba(21,128,61,.08); border-left: 4px solid #15803d; }}
.watch-out {{ background: rgba(180,83,9,.08); border-left: 4px solid #b45309; }}
.best-for-label, .watch-out-label {{ font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; font-weight: 700; }}
.best-for-label {{ color: #15803d; }}
.watch-out-label {{ color: #b45309; }}
.best-for-body, .watch-out-body {{ font-size: 15px; line-height: 1.55; color: var(--text); }}
.quality-grid {{ display: flex; flex-direction: column; gap: 12px; }}
.quality-row {{ display: flex; gap: 20px; padding: 14px 18px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; align-items: baseline; }}
.quality-label {{ flex: 0 0 auto; width: 140px; font-family: var(--font-mono); font-size: 13px; color: var(--text-dim); text-transform: uppercase; letter-spacing: .06em; }}
.quality-value {{ flex: 1 1 auto; font-size: 14px; color: var(--text); line-height: 1.5; }}
details.technical, details.test-log, details.raw-archive {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 0; margin-bottom: 16px; overflow: hidden; }}
details.technical > summary, details.test-log > summary, details.raw-archive > summary {{ padding: 18px 22px; cursor: pointer; font-family: var(--font-mono); font-size: 13px; color: var(--text-dim); text-transform: uppercase; letter-spacing: .06em; user-select: none; list-style: none; font-weight: 600; }}
details.technical > summary::-webkit-details-marker, details.test-log > summary::-webkit-details-marker, details.raw-archive > summary::-webkit-details-marker {{ display: none; }}
details.technical > summary::before, details.test-log > summary::before, details.raw-archive > summary::before {{ content: "▸ "; transition: transform .15s; display: inline-block; }}
details.technical[open] > summary::before, details.test-log[open] > summary::before, details.raw-archive[open] > summary::before {{ transform: rotate(90deg); }}
details.technical > .body, details.test-log > .body, details.raw-archive > .body {{ padding: 4px 22px 22px; }}
.log-run {{ border-top: 1px dashed var(--border); padding: 14px 0; }}
.log-run:first-child {{ border-top: none; padding-top: 0; }}
.log-run h4 {{ margin: 0 0 8px; font-size: 13px; font-weight: 500; color: var(--text-dim); font-family: var(--font-mono); }}
.log-run h4 code {{ color: var(--text); background: var(--surface2); padding: 1px 6px; border-radius: 4px; }}
.log-rbc {{ list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 6px; font-size: 12px; }}
.log-rbc li {{ background: var(--surface2); padding: 3px 9px; border-radius: 5px; }}
.log-rbc code {{ font-family: var(--font-mono); font-size: 11px; color: var(--text-dim); }}

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
    <p class="what-does-it-do">{product_one_liner_html}</p>
    <div class="bucket-banner">
      <span class="emoji">{emoji}</span>
      <span class="name">{_esc(bucket)}</span>
      <span class="conf">{i18n("confidence")}: {confidence}</span>
    </div>
  </div>

  {best_for_html}
  {watch_out_html}

  <section>
    <h2>{i18n("we_verified")}</h2>
    <div class="capabilities-grid">
      {capability_cards_html}
    </div>
  </section>


  <details class="technical">
    <summary>{i18n("technical_details")}</summary>
    <div class="body">

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

    </div>
  </details>

  <details class="test-log">
    <summary>{i18n("test_log")}</summary>
    <div class="body">
      {test_log_html}
    </div>
  </details>

  <details class="raw-archive">
    <summary>{i18n("source_raw")}</summary>
    <div class="body">
      <pre class="md">{verdict_md_escaped}</pre>
    </div>
  </details>

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
