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

# Sibling layers module — same scripts/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import layers as layers_mod  # noqa: E402

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


def _derive_verdict_input(repo: dict[str, Any], claims: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a verdict-input dict from repo.yaml + claim-map.yaml.

    Without a hand-authored verdict-input.yaml sidecar, the dossier
    used to render `bucket: unknown` even when repo.yaml already had
    `current_bucket: usable`. This derives the same shape that
    verdict_calculator.compute_verdict() expects, so the live
    calculation reflects the evaluator's actual claim statuses.

    Heuristics:
      - core_layer_tested is true only for an atom layer (no deferred
        molecule/compound work). Molecule and compound caps stay
        active until the evaluator explicitly hand-writes a sidecar
        with core_layer_tested: true.
      - evidence_completeness defaults to 'partial' (we have static
        artifacts and per-claim notes, no full live-run trace).

    The evaluator can always override by hand-writing a real
    verdict-input.yaml file — this only fills in for the missing case.
    """

    layer = str(repo.get("layer", "unknown")).strip().lower()
    archetype = str(repo.get("archetype", "unknown")).strip().lower()
    owner = repo.get("owner", "")
    name = repo.get("repo", "")

    # Atoms have no deferred molecule layer above them, so a fully-passed
    # static eval is the user-facing layer. Molecule + compound layers
    # have deferred live runs above them, so the core layer is untested.
    core_layer_tested = (layer == "atom")

    derived_claims: list[dict[str, Any]] = []
    for c in claims:
        derived_claims.append({
            "id": str(c.get("id", "")),
            "priority": str(c.get("priority", "medium")).lower(),
            "status": str(c.get("status", "untested")).lower(),
            # Pass `area` through so the score model can apply
            # privacy/security penalties to passed_with_concerns claims.
            "area": str(c.get("area", "") or ""),
        })

    out: dict[str, Any] = {
        "repo": f"{owner}/{name}" if owner and name else (name or owner or "unknown"),
        "archetype": archetype,
        "layer": layer,  # 2026-05-05: layer drives layer-bonus in score
        "core_layer_tested": core_layer_tested,
        "evidence_completeness": "partial",
        "claims": derived_claims,
        "_derived": True,  # marker so reviewers know this wasn't hand-authored
    }

    # Score-model inputs — read from repo.yaml when set so the 0-100
    # score can incorporate ecosystem + maintainer evidence. Each is
    # optional; the score function defaults to zero / false if missing.
    for key in (
        "stars", "archived", "has_license",
        "multilingual_readme", "release_pipeline_score",
        "eval_discipline_score", "recently_active",
    ):
        if key in repo:
            out[key] = repo[key]

    return out


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

    # If no verdict-input.yaml sidecar exists, derive one from claim-map.yaml
    # + repo.yaml so the dossier reflects what the evaluator actually wrote.
    # Without this, every freshly-evaluated repo renders as `unknown` even
    # when repo.yaml says `current_bucket: usable`.
    if not verdict_input and claims:
        verdict_input = _derive_verdict_input(repo, claims)

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

        # Editorial card — status-labeled badge maps to the raw status word.
        status_badge_text = {
            "passed": "passed",
            "passed_with_concerns": "passed",
            "partial": "partial",
            "failed": "failed",
            "failed_partial": "failed",
            "untested": "untested",
        }.get(status, status)

        return (
            f'<article class="capability-card status-{status}">'
            f'  <div class="cap-header">'
            f'    <span class="cap-badge">{_esc(status_badge_text)}</span>'
            f'    <span class="cap-id">{cid}</span>'
            f'  </div>'
            f'  <h3 class="cap-title">{title_span}</h3>'
            f'  {desc_html}'
            f'  {skip_html}'
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


def count_claim_statuses(vd: VerdictData) -> dict[str, int]:
    """Bucket every claim into one of four visible categories for the
    stats bar. 'passed_with_concerns' and 'partial' both show as
    'partial' on the bar."""
    counts = {"passed": 0, "partial": 0, "failed": 0, "untested": 0}
    for c in vd.claims:
        s = str(c.get("status", "unknown"))
        if s == "passed":
            counts["passed"] += 1
        elif s in {"passed_with_concerns", "partial"}:
            counts["partial"] += 1
        elif s in {"failed", "failed_partial"}:
            counts["failed"] += 1
        else:
            counts["untested"] += 1
    return counts


def render_stats_bar(counts: dict[str, int]) -> str:
    parts = []
    for key, cls in (("passed", "s-pass"), ("partial", "s-warn"),
                     ("failed", "s-bad"), ("untested", "s-skip")):
        n = counts.get(key, 0)
        if n > 0:
            parts.append(f'<span class="{cls}" style="flex: {n}"></span>')
    return "".join(parts) or '<span class="s-skip" style="flex: 1"></span>'


def render_stats_legend(counts: dict[str, int]) -> str:
    items = [
        ("passed", "passed", "通过", "var(--ok)"),
        ("partial", "partial", "部分", "var(--warn)"),
        ("failed", "failed", "失败", "var(--bad)"),
        ("untested", "untested", "未测", "var(--skip)"),
    ]
    html_parts = []
    for key, label_en, label_zh, color in items:
        n = counts.get(key, 0)
        if n == 0:
            continue
        html_parts.append(
            f'<span class="item">'
            f'<span class="dot" style="background:{color}"></span>'
            f'<span class="num">{n}</span> '
            f'<span class="i18n" data-en="{label_en}" data-zh="{label_zh}"></span>'
            f'</span>'
        )
    return "".join(html_parts)


def render_derivation_flow(vd: VerdictData) -> str:
    """Editorial flow diagram (hand-built HTML, no Mermaid)."""
    inputs = vd.verdict_input.get("inputs_summary") or {}
    ceilings = vd.verdict_input.get("ceiling_reasons") or []
    core_tested = inputs.get("core_layer_tested")
    evidence = inputs.get("evidence_completeness") or "—"
    core_tested_label = "True" if core_tested else "False"

    nodes = (
        f'<span class="flow-node start">archetype: {_esc(vd.archetype)}</span>'
        f'<span class="flow-arrow">→</span>'
        f'<span class="flow-node decision">core_layer_tested? '
        f'<b style="color:inherit">{core_tested_label}</b></span>'
        f'<span class="flow-arrow">→</span>'
        f'<span class="flow-node">evidence: {_esc(evidence)}</span>'
        f'<span class="flow-arrow">→</span>'
        f'<span class="flow-node">recommended: {_esc(vd.recommended_bucket)}</span>'
        f'<span class="flow-arrow">→</span>'
        f'<span class="flow-node final">final: {_esc(vd.bucket)}</span>'
    )
    notes_html = ""
    if ceilings:
        notes = "".join(
            f'<div class="note">ceiling {i+1} · {_esc(str(r))}</div>'
            for i, r in enumerate(ceilings)
        )
        notes_html = f'<div class="flow-notes">{notes}</div>'

    return (
        f'<div class="flow">'
        f'<div class="flow-row">{nodes}</div>'
        f'{notes_html}'
        f'</div>'
    )


def render_metric_tiles(vd: VerdictData) -> str:
    """Three big editorial tiles. Pull from the first run's metrics."""
    run = vd.runs[0] if vd.runs else None
    metrics = (run.summary.get("metrics") if run else {}) or {}
    baseline = (run.summary.get("metrics_baseline") if run else {}) or {}

    pr = metrics.get("pass_rate")
    el = metrics.get("elapsed_time_sec")
    tok = (metrics.get("token_usage") or {})
    pr_pct = int((pr or 0) * 100) if isinstance(pr, (int, float)) else 0
    el_val = float(el) if isinstance(el, (int, float)) else 0.0
    tok_out = int(tok.get("output") or 0)
    tok_in = int(tok.get("input") or 0)

    # Baseline comparison — stringified for display only.
    baseline_pr = baseline.get("pass_rate")
    baseline_pr_s = (
        f"baseline · {int(baseline_pr*100)}%"
        if isinstance(baseline_pr, (int, float))
        else "baseline · none"
    )
    baseline_pr_zh = (
        f"baseline · {int(baseline_pr*100)}%"
        if isinstance(baseline_pr, (int, float))
        else "baseline · 无"
    )

    # Rough bar widths — capped at 100%.
    el_bar = min(100, int(el_val / 10 * 100)) if el_val else 0
    tok_bar = min(100, int(tok_out / 500 * 100)) if tok_out else 0

    return (
        f'<div class="metric-tile">'
        f'  <div class="mt-label"><span class="i18n" data-en="pass rate" data-zh="通过率"></span></div>'
        f'  <div class="mt-value">{pr_pct}<span class="mt-unit">%</span></div>'
        f'  <div class="mt-bar"><div class="mt-bar-fill" style="width:{pr_pct}%"></div></div>'
        f'  <div class="mt-compare"><span class="i18n" '
        f'data-en="{_esc(baseline_pr_s)}" data-zh="{_esc(baseline_pr_zh)}"></span></div>'
        f'</div>'
        f'<div class="metric-tile">'
        f'  <div class="mt-label"><span class="i18n" data-en="elapsed" data-zh="耗时"></span></div>'
        f'  <div class="mt-value">{el_val:.2f}<span class="mt-unit">s</span></div>'
        f'  <div class="mt-bar"><div class="mt-bar-fill" style="width:{el_bar}%"></div></div>'
        f'  <div class="mt-compare"><span class="i18n" data-en="baseline · none" data-zh="baseline · 无"></span></div>'
        f'</div>'
        f'<div class="metric-tile">'
        f'  <div class="mt-label"><span class="i18n" data-en="token output" data-zh="token 输出"></span></div>'
        f'  <div class="mt-value">{tok_out}</div>'
        f'  <div class="mt-bar"><div class="mt-bar-fill" style="width:{tok_bar}%"></div></div>'
        f'  <div class="mt-compare"><span class="i18n" '
        f'data-en="in · {tok_in:,} / out · {tok_out}" data-zh="输入 · {tok_in:,} / 输出 · {tok_out}"></span></div>'
        f'</div>'
    )


_STATUS_SYMBOL = {
    "passed": ("●", "passed", "var(--ok)"),
    "passed_with_concerns": ("◐", "partial", "var(--warn)"),
    "partial": ("◐", "partial", "var(--warn)"),
    "failed": ("✕", "failed", "var(--bad)"),
    "failed_partial": ("✕", "failed", "var(--bad)"),
    "untested": ("○", "untested", "var(--skip)"),
}


def render_claim_ledger(vd: VerdictData) -> str:
    rows = []
    for c in vd.claims:
        status = str(c.get("status", "unknown"))
        sym, label, color = _STATUS_SYMBOL.get(status, ("·", status, "var(--text-3)"))
        prio = str(c.get("priority", "medium"))
        cid = _esc(c.get("id", ""))
        title = _esc(dual_lang_plain(c.get("title") or c.get("user_title") or c.get("id", "")))
        area = _esc(c.get("area", ""))
        skip = _esc(dual_lang_plain(c.get("skip_reason") or ""))
        rows.append(
            f'<tr class="prio-{prio}">'
            f'<td class="c-id">{cid}</td>'
            f'<td class="c-title">{title}</td>'
            f'<td><span class="prio-pill {prio}">{prio}</span></td>'
            f'<td>{area}</td>'
            f'<td class="c-status" style="color:{color}">{sym} {label}</td>'
            f'<td class="c-skip">{skip}</td>'
            f'</tr>'
        )
    return "\n".join(rows)


def render_run_cards_editorial(vd: VerdictData) -> str:
    blocks = []
    for run in vd.runs:
        summary = run.summary
        metrics = summary.get("metrics") or {}
        rbc = summary.get("results_by_claim") or {}
        pr = metrics.get("pass_rate")
        pr_pct = int(pr * 100) if isinstance(pr, (int, float)) else 0
        el = metrics.get("elapsed_time_sec")
        el_s = f"{el:.1f}s" if isinstance(el, (int, float)) else "—"
        tok = metrics.get("token_usage") or {}
        tok_s = f"in {tok.get('input','?')} / out {tok.get('output','?')}"

        # Classify each rbc result for the colored left-border.
        rbc_items = []
        for k, v in rbc.items():
            vs = str(v)
            rbc_cls = {
                "passed": "pass",
                "passed_with_concerns": "partial",
                "partial": "partial",
                "failed": "fail",
                "failed_partial": "fail",
                "untested": "skip",
            }.get(vs, "skip")
            rbc_items.append(f'<li class="{rbc_cls}">{_esc(k)} · {_esc(vs)}</li>')
        rbc_html = f'<ul class="run-rbc">{"".join(rbc_items)}</ul>' if rbc_items else ""

        blocks.append(
            f'<div class="run-card">'
            f'  <h3>{_esc(run.name)}</h3>'
            f'  <div class="run-date"><span class="i18n" data-en="executed on" '
            f'data-zh="执行于"></span> {_esc(run.date)}</div>'
            f'  <div class="run-metrics">'
            f'    <span class="run-metric"><b><span class="i18n" data-en="pass" '
            f'data-zh="通过率"></span></b> <span class="v">{pr_pct}%</span></span>'
            f'    <span class="run-metric"><b><span class="i18n" data-en="time" '
            f'data-zh="耗时"></span></b> <span class="v">{el_s}</span></span>'
            f'    <span class="run-metric"><b>tokens</b> <span class="v">{tok_s}</span></span>'
            f'  </div>'
            f'  {rbc_html}'
            f'</div>'
        )
    return "\n".join(blocks) or f'<p class="dim">{i18n("none")}</p>'


def render_test_log_editorial(vd: VerdictData) -> str:
    """Compact test log — one run entry per line, suitable for a log fold."""
    if not vd.runs:
        return f'<p class="dim">{i18n("none")}</p>'
    return render_run_cards_editorial(vd)


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


def _layer_for(vd: VerdictData) -> tuple[str, bool]:
    """Return (effective_layer, was_inferred). Reads `layer:` from
    repo.yaml first, falls back to the archetype-driven default."""

    declared = layers_mod.normalise_layer(vd.repo.get("layer"))
    if declared != "unknown":
        return declared, False
    inferred = layers_mod.default_layer_for_archetype(vd.archetype)
    return inferred, True


def render_layer_pill(vd: VerdictData) -> str:
    """A small bilingual pill that lives in the hero, next to the bucket."""

    layer, _ = _layer_for(vd)
    if layer == "unknown":
        return ""
    label = layers_mod.layer_label(layer)
    return (
        f'<span class="layer-pill layer-{layer}" title="{html.escape(layer)}">'
        f'<span class="layer-pill-eyebrow i18n" data-en="layer" data-zh="层级"></span>'
        f'{dual_lang(label)}'
        f'</span>'
    )


_LAYER_LEVEL_HEADINGS = {
    "atom":     {"en": "Atom-level checks",     "zh": "原子层检查"},
    "molecule": {"en": "Molecule-level checks", "zh": "分子层检查"},
    "compound": {"en": "Compound-level checks", "zh": "复合物层检查"},
}


def render_layer_section(vd: VerdictData) -> str:
    """Editorial 'how we evaluated this repo by layer' section.

    Renders:
      - A header naming the layer in en + zh (Atom/Molecule/Compound /
        原子/分子/复合物).
      - One sub-block per applicable level. Higher layers stack the
        lower-level blocks too — a compound shows atom + molecule +
        compound dimension tables.
      - For compound layers: a list of scenario experiments the
        operator runs by hand (system prompt + watch-for + verdict
        log location), bilingual.

    Empty section if the repo has no layer and no archetype default.
    """

    layer, was_inferred = _layer_for(vd)
    if layer == "unknown":
        return ""

    levels = layers_mod.applicable_levels(layer)
    label = layers_mod.layer_label(layer)
    summary = layers_mod.layer_summary(layer)

    declared_note_en = (
        f"Inferred from archetype <code>{html.escape(vd.archetype)}</code>"
        if was_inferred
        else "Declared in repo.yaml"
    )
    declared_note_zh = (
        f"由 archetype <code>{html.escape(vd.archetype)}</code> 推断而来"
        if was_inferred
        else "已在 repo.yaml 中显式声明"
    )

    # Header / hero strip for the section.
    header = f"""
    <div class="layer-hero">
      <div class="layer-hero-eyebrow">
        <span class="i18n" data-en="Composition layer" data-zh="组合层级"></span>
      </div>
      <div class="layer-hero-name layer-{layer}">{dual_lang(label)}</div>
      <div class="layer-hero-summary">{dual_lang(summary)}</div>
      <div class="layer-hero-source"><span class="i18n"
        data-en="{html.escape(declared_note_en, quote=True)}"
        data-zh="{html.escape(declared_note_zh, quote=True)}"></span></div>
    </div>
    """

    # One sub-card per applicable level.
    level_cards: list[str] = []
    for level in levels:
        applies = (
            {"en": "applies (this layer)", "zh": "适用（当前层）"}
            if level == layer
            else {"en": "applies (lower-level dependency)", "zh": "适用（下层依赖）"}
        )
        rows = "".join(
            f'<tr>'
            f'<th><code>{html.escape(d.key)}</code></th>'
            f'<td>{dual_lang(d.question)}</td>'
            f'</tr>'
            for d in layers_mod.dimensions_for_level(level)
        )
        level_cards.append(
            f'<div class="layer-card layer-card-{level}">'
            f'<div class="layer-card-head">'
            f'<h3>{dual_lang(_LAYER_LEVEL_HEADINGS[level])}</h3>'
            f'<span class="layer-card-tag">{dual_lang(applies)}</span>'
            f'</div>'
            f'<p class="layer-card-summary">{dual_lang(layers_mod.layer_summary(level))}</p>'
            f'<table class="layer-dim-table"><tbody>{rows}</tbody></table>'
            f'</div>'
        )

    # Compound experiments — only for compound layer.
    experiments_html = ""
    if layer == "compound":
        experiments = layers_mod.experiments_for(layer, vd.archetype)
        if experiments:
            cards: list[str] = []
            for idx, exp in enumerate(experiments, start=1):
                watch_items = "".join(
                    f"<li>{dual_lang(item)}</li>" for item in exp.watch_for
                )
                scenario_label = {
                    "en": f"Scenario {idx}",
                    "zh": f"场景 {idx}",
                }
                cards.append(
                    f'<div class="layer-experiment">'
                    f'<div class="layer-experiment-head">'
                    f'<span class="layer-experiment-num">{dual_lang(scenario_label)}</span>'
                    f'<h4>{dual_lang(exp.title)}</h4>'
                    f'</div>'
                    f'<div class="layer-experiment-label"><span class="i18n" '
                    f'data-en="System prompt" data-zh="System prompt（起手提示）"></span></div>'
                    f'<blockquote class="layer-experiment-prompt">'
                    f'{dual_lang(exp.system_prompt)}</blockquote>'
                    f'<div class="layer-experiment-label"><span class="i18n" '
                    f'data-en="What to watch for" data-zh="观察要点"></span></div>'
                    f'<ul class="layer-experiment-watch">{watch_items}</ul>'
                    f'<div class="layer-experiment-meta">'
                    f'<span class="i18n" data-en="Sub-skills expected: " '
                    f'data-zh="预期触发的子技能："></span>'
                    f'{dual_lang(exp.expected_sub_molecules)}'
                    f'</div>'
                    f'</div>'
                )
            experiments_html = (
                '<div class="layer-experiments">'
                '<div class="layer-experiments-eyebrow">'
                '<span class="i18n" data-en="Compound experiments — human-driven" '
                'data-zh="复合物实验 — 人驱动"></span>'
                '</div>'
                '<p class="layer-experiments-intro">'
                '<span class="i18n" '
                'data-en="The call graph is decided at runtime, so compound eval is scenario-driven. '
                'Run each scenario, observe the behaviour, log a verdict in '
                'runs/&lt;date&gt;/run-&lt;slug&gt;/business-notes.md." '
                'data-zh="复合物的调用图是运行时决定的，所以评测是场景驱动。'
                '逐个场景跑下来，观察行为，把判断记到 runs/&lt;date&gt;/run-&lt;slug&gt;/business-notes.md。"></span>'
                '</p>'
                + "".join(cards)
                + '</div>'
            )

    return (
        header
        + '<div class="layer-stack">'
        + "".join(level_cards)
        + '</div>'
        + experiments_html
    )


def render_score_block(vd: VerdictData) -> str:
    """Big-number score + emoji + bilingual tier label + blurb."""

    score = vd.verdict_input.get("score")
    if score is None:
        return ""  # legacy verdict-input without score field
    tier_emoji = vd.verdict_input.get("tier_emoji", "")
    tier_en = _esc(vd.verdict_input.get("tier_en", ""))
    tier_zh = _esc(vd.verdict_input.get("tier_zh", ""))
    blurb_en = _esc(vd.verdict_input.get("tier_blurb_en", ""))
    blurb_zh = _esc(vd.verdict_input.get("tier_blurb_zh", ""))
    tier_key = vd.verdict_input.get("tier_key", "unknown")

    return (
        f'<div class="score-hero tier-{tier_key}">'
        f'<div class="score-hero-row">'
        f'<span class="score-emoji">{tier_emoji}</span>'
        f'<span class="score-num">{int(score)}</span>'
        f'<span class="score-denom">/ 100</span>'
        f'</div>'
        f'<div class="score-tier">'
        f'<span class="i18n" data-en="{tier_en}" data-zh="{tier_zh}"></span>'
        f'</div>'
        f'<p class="score-blurb">'
        f'<span class="i18n" data-en="{blurb_en}" data-zh="{blurb_zh}"></span>'
        f'</p>'
        f'</div>'
    )


def render_score_breakdown(vd: VerdictData) -> str:
    """Collapsible breakdown so readers can audit each point."""

    bd = vd.verdict_input.get("score_breakdown")
    if not bd:
        return ""

    rows: list[str] = []
    for label_key, value in bd.items():
        label_en = {
            "base": "Base",
            "static_eval": "Static eval (claims)",
            "maintainer_evidence": "Maintainer evidence",
            "ecosystem": "Ecosystem (stars)",
            "layer_bonus": "Layer bonus",
            "penalties": "Penalties",
        }.get(label_key, label_key)
        label_zh = {
            "base": "基础分",
            "static_eval": "静态评测（claim）",
            "maintainer_evidence": "维护者证据",
            "ecosystem": "生态（stars）",
            "layer_bonus": "分层加分",
            "penalties": "罚分",
        }.get(label_key, label_key)
        sign = "+" if value > 0 else ""
        rows.append(
            f'<tr><th><span class="i18n" data-en="{label_en}" data-zh="{label_zh}"></span></th>'
            f'<td class="num">{sign}{int(value)}</td></tr>'
        )
    return (
        '<details class="score-breakdown">'
        '<summary><span class="i18n" data-en="How the score was computed" '
        'data-zh="分数是怎么算的"></span></summary>'
        '<table class="breakdown-table"><tbody>'
        + "".join(rows) +
        '</tbody></table></details>'
    )


def render_scenarios(vd: VerdictData) -> str:
    """Render the ✅ use_for / ❌ dont_use_for lists from product_view."""

    pv = vd.repo.get("product_view") or {}
    use_for = pv.get("use_for") or []
    dont_use_for = pv.get("dont_use_for") or []
    if not use_for and not dont_use_for:
        return ""

    items: list[str] = []
    for s in use_for:
        items.append(
            f'<li class="scenario scenario-yes">'
            f'<span class="scenario-mark">✅</span>{dual_lang(s)}</li>'
        )
    for s in dont_use_for:
        items.append(
            f'<li class="scenario scenario-no">'
            f'<span class="scenario-mark">❌</span>{dual_lang(s)}</li>'
        )
    return (
        '<section class="scenarios-section">'
        '<div class="section-head">'
        '<h2><span class="i18n" data-en="Use it for / Don\'t use it for" '
        'data-zh="什么时候用 / 什么时候别用"></span></h2></div>'
        f'<ul class="scenarios">{"".join(items)}</ul>'
        '</section>'
    )


def render_deployment_section(vd: VerdictData) -> str:
    """Prominent dossier section: deployment status + third-party services.

    Two cards:
      1. **Deploy** — Can you install? How? Online needed? Compile needed?
      2. **Third-party services** — what API keys / signups / costs are
         actually required to use the repo, with traffic-light status
         per service.

    Renders nothing if neither field is populated in repo.yaml.
    """

    deployment = vd.repo.get("deployment") or {}
    services = vd.repo.get("third_party_services") or []
    if not deployment and not services:
        return ""

    # --- Deployment card ----
    deploy_html = ""
    if deployment:
        installable = deployment.get("installable", False)
        install_status = (
            ('<span class="deploy-status status-good">'
             '<span class="i18n" data-en="✅ Installable now" '
             'data-zh="✅ 现在就能装"></span></span>')
            if installable
            else ('<span class="deploy-status status-bad">'
                  '<span class="i18n" data-en="❌ Not directly installable" '
                  'data-zh="❌ 不能直接安装"></span></span>')
        )

        methods = deployment.get("install_methods") or []
        methods_rows: list[str] = []
        for m in methods:
            method_name = _esc(m.get("method", ""))
            platform = _esc(m.get("platform", ""))
            complexity = m.get("complexity", "")
            paid = m.get("paid", False)
            internal = m.get("internal", False)
            no_install = m.get("no_install", False)
            badges = []
            if complexity:
                cls = {"easy": "complexity-easy", "moderate": "complexity-moderate",
                       "hard": "complexity-hard"}.get(complexity, "")
                badges.append(f'<span class="badge {cls}">{_esc(complexity)}</span>')
            if paid:
                badges.append('<span class="badge complexity-hard"><span class="i18n" data-en="paid" data-zh="付费"></span></span>')
            if internal:
                badges.append('<span class="badge"><span class="i18n" data-en="internal" data-zh="内部用法"></span></span>')
            if no_install:
                badges.append('<span class="badge complexity-easy"><span class="i18n" data-en="no install" data-zh="免安装"></span></span>')
            methods_rows.append(
                f'<tr><td><code>{method_name}</code></td>'
                f'<td>{platform}</td>'
                f'<td>{" ".join(badges)}</td></tr>'
            )

        flags: list[str] = []
        if deployment.get("requires_compile"):
            flags.append(
                '<li><span class="flag-icon">🛠</span><span class="i18n" '
                'data-en="Requires compile / build step" '
                'data-zh="需要编译 / build 步骤"></span></li>'
            )
        if deployment.get("works_offline_after_install"):
            flags.append(
                '<li><span class="flag-icon">📡</span><span class="i18n" '
                'data-en="Works offline after install" '
                'data-zh="装完之后可离线运行"></span></li>'
            )
        else:
            flags.append(
                '<li><span class="flag-icon">🌐</span><span class="i18n" '
                'data-en="Needs network at runtime" '
                'data-zh="运行时需要网络"></span></li>'
            )
        if deployment.get("auto_update"):
            flags.append(
                '<li><span class="flag-icon">🔄</span><span class="i18n" '
                'data-en="Auto-updates by default" '
                'data-zh="默认自动更新"></span></li>'
            )
        if deployment.get("private_npm"):
            flags.append(
                '<li><span class="flag-icon">🔒</span><span class="i18n" '
                'data-en="Private npm package — not on registry" '
                'data-zh="私有 npm 包 —— 不在公开 registry 上"></span></li>'
            )
        if deployment.get("windows_unsupported"):
            flags.append(
                '<li><span class="flag-icon">⚠️</span><span class="i18n" '
                'data-en="Windows not supported" '
                'data-zh="不支持 Windows"></span></li>'
            )
        warn = deployment.get("default_password_warning")
        if warn:
            flags.append(
                f'<li><span class="flag-icon">🚨</span>{_esc(warn)}</li>'
            )

        deploy_html = (
            '<div class="deploy-card">'
            '<div class="card-eyebrow"><span class="i18n" '
            'data-en="Can I deploy this?" data-zh="能不能装上跑？"></span></div>'
            f'<div class="card-headline">{install_status}</div>'
            + (
                '<table class="install-table">'
                '<thead><tr>'
                '<th><span class="i18n" data-en="Install method" data-zh="安装方式"></span></th>'
                '<th><span class="i18n" data-en="Platform" data-zh="平台"></span></th>'
                '<th><span class="i18n" data-en="Difficulty" data-zh="复杂度"></span></th>'
                '</tr></thead>'
                f'<tbody>{"".join(methods_rows)}</tbody>'
                '</table>' if methods_rows else ''
            )
            + (
                f'<ul class="deploy-flags">{"".join(flags)}</ul>'
                if flags else ''
            )
            + '</div>'
        )

    # --- Third-party services card ----
    services_html = ""
    if services:
        rows: list[str] = []
        for s in services:
            name = _esc(s.get("name", ""))
            purpose = _esc(s.get("purpose", ""))
            required = s.get("required", False)
            api_key = s.get("api_key_needed", False)
            signup = s.get("signup_needed", False)
            free_tier = s.get("free_tier", False)
            cost_note = _esc(s.get("cost_note", ""))

            # Status pills (each clickable when any policy fails)
            req_class = "status-must" if required else "status-opt"
            req_label_en = "Required" if required else "Optional"
            req_label_zh = "必需" if required else "可选"

            # Cost ladder: free + no signup = green; signup needed = yellow;
            # paid api key needed = orange.
            if api_key and not free_tier:
                cost_class, cost_en, cost_zh = "status-paid", "💰 Paid API key", "💰 需付费 API key"
            elif api_key and free_tier:
                cost_class, cost_en, cost_zh = "status-free", "🆓 Free tier API key", "🆓 免费版 API key"
            elif signup:
                cost_class, cost_en, cost_zh = "status-signup", "📝 Signup needed", "📝 需要注册账号"
            else:
                cost_class, cost_en, cost_zh = "status-easy", "🟢 Just install", "🟢 装上就能用"

            rows.append(
                f'<div class="service-card">'
                f'<div class="service-head">'
                f'<div>'
                f'<div class="service-name">{name}</div>'
                f'<div class="service-purpose">{purpose}</div>'
                f'</div>'
                f'<div class="service-pills">'
                f'<span class="service-pill {req_class}">'
                f'<span class="i18n" data-en="{req_label_en}" data-zh="{req_label_zh}"></span></span>'
                f'<span class="service-pill {cost_class}">'
                f'<span class="i18n" data-en="{cost_en}" data-zh="{cost_zh}"></span></span>'
                f'</div>'
                f'</div>'
                + (f'<div class="service-cost"><span class="i18n" '
                   f'data-en="Cost note: " data-zh="成本说明："></span>'
                   f'{cost_note}</div>' if cost_note else '')
                + '</div>'
            )

        services_html = (
            '<div class="services-card">'
            '<div class="card-eyebrow"><span class="i18n" '
            'data-en="Third-party services it touches" '
            'data-zh="会用到哪些第三方服务"></span></div>'
            + "".join(rows) +
            '</div>'
        )

    if not deploy_html and not services_html:
        return ""

    return (
        '<section class="deployment-section">'
        '<div class="section-head">'
        '<h2><span class="i18n" '
        'data-en="Deploy &amp; cost" '
        'data-zh="部署与成本"></span></h2></div>'
        '<div class="deploy-grid">'
        f'{deploy_html}{services_html}'
        '</div>'
        '</section>'
    )


def render_html(vd: VerdictData, initial_lang: str = "auto") -> str:
    """Editorial dossier template — dark warm palette, zero external
    dependencies (no Chart.js, Mermaid, or Google Fonts), bucket-driven
    accent color via ``<html data-bucket=...>``."""
    bucket = vd.bucket
    inputs = vd.verdict_input.get("inputs_summary") or {}
    confidence = _esc(vd.verdict_input.get("confidence") or "unknown")
    ceilings = vd.verdict_input.get("ceiling_reasons") or []
    blocking = vd.verdict_input.get("blocking_issues") or []

    ceilings_html = "".join(f"<li>{_esc(r)}</li>" for r in ceilings) \
        or f'<li class="dim">{i18n("none")}</li>'
    blocking_html = "".join(f"<li>{_esc(b)}</li>" for b in blocking) \
        or f'<li class="dim">{i18n("none")}</li>'

    # Product-facing pieces
    product_one_liner_html = product_one_liner(vd)
    capability_cards_html = render_capability_cards(vd)
    best_for_html = render_best_for(vd)
    watch_out_html = render_watch_out(vd)

    # Editorial pieces
    status_counts = count_claim_statuses(vd)
    total_claims = sum(status_counts.values())
    covered = total_claims - status_counts.get("untested", 0)
    stats_bar_html = render_stats_bar(status_counts)
    stats_legend_html = render_stats_legend(status_counts)
    flow_html = render_derivation_flow(vd)
    metric_tiles_html = render_metric_tiles(vd)
    claim_ledger_html = render_claim_ledger(vd)
    run_cards_html = render_run_cards_editorial(vd)
    test_log_html = render_test_log_editorial(vd)
    layer_section_html = render_layer_section(vd)
    layer_pill_html = render_layer_pill(vd)
    score_block_html = render_score_block(vd)
    score_breakdown_html = render_score_breakdown(vd)
    scenarios_html = render_scenarios(vd)
    deployment_html = render_deployment_section(vd)

    verdict_md_escaped = _esc(vd.verdict_md)

    # Version chip — from repo.yaml if the evaluator recorded one.
    version_tested = vd.repo.get("version_tested") or ""
    version_chip = (
        f'<span class="sep">·</span><span>{_esc(version_tested)}</span>'
        if version_tested else ""
    )
    repo_url = vd.repo.get("repo_url") or f"https://github.com/{vd.owner_repo}"

    # Pre-paint lang attribute: avoids the "flash of wrong language" when
    # the CLI caller pre-picks a language. "auto" still works but will
    # flip to the correct one as soon as the <script> runs.
    server_lang = initial_lang if initial_lang in ("en", "zh") else "en"

    return f"""<!DOCTYPE html>
<html lang="{server_lang}" data-bucket="{bucket}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(vd.display_name)} — verdict · repo-evals</title>
<style>
/* ============================================================
   REPO-EVALS VERDICT PAGE — Editorial Dossier style
   Pure HTML + CSS, zero external dependencies, zero JS frameworks.
   One small inline <script> at the bottom handles language toggle.
   ============================================================ */

/* ---------- Design tokens ---------- */
:root {{
  --font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
               "Segoe UI", "PingFang SC", "Hiragino Sans GB",
               "Microsoft YaHei", Helvetica, Arial, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
               "Liberation Mono", "Courier New", monospace;

  --bg:            #0a0908;
  --surface-0:     #141210;
  --surface-1:     #1c1a17;
  --surface-2:     #26231f;
  --border:        rgba(255, 248, 235, 0.07);
  --border-strong: rgba(255, 248, 235, 0.16);

  --text:   #f5efe6;
  --text-2: #a6998a;
  --text-3: #6b6157;

  --bucket:      #f59e0b;
  --bucket-bg:   rgba(245, 158, 11, 0.10);
  --bucket-soft: rgba(245, 158, 11, 0.16);

  --ok:      #4ade80;
  --ok-bg:   rgba(74, 222, 128, 0.10);
  --warn:    #fbbf24;
  --warn-bg: rgba(251, 191, 36, 0.10);
  --bad:     #f87171;
  --bad-bg:  rgba(248, 113, 113, 0.10);
  --skip:    #a6998a;
  --skip-bg: rgba(166, 153, 138, 0.08);

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 14px;
}}

html[data-bucket="usable"]        {{ --bucket:#f59e0b; --bucket-bg:rgba(245,158,11,.10); --bucket-soft:rgba(245,158,11,.16); }}
html[data-bucket="reusable"]      {{ --bucket:#60a5fa; --bucket-bg:rgba(96,165,250,.10); --bucket-soft:rgba(96,165,250,.16); }}
html[data-bucket="recommendable"] {{ --bucket:#4ade80; --bucket-bg:rgba(74,222,128,.10); --bucket-soft:rgba(74,222,128,.16); }}
html[data-bucket="unusable"]      {{ --bucket:#f87171; --bucket-bg:rgba(248,113,113,.10); --bucket-soft:rgba(248,113,113,.16); }}

* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  font-family: var(--font-sans);
  background: var(--bg);
  color: var(--text);
  font-size: 16px;
  line-height: 1.6;
  font-feature-settings: "ss01", "cv11", "tnum";
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
}}

body::before {{
  content: "";
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 1200px 800px at 70% -10%, var(--bucket-bg), transparent 60%),
    radial-gradient(ellipse 900px 600px at 0% 100%, rgba(255,248,235,0.025), transparent 60%);
  pointer-events: none;
  z-index: 0;
}}

main {{ position: relative; z-index: 1; max-width: 1180px; margin: 0 auto; padding: 0 32px 120px; }}

.topbar {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 24px 0 48px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-3);
  text-transform: uppercase;
  letter-spacing: 0.14em;
}}
.wordmark {{ color: var(--text-2); font-weight: 600; }}
.wordmark .dot {{ color: var(--bucket); }}

.lang-toggle {{ display: inline-flex; gap: 2px; background: var(--surface-1); border: 1px solid var(--border); border-radius: 999px; padding: 3px; }}
.lang-toggle button {{
  background: transparent; border: 0; cursor: pointer;
  font-family: var(--font-mono); font-size: 10px; font-weight: 600;
  color: var(--text-3); padding: 5px 12px; border-radius: 999px;
  letter-spacing: 0.12em; text-transform: uppercase;
  transition: color 0.15s, background 0.15s;
}}
.lang-toggle button:hover {{ color: var(--text); }}
html[lang="en"] .lang-toggle button[data-lang="en"],
html[lang="zh"] .lang-toggle button[data-lang="zh"] {{
  background: var(--text); color: var(--bg);
}}

.hero {{ padding: 24px 0 72px; border-bottom: 1px solid var(--border); margin-bottom: 72px; }}

.eyebrow {{
  font-family: var(--font-mono); font-size: 11px;
  color: var(--text-3); text-transform: uppercase;
  letter-spacing: 0.16em; margin-bottom: 32px;
  display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
}}
.eyebrow .sep {{ color: var(--border-strong); }}

h1.repo-title {{
  font-size: clamp(40px, 6vw, 68px);
  font-weight: 800;
  letter-spacing: -0.035em;
  line-height: 0.98;
  margin: 0 0 14px;
  color: var(--text);
}}
.repo-slug {{
  font-family: var(--font-mono); font-size: 14px;
  color: var(--text-2); margin-bottom: 36px;
}}
.repo-slug::before {{ content: "↳ "; color: var(--text-3); }}

.tagline {{
  font-size: clamp(18px, 2vw, 22px);
  line-height: 1.45; font-weight: 400;
  color: var(--text); max-width: 62ch;
  margin: 0 0 72px;
}}

.verdict-block {{ display: grid; grid-template-columns: auto 1fr; gap: 64px; align-items: end; }}
@media (max-width: 720px) {{ .verdict-block {{ grid-template-columns: 1fr; gap: 40px; }} }}

.verdict-word {{
  font-size: clamp(80px, 14vw, 168px);
  font-weight: 800;
  letter-spacing: -0.055em;
  line-height: 0.85;
  color: var(--bucket);
  text-transform: lowercase;
  margin: 0;
  position: relative;
  padding-right: 0.1em;
}}
.verdict-word::after {{
  content: "";
  display: inline-block;
  width: 0.18em; height: 0.18em;
  background: var(--bucket);
  border-radius: 50%;
  margin-left: 0.08em;
  margin-bottom: 0.08em;
  vertical-align: baseline;
}}

.verdict-meta {{ padding-bottom: 14px; }}
.verdict-meta .label {{
  font-family: var(--font-mono); font-size: 11px;
  color: var(--text-3); text-transform: uppercase;
  letter-spacing: 0.14em; margin-bottom: 10px;
}}
.verdict-meta .confidence {{
  font-family: var(--font-mono); font-size: 15px;
  color: var(--text); margin-bottom: 28px;
  text-transform: uppercase; letter-spacing: 0.08em;
}}
.verdict-meta .confidence .value {{ color: var(--bucket); font-weight: 700; }}

/* --- 0-100 score hero ----------------------------------------------- */

.score-hero {{ margin: 0; }}
.score-hero-row {{
  display: flex; align-items: baseline; gap: 16px;
  flex-wrap: wrap;
}}
.score-emoji {{ font-size: 60px; line-height: 1; }}
.score-num {{
  font-family: var(--font-display, var(--font-sans));
  font-size: clamp(80px, 12vw, 144px); font-weight: 800;
  letter-spacing: -0.04em; line-height: 0.85;
}}
.score-denom {{
  font-family: var(--font-mono); font-size: 16px;
  color: var(--text-3); letter-spacing: 0.04em;
}}
.score-tier {{
  font-family: var(--font-display, var(--font-serif));
  font-size: clamp(28px, 4vw, 40px); font-weight: 700;
  margin-top: 4px;
}}
.score-blurb {{
  margin: 14px 0 0; max-width: 60ch;
  color: var(--text-2); font-size: 16px; line-height: 1.55;
}}

/* tier-driven accent — overrides --bucket */
.score-hero.tier-recommend  .score-num {{ color: #4ade80; }}
.score-hero.tier-team       .score-num {{ color: #60a5fa; }}
.score-hero.tier-self       .score-num {{ color: #c084fc; }}
.score-hero.tier-try        .score-num {{ color: #f59e0b; }}
.score-hero.tier-risky      .score-num {{ color: #f87171; }}
.score-hero.tier-broken     .score-num {{ color: #f87171; }}

/* --- score breakdown (collapsible) ---------------------------------- */

details.score-breakdown {{
  margin-top: 22px; border: 1px solid var(--border);
  border-radius: 10px; padding: 0;
}}
details.score-breakdown > summary {{
  list-style: none; cursor: pointer;
  padding: 10px 14px; font-family: var(--font-mono);
  font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.12em; color: var(--text-3);
}}
details.score-breakdown > summary::-webkit-details-marker {{ display: none; }}
details.score-breakdown > summary::after {{
  content: "+"; float: right; font-weight: 700;
}}
details.score-breakdown[open] > summary::after {{ content: "−"; }}
.breakdown-table {{ width: 100%; border-collapse: collapse; }}
.breakdown-table th, .breakdown-table td {{
  padding: 8px 14px; border-top: 1px solid var(--border);
  font-size: 13px; text-align: left;
}}
.breakdown-table th {{ font-weight: 500; color: var(--text-2); width: 60%; }}
.breakdown-table td.num {{
  text-align: right; font-family: var(--font-mono);
  font-variant-numeric: tabular-nums; color: var(--text);
}}

/* --- ✅ / ❌ scenarios section -------------------------------------- */

.scenarios-section {{ margin: 24px 0 56px; }}
.scenarios {{
  list-style: none; padding: 0; margin: 12px 0 0;
  display: grid; gap: 10px;
}}
.scenario {{
  display: flex; gap: 12px; padding: 12px 16px;
  border: 1px solid var(--border); border-radius: 10px;
  background: var(--surface-1); align-items: baseline;
  font-size: 15px; line-height: 1.55;
}}
.scenario-mark {{ font-size: 18px; flex-shrink: 0; }}
.scenario-yes {{ border-left: 3px solid #4ade80; }}
.scenario-no  {{ border-left: 3px solid #f87171; color: var(--text-2); }}

/* --- Deployment + 3rd-party services section ------------------------ */

.deployment-section {{ margin: 24px 0 48px; }}
.deploy-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  margin-top: 12px;
}}
@media (max-width: 720px) {{ .deploy-grid {{ grid-template-columns: 1fr; }} }}

.deploy-card, .services-card {{
  background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px 22px;
}}
.card-eyebrow {{
  font-family: var(--font-mono); font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.12em;
  color: var(--text-3); margin-bottom: 10px;
}}
.card-headline {{ margin-bottom: 14px; }}

.deploy-status {{
  font-family: var(--font-display, var(--font-serif));
  font-size: 18px; font-weight: 700;
}}
.deploy-status.status-good {{ color: #4ade80; }}
.deploy-status.status-bad {{ color: #f87171; }}

.install-table {{
  width: 100%; border-collapse: collapse; margin-top: 6px; margin-bottom: 14px;
}}
.install-table th, .install-table td {{
  padding: 8px 10px; border-top: 1px solid var(--border);
  text-align: left; vertical-align: top; font-size: 13px;
}}
.install-table th {{
  font-family: var(--font-mono); font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--text-3); font-weight: 600;
}}
.install-table td code {{ font-size: 12px; word-break: break-word; }}

.install-table .badge {{
  display: inline-block; padding: 1px 7px; border-radius: 4px;
  font-family: var(--font-mono); font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.06em;
  background: var(--surface-2); color: var(--text-2);
  border: 1px solid var(--border);
}}
.install-table .complexity-easy {{ color: #4ade80; border-color: rgba(74,222,128,.3); }}
.install-table .complexity-moderate {{ color: #f59e0b; border-color: rgba(245,158,11,.3); }}
.install-table .complexity-hard {{ color: #f87171; border-color: rgba(248,113,113,.3); }}

.deploy-flags {{ list-style: none; padding: 0; margin: 8px 0 0; }}
.deploy-flags li {{
  padding: 6px 0; font-size: 13px; color: var(--text-2);
  display: flex; gap: 10px; align-items: baseline;
}}
.flag-icon {{ flex-shrink: 0; }}

.service-card {{
  border: 1px solid var(--border); border-radius: 8px;
  padding: 12px 14px; margin-bottom: 10px;
  background: var(--surface-2);
}}
.service-card:last-child {{ margin-bottom: 0; }}
.service-head {{
  display: flex; justify-content: space-between;
  gap: 12px; align-items: flex-start;
}}
.service-name {{ font-weight: 600; color: var(--text); font-size: 14px; }}
.service-purpose {{
  font-size: 12px; color: var(--text-2);
  margin-top: 2px; line-height: 1.45;
}}
.service-pills {{
  display: flex; flex-direction: column;
  gap: 4px; flex-shrink: 0; align-items: flex-end;
}}
.service-pill {{
  display: inline-block; padding: 2px 8px; border-radius: 999px;
  font-family: var(--font-mono); font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.06em;
  white-space: nowrap;
}}
.service-pill.status-must  {{ background: rgba(248,113,113,.14); color: #f87171; }}
.service-pill.status-opt   {{ background: var(--surface-1); color: var(--text-3); }}
.service-pill.status-paid  {{ background: rgba(245,158,11,.14); color: #f59e0b; }}
.service-pill.status-free  {{ background: rgba(96,165,250,.14); color: #60a5fa; }}
.service-pill.status-signup {{ background: rgba(192,132,252,.14); color: #c084fc; }}
.service-pill.status-easy  {{ background: rgba(74,222,128,.14); color: #4ade80; }}

.service-cost {{
  margin-top: 8px; padding-top: 8px;
  border-top: 1px dashed var(--border);
  font-size: 12px; color: var(--text-2); line-height: 1.5;
}}

.stats-bar {{
  display: flex; height: 10px; border-radius: 999px;
  overflow: hidden; background: var(--surface-1);
  border: 1px solid var(--border);
  min-width: 280px; max-width: 420px;
}}
.stats-bar span {{ display: block; height: 100%; }}
.stats-bar .s-pass {{ background: var(--ok); }}
.stats-bar .s-warn {{ background: var(--warn); }}
.stats-bar .s-bad  {{ background: var(--bad); }}
.stats-bar .s-skip {{ background: var(--skip); }}

.stats-legend {{
  display: flex; gap: 20px; margin-top: 14px;
  font-family: var(--font-mono); font-size: 12px;
  color: var(--text-2); flex-wrap: wrap;
}}
.stats-legend .item {{ display: inline-flex; align-items: center; gap: 6px; }}
.stats-legend .dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
.stats-legend .num {{ color: var(--text); font-weight: 700; }}

.pull-quotes {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 96px; }}
@media (max-width: 720px) {{ .pull-quotes {{ grid-template-columns: 1fr; }} }}

.pull {{
  padding: 28px 32px;
  background: var(--surface-0);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  border-top: 3px solid;
  position: relative;
}}
.pull.best   {{ border-top-color: var(--ok); }}
.pull.watch  {{ border-top-color: var(--warn); }}
.pull .kicker {{
  font-family: var(--font-mono); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.14em;
  margin-bottom: 14px; font-weight: 700;
}}
.pull.best .kicker  {{ color: var(--ok); }}
.pull.watch .kicker {{ color: var(--warn); }}
.pull .body {{ font-size: 16px; line-height: 1.55; color: var(--text); }}

.section-head {{
  display: flex; align-items: baseline; gap: 16px;
  margin-bottom: 36px; padding-bottom: 18px;
  border-bottom: 1px solid var(--border);
}}
.section-head h2 {{
  font-size: 32px; font-weight: 700;
  letter-spacing: -0.022em; margin: 0;
}}
.section-head .count {{
  font-family: var(--font-mono); font-size: 12px;
  color: var(--text-3); letter-spacing: 0.08em;
  text-transform: uppercase;
}}
section {{ margin-bottom: 96px; }}

.capabilities-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 16px;
}}

.capability-card {{
  position: relative;
  background: var(--surface-0);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px 24px 24px 28px;
  display: flex; flex-direction: column; gap: 12px;
  transition: transform 0.2s ease, border-color 0.2s ease;
  overflow: hidden;
}}
.capability-card:hover {{ transform: translateY(-2px); border-color: var(--border-strong); }}

.capability-card::before {{
  content: ""; position: absolute;
  left: 0; top: 0; bottom: 0; width: 4px;
  background: var(--skip);
}}
.capability-card.status-passed::before,
.capability-card.status-passed_with_concerns::before {{ background: var(--ok); }}
.capability-card.status-partial::before {{ background: var(--warn); }}
.capability-card.status-failed::before,
.capability-card.status-failed_partial::before {{ background: var(--bad); }}
.capability-card.status-untested::before {{ background: var(--skip); }}

.cap-header {{
  display: flex; align-items: center; gap: 10px;
  font-family: var(--font-mono); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.1em;
}}
.cap-badge {{
  padding: 3px 9px; border-radius: var(--radius-sm);
  font-weight: 700; font-size: 10px;
  background: var(--skip-bg); color: var(--skip);
}}
.capability-card.status-passed .cap-badge,
.capability-card.status-passed_with_concerns .cap-badge {{ background: var(--ok-bg); color: var(--ok); }}
.capability-card.status-partial .cap-badge {{ background: var(--warn-bg); color: var(--warn); }}
.capability-card.status-failed .cap-badge,
.capability-card.status-failed_partial .cap-badge {{ background: var(--bad-bg); color: var(--bad); }}
.capability-card.status-untested .cap-badge {{ background: var(--skip-bg); color: var(--skip); }}

.cap-id {{ margin-left: auto; color: var(--text-3); }}

.cap-title {{
  font-size: 20px; font-weight: 700;
  letter-spacing: -0.015em; line-height: 1.25;
  color: var(--text); margin: 4px 0 0;
}}
.cap-description {{
  font-size: 14px; line-height: 1.55;
  color: var(--text-2); margin: 0;
}}
.cap-skip {{
  margin-top: 4px;
  font-size: 12.5px; color: var(--text-3);
  font-family: var(--font-mono); line-height: 1.55;
  padding: 10px 12px;
  background: var(--surface-1);
  border-radius: var(--radius-sm);
  border-left: 2px solid var(--border-strong);
  white-space: pre-wrap;
}}

details.section-fold {{
  background: var(--surface-0);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: 16px;
  overflow: hidden;
  transition: border-color 0.15s;
}}
details.section-fold[open] {{ border-color: var(--border-strong); }}
details.section-fold > summary {{
  padding: 22px 28px;
  cursor: pointer;
  font-family: var(--font-mono); font-size: 12px;
  color: var(--text-2);
  text-transform: uppercase; letter-spacing: 0.14em;
  font-weight: 600; user-select: none;
  list-style: none;
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
}}
details.section-fold > summary::-webkit-details-marker {{ display: none; }}
details.section-fold > summary::after {{
  content: "+"; font-family: var(--font-mono);
  font-size: 18px; color: var(--text-3);
  transition: transform 0.2s;
  display: inline-block; line-height: 1;
}}
details.section-fold[open] > summary::after {{ transform: rotate(45deg); color: var(--text); }}
details.section-fold > summary:hover {{ color: var(--text); background: var(--surface-1); }}
details.section-fold > .body {{ padding: 8px 28px 32px; border-top: 1px solid var(--border); }}

.subsection {{ margin: 28px 0; }}
.subsection h3 {{
  font-family: var(--font-mono); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.14em;
  color: var(--text-3); font-weight: 700;
  margin: 0 0 14px; padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}}
.grid-two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
@media (max-width: 720px) {{ .grid-two {{ grid-template-columns: 1fr; }} }}

.mini-card {{
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 18px 20px;
}}
.mini-card h4 {{
  font-family: var(--font-mono); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--text-3); margin: 0 0 12px; font-weight: 700;
}}
.mini-card ul {{ margin: 0; padding: 0; list-style: none; }}
.mini-card li {{
  padding: 8px 0; font-size: 14px; color: var(--text-2);
  border-bottom: 1px dashed var(--border);
  line-height: 1.5;
}}
.mini-card li:last-child {{ border-bottom: 0; padding-bottom: 0; }}
.mini-card li:first-child {{ padding-top: 0; }}

/* --- Layer (atom / molecule / compound) section -------------------- */

.layer-pill {{
  display: inline-flex; align-items: baseline; gap: 8px;
  padding: 4px 12px; border-radius: 999px;
  background: var(--surface-1); border: 1px solid var(--border-strong);
  font-family: var(--font-mono); font-size: 12px;
  margin-left: 12px;
}}
.layer-pill-eyebrow {{
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--text-3); font-size: 10px;
}}
.layer-pill.layer-atom     {{ border-color: #4a9d8a; color: #2d7866; }}
.layer-pill.layer-molecule {{ border-color: #7a5fb8; color: #5a3aa1; }}
.layer-pill.layer-compound {{ border-color: #c75441; color: #a13d30; }}

.layer-hero {{
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 24px 28px; margin-bottom: 22px;
}}
.layer-hero-eyebrow {{
  font-family: var(--font-mono); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.12em;
  color: var(--text-3); margin-bottom: 6px;
}}
.layer-hero-name {{
  font-family: var(--font-display, var(--font-serif));
  font-size: 32px; font-weight: 700; line-height: 1.1;
  margin-bottom: 10px;
}}
.layer-hero-name.layer-atom     {{ color: #2d7866; }}
.layer-hero-name.layer-molecule {{ color: #5a3aa1; }}
.layer-hero-name.layer-compound {{ color: #a13d30; }}
.layer-hero-summary {{ font-size: 16px; color: var(--text-2); line-height: 1.55; max-width: 70ch; }}
.layer-hero-source {{ margin-top: 10px; font-family: var(--font-mono); font-size: 12px; color: var(--text-3); }}

.layer-stack {{ display: grid; gap: 18px; margin-bottom: 28px; }}

.layer-card {{
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 20px 24px;
}}
.layer-card-head {{
  display: flex; align-items: baseline;
  justify-content: space-between; gap: 12px; flex-wrap: wrap;
  margin-bottom: 6px;
}}
.layer-card-head h3 {{
  margin: 0;
  font-family: var(--font-display, var(--font-serif));
  font-size: 18px; font-weight: 700;
}}
.layer-card-tag {{
  font-family: var(--font-mono); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--text-3); padding: 2px 8px;
  border: 1px solid var(--border); border-radius: 4px;
}}
.layer-card-summary {{ color: var(--text-2); margin: 4px 0 14px; line-height: 1.55; }}

.layer-card.layer-card-atom     {{ border-left: 3px solid #4a9d8a; }}
.layer-card.layer-card-molecule {{ border-left: 3px solid #7a5fb8; }}
.layer-card.layer-card-compound {{ border-left: 3px solid #c75441; }}

.layer-dim-table {{ width: 100%; border-collapse: collapse; }}
.layer-dim-table th, .layer-dim-table td {{
  text-align: left; padding: 10px 12px;
  border-top: 1px solid var(--border); vertical-align: top;
  font-size: 14px; line-height: 1.55;
}}
.layer-dim-table th {{
  width: 28%; font-weight: 600; color: var(--text);
}}
.layer-dim-table td {{ color: var(--text-2); }}
.layer-dim-table th code {{
  font-family: var(--font-mono); font-size: 12px;
  background: var(--surface-2); padding: 2px 6px; border-radius: 4px;
}}

.layer-experiments {{
  margin-top: 28px; padding-top: 22px;
  border-top: 1px dashed var(--border);
}}
.layer-experiments-eyebrow {{
  font-family: var(--font-mono); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.12em;
  color: var(--text-3); margin-bottom: 6px;
}}
.layer-experiments-intro {{
  color: var(--text-2); margin: 0 0 18px; max-width: 70ch; line-height: 1.55;
}}

.layer-experiment {{
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 18px 22px; margin-bottom: 14px;
}}
.layer-experiment-head {{
  display: flex; align-items: baseline; gap: 12px; margin-bottom: 10px;
}}
.layer-experiment-num {{
  font-family: var(--font-mono); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--text-3);
  padding: 2px 8px; border: 1px solid var(--border); border-radius: 4px;
}}
.layer-experiment h4 {{
  margin: 0; font-family: var(--font-display, var(--font-serif));
  font-size: 17px; font-weight: 700;
}}
.layer-experiment-label {{
  font-family: var(--font-mono); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--text-3); margin: 12px 0 6px;
}}
.layer-experiment-prompt {{
  margin: 0 0 4px; padding: 12px 16px;
  border-left: 3px solid var(--border-strong);
  background: var(--surface-2);
  font-family: var(--font-serif); font-size: 14px; font-style: italic;
  color: var(--text); line-height: 1.55;
}}
.layer-experiment-watch {{
  margin: 0 0 4px; padding: 0 0 0 18px;
}}
.layer-experiment-watch li {{ padding: 4px 0; color: var(--text-2); line-height: 1.5; }}
.layer-experiment-meta {{
  margin-top: 10px; font-family: var(--font-mono); font-size: 12px;
  color: var(--text-3);
}}

.flow {{
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 28px 24px;
  overflow-x: auto;
}}
.flow-row {{
  display: flex; align-items: center; gap: 12px;
  flex-wrap: wrap;
  font-family: var(--font-mono); font-size: 13px;
}}
.flow-node {{
  padding: 10px 16px; border-radius: var(--radius-sm);
  background: var(--surface-2); color: var(--text);
  border: 1px solid var(--border-strong);
  white-space: nowrap;
}}
.flow-node.start {{ color: var(--text-2); }}
.flow-node.decision {{ background: var(--warn-bg); color: var(--warn); border-color: var(--warn); }}
.flow-node.final {{ background: var(--bucket-bg); color: var(--bucket); border-color: var(--bucket); font-weight: 700; }}
.flow-arrow {{ color: var(--text-3); font-family: var(--font-mono); }}
.flow-notes {{ margin-top: 18px; padding-top: 18px; border-top: 1px dashed var(--border); }}
.flow-notes .note {{
  font-family: var(--font-mono); font-size: 12px;
  color: var(--text-3); padding: 4px 0; line-height: 1.5;
}}
.flow-notes .note::before {{
  content: "▸"; color: var(--warn);
  margin-right: 8px;
}}

.metric-tiles {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 24px; }}
@media (max-width: 640px) {{ .metric-tiles {{ grid-template-columns: 1fr; }} }}
.metric-tile {{
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 22px 20px;
}}
.metric-tile .mt-label {{
  font-family: var(--font-mono); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.12em;
  color: var(--text-3); margin-bottom: 14px;
}}
.metric-tile .mt-value {{
  font-size: 38px; font-weight: 800;
  letter-spacing: -0.025em; line-height: 1;
  color: var(--text); font-variant-numeric: tabular-nums;
}}
.metric-tile .mt-unit {{ font-size: 16px; color: var(--text-3); font-weight: 500; margin-left: 4px; }}
.metric-tile .mt-bar {{
  margin-top: 14px; height: 4px;
  background: var(--surface-2); border-radius: 2px; overflow: hidden;
}}
.metric-tile .mt-bar-fill {{ height: 100%; background: var(--bucket); border-radius: 2px; }}
.metric-tile .mt-compare {{
  margin-top: 10px; font-family: var(--font-mono); font-size: 11px;
  color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em;
}}

.claims-table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
.claims-table th, .claims-table td {{
  text-align: left; padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}}
.claims-table th {{
  font-family: var(--font-mono); font-size: 11px;
  color: var(--text-3); text-transform: uppercase;
  letter-spacing: 0.1em; font-weight: 700;
  background: var(--surface-1);
}}
.claims-table td.c-id {{ font-family: var(--font-mono); color: var(--text-2); white-space: nowrap; }}
.claims-table td.c-title {{ color: var(--text); }}
.claims-table td.c-status {{ font-family: var(--font-mono); font-size: 12px; white-space: nowrap; }}
.claims-table td.c-skip {{ font-size: 12px; color: var(--text-3); white-space: pre-wrap; line-height: 1.5; max-width: 320px; }}
.claims-table tr.prio-critical td.c-id::before {{ content: "◆"; color: var(--bad); margin-right: 6px; }}
.claims-table tr.prio-high td.c-id::before     {{ content: "◆"; color: var(--warn); margin-right: 6px; }}
.claims-table tr.prio-medium td.c-id::before   {{ content: "◆"; color: var(--text-2); margin-right: 6px; }}
.claims-table tr.prio-low td.c-id::before      {{ content: "◆"; color: var(--text-3); margin-right: 6px; }}

.prio-pill {{
  display: inline-block; font-family: var(--font-mono); font-size: 10px;
  padding: 2px 8px; border-radius: 3px; text-transform: uppercase;
  letter-spacing: 0.08em; font-weight: 700;
}}
.prio-pill.critical {{ background: var(--bad-bg); color: var(--bad); }}
.prio-pill.high     {{ background: var(--warn-bg); color: var(--warn); }}
.prio-pill.medium   {{ background: var(--surface-2); color: var(--text-2); }}
.prio-pill.low      {{ background: var(--surface-2); color: var(--text-3); }}

.run-card {{
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 22px 24px;
  margin-bottom: 12px;
}}
.run-card h3 {{ font-family: var(--font-mono); font-size: 14px; margin: 0; color: var(--text); }}
.run-card .run-date {{ font-family: var(--font-mono); font-size: 12px; color: var(--text-3); margin: 4px 0 16px; }}
.run-metrics {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }}
.run-metric {{
  font-family: var(--font-mono); font-size: 12px;
  background: var(--surface-2); padding: 6px 12px;
  border-radius: var(--radius-sm); color: var(--text-2);
}}
.run-metric b {{ color: var(--text-3); font-weight: 500; margin-right: 6px; }}
.run-metric .v {{ color: var(--text); font-weight: 600; }}
.run-rbc {{ list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 6px; }}
.run-rbc li {{
  font-family: var(--font-mono); font-size: 11px;
  background: var(--surface-2); padding: 4px 8px;
  border-radius: 3px; color: var(--text-2);
  border: 1px solid var(--border);
}}
.run-rbc li.pass    {{ border-left: 2px solid var(--ok); }}
.run-rbc li.partial {{ border-left: 2px solid var(--warn); }}
.run-rbc li.fail    {{ border-left: 2px solid var(--bad); }}
.run-rbc li.skip    {{ border-left: 2px solid var(--skip); }}

pre.md {{
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 24px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: var(--font-mono);
  font-size: 12.5px;
  line-height: 1.65;
  color: var(--text-2);
}}
pre.md code {{ color: var(--text); }}

footer {{
  margin-top: 80px; padding-top: 32px;
  border-top: 1px solid var(--border);
  font-family: var(--font-mono); font-size: 11px;
  color: var(--text-3); text-transform: uppercase;
  letter-spacing: 0.12em;
  display: flex; justify-content: space-between; gap: 20px; flex-wrap: wrap;
}}
footer a {{ color: var(--text-2); text-decoration: none; border-bottom: 1px solid var(--border); }}
footer a:hover {{ color: var(--text); border-color: var(--text-3); }}

.dim {{ color: var(--text-3); }}

/* i18n — dual-language content swap */
.i18n::before {{ content: attr(data-en); }}
html[lang="zh"] .i18n::before {{ content: attr(data-zh); }}

@media (prefers-color-scheme: light) {{
  :root {{
    --bg:            #fbf8f3;
    --surface-0:     #ffffff;
    --surface-1:     #f6f1e9;
    --surface-2:     #ede6d9;
    --border:        rgba(20, 18, 14, 0.07);
    --border-strong: rgba(20, 18, 14, 0.16);
    --text:   #1a1714;
    --text-2: #5c5246;
    --text-3: #8a7e6f;
    --skip:    #8a7e6f;
    --skip-bg: rgba(138, 126, 111, 0.10);
  }}
}}

@media (max-width: 720px) {{
  main {{ padding: 0 20px 80px; }}
  .hero {{ padding: 8px 0 48px; margin-bottom: 48px; }}
  section {{ margin-bottom: 64px; }}
  h1.repo-title {{ font-size: 40px; }}
  .tagline {{ margin-bottom: 48px; }}
  .section-head h2 {{ font-size: 24px; }}
  .capabilities-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>

<body>
<main>

  <div class="topbar">
    <div class="wordmark">repo<span class="dot">·</span>evals</div>
    <div class="lang-toggle" aria-label="language toggle">
      <button data-lang="en" onclick="setLang('en')">EN</button>
      <button data-lang="zh" onclick="setLang('zh')">中</button>
    </div>
  </div>

  <header class="hero">
    <div class="eyebrow">
      <span class="i18n" data-en="Verdict report" data-zh="评测结论"></span>
      <span class="sep">·</span>
      <span>{_esc(vd.date)}</span>
      {version_chip}
    </div>

    <h1 class="repo-title">{_esc(vd.display_name)}</h1>
    <div class="repo-slug">{_esc(vd.owner_repo)}</div>

    <p class="tagline">{product_one_liner_html}</p>

    <div class="verdict-block">
      <div>
        <div class="eyebrow" style="margin-bottom:12px"><span class="i18n" data-en="Final verdict" data-zh="最终判定"></span></div>
        {score_block_html or f'<div class="verdict-word">{_esc(bucket)}</div>'}
      </div>

      <div class="verdict-meta">
        <div class="label"><span class="i18n" data-en="Confidence" data-zh="置信度"></span></div>
        <div class="confidence"><span class="value">{confidence}</span>{layer_pill_html}</div>

        <div class="label"><span class="i18n" data-en="Claim results" data-zh="Claim 结果"></span> · {total_claims} <span class="i18n" data-en="total" data-zh="共"></span></div>
        <div class="stats-bar">{stats_bar_html}</div>
        <div class="stats-legend">{stats_legend_html}</div>

        {score_breakdown_html}
      </div>
    </div>
  </header>

  {scenarios_html}

  {deployment_html}

  <div class="pull-quotes">
    {best_for_html or ''}
    {watch_out_html or ''}
  </div>

  <section>
    <div class="section-head">
      <h2><span class="i18n" data-en="What we verified" data-zh="我们验证了什么"></span></h2>
      <span class="count">{covered} / {total_claims}</span>
    </div>
    <div class="capabilities-grid">
      {capability_cards_html}
    </div>
  </section>

  {("<section><div class='section-head'><h2><span class='i18n' "
    "data-en='How we evaluated this · by layer' "
    "data-zh='我们如何按层级评测'></span></h2></div>" + layer_section_html + "</section>")
    if layer_section_html else ""}

  <details class="section-fold">
    <summary><span class="i18n" data-en="Technical details" data-zh="技术细节"></span></summary>
    <div class="body">

      <div class="subsection">
        <h3><span class="i18n" data-en="Ceiling &amp; blocking reasons" data-zh="Ceiling 与 Blocking 理由"></span></h3>
        <div class="grid-two">
          <div class="mini-card">
            <h4><span class="i18n" data-en="Why capped" data-zh="为什么封顶"></span></h4>
            <ul>{ceilings_html}</ul>
          </div>
          <div class="mini-card">
            <h4><span class="i18n" data-en="Blocking issues" data-zh="Blocking 问题"></span></h4>
            <ul>{blocking_html}</ul>
          </div>
        </div>
      </div>

      <div class="subsection">
        <h3><span class="i18n" data-en="Derivation" data-zh="推导路径"></span></h3>
        {flow_html}
      </div>

      <div class="subsection">
        <h3><span class="i18n" data-en="Claim ledger" data-zh="Claim 清单"></span></h3>
        <table class="claims-table">
          <thead>
            <tr>
              <th style="width:110px"><span class="i18n" data-en="ID" data-zh="ID"></span></th>
              <th><span class="i18n" data-en="Title" data-zh="标题"></span></th>
              <th style="width:100px"><span class="i18n" data-en="Priority" data-zh="优先级"></span></th>
              <th style="width:170px"><span class="i18n" data-en="Area" data-zh="领域"></span></th>
              <th style="width:130px"><span class="i18n" data-en="Status" data-zh="状态"></span></th>
              <th><span class="i18n" data-en="Note" data-zh="备注"></span></th>
            </tr>
          </thead>
          <tbody>
            {claim_ledger_html}
          </tbody>
        </table>
      </div>

      <div class="subsection">
        <h3><span class="i18n" data-en="Runs &amp; metrics" data-zh="Runs 与指标"></span></h3>
        <div class="metric-tiles">
          {metric_tiles_html}
        </div>
        {run_cards_html}
      </div>

    </div>
  </details>

  <details class="section-fold">
    <summary><span class="i18n" data-en="Test log — all probes we ran" data-zh="测试日志 — 我们跑过的所有探针"></span></summary>
    <div class="body">
      {test_log_html}
    </div>
  </details>

  <details class="section-fold">
    <summary><span class="i18n" data-en="Raw verdict archive (authored by evaluator)" data-zh="原始 verdict 存档（评测者原文）"></span></summary>
    <div class="body">
<pre class="md">{verdict_md_escaped}</pre>
    </div>
  </details>

  <footer>
    <div><span class="i18n" data-en="Rendered by repo-evals · render_verdict_html.py" data-zh="由 repo-evals · render_verdict_html.py 生成"></span></div>
    <div><a href="{_esc(repo_url)}" target="_blank" rel="noopener">{_esc(vd.owner_repo)}</a></div>
  </footer>

</main>

<script>
  const LANG_KEY = 'repoEvalsVerdictLang';
  const INITIAL_LANG = {json.dumps(initial_lang)};
  function detectLang() {{
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
  }}
  setLang(detectLang());
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
