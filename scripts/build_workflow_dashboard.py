#!/usr/bin/env python3
"""Build dashboard/workflows/<workflow-id>.html — workflow-overlay view.

Where ``all-evals.html`` is the generic-eval index, this page is the
workflow-specific map: which evaluated repos sit at which stage of a
given workflow (Park content / Park trading / Park development). Empty
stages are surfaced as "GAP" markers — those are roadmap signals.

Run:
    python3 scripts/build_workflow_dashboard.py park-content-v1
    python3 scripts/build_workflow_dashboard.py --all
"""
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verdict_calculator as vc


ROLE_LABELS: dict[str, tuple[str, str, str]] = {
    "primary":     ("Primary",     "主要", "wp-primary"),
    "support":     ("Support",     "辅助", "wp-support"),
    "alternative": ("Alternative", "替代", "wp-alternative"),
    "reference":   ("Reference",   "参考", "wp-reference"),
}


def _load_workflow(wf_id: str) -> dict | None:
    path = ROOT / "workflows" / f"{wf_id}.yaml"
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text())


def _bilingual_text(val) -> tuple[str, str]:
    if isinstance(val, dict):
        return (val.get("en") or val.get("zh") or "",
                val.get("zh") or val.get("en") or "")
    s = str(val or "")
    return (s, s)


def _load_repo_for_card(slug: str) -> dict | None:
    """Pull the data needed to render one repo card on the workflow page."""

    repo_dir = ROOT / "repos" / slug
    repo_yaml = repo_dir / "repo.yaml"
    cm_yaml = repo_dir / "claims" / "claim-map.yaml"
    if not repo_yaml.exists() or not cm_yaml.exists():
        return None

    repo = yaml.safe_load(repo_yaml.read_text()) or {}
    cm = yaml.safe_load(cm_yaml.read_text()) or {}
    claims = cm.get("claims") or []

    inp = {
        "repo": f"{repo.get('owner','?')}/{repo.get('repo','?')}",
        "archetype": repo.get("archetype", "unknown"),
        "layer": repo.get("layer", "unknown"),
        "core_layer_tested": repo.get("layer", "") == "atom",
        "evidence_completeness": "partial",
        "claims": [
            {"id": c.get("id", ""), "priority": c.get("priority", "medium"),
             "status": c.get("status", "untested"), "area": c.get("area", "")}
            for c in claims
        ],
    }
    for k in ("stars", "archived", "has_license", "multilingual_readme",
              "release_pipeline_score", "eval_discipline_score",
              "recently_active"):
        if k in repo:
            inp[k] = repo[k]

    try:
        result = vc.compute_verdict(inp)
    except Exception:
        return None

    pv = repo.get("product_view") or {}
    ol = pv.get("one_liner") or {}
    one_liner_zh = (ol.get("zh") if isinstance(ol, dict) else "") or ""
    one_liner_en = (ol.get("en") if isinstance(ol, dict) else "") or ""

    dossiers = sorted(repo_dir.glob("verdicts/*-verdict.html"), reverse=True)
    dossier_rel = (
        dossiers[0].relative_to(ROOT).as_posix()
        if dossiers else None
    )

    return {
        "slug": slug,
        "owner": repo.get("owner", ""),
        "display": repo.get("display_name") or repo.get("repo", ""),
        "stars": int(repo.get("stars", 0) or 0),
        "layer": str(repo.get("layer", "") or "").lower(),
        "score": int(result.get("score", 0)),
        "category_emoji": result.get("category_emoji", ""),
        "category_en": result.get("category_en", ""),
        "category_zh": result.get("category_zh", ""),
        "category_key": result.get("category_key", "available"),
        "one_liner_en": one_liner_en,
        "one_liner_zh": one_liner_zh,
        "dossier_rel": dossier_rel,
        "placements": repo.get("workflow_placements") or [],
    }


def collect_repos_in_workflow(wf_id: str) -> dict[str, list[dict]]:
    """Return {stage_id: [card, ...]} for repos placed in this workflow.

    Each card carries the repo summary plus the matching placement
    (role + reason + medium) from this workflow's placements. Sorted
    by score within each stage.
    """

    by_stage: dict[str, list[dict]] = {}
    repos_dir = ROOT / "repos"
    for slug_dir in sorted(repos_dir.iterdir()):
        if not slug_dir.is_dir():
            continue
        card = _load_repo_for_card(slug_dir.name)
        if card is None:
            continue
        for p in card["placements"]:
            if str(p.get("workflow_id", "")) != wf_id:
                continue
            stage_id = str(p.get("stage_id", ""))
            entry = dict(card)
            entry["placement"] = p
            by_stage.setdefault(stage_id, []).append(entry)
    # Sort each bucket by score desc
    for sid, entries in by_stage.items():
        entries.sort(key=lambda c: -c["score"])
    return by_stage


def render_card(entry: dict) -> str:
    p = entry["placement"]
    role = str(p.get("role", "")).lower()
    role_en, role_zh, role_class = ROLE_LABELS.get(
        role, (role.capitalize(), role, "wp-primary"))
    medium = p.get("medium")
    medium_pill = (
        f'<span class="wp-medium-pill">{html.escape(str(medium))}</span>'
        if medium else ''
    )
    reason_en, reason_zh = _bilingual_text(p.get("reason") or {})

    dossier_link = (
        f'../../{html.escape(entry["dossier_rel"])}'
        if entry["dossier_rel"] else "#"
    )

    return (
        f'<article class="wf-card {role_class}">'
        f'<div class="wf-card-head">'
        f'<a class="wf-card-name" href="{dossier_link}">'
        f'<strong>{html.escape(entry["owner"])}/{html.escape(entry["display"])}</strong>'
        f'</a>'
        f'<div class="wf-card-meta">'
        f'<span class="wf-score-pill cat-{entry["category_key"]}">'
        f'{entry["category_emoji"]} {entry["score"]}'
        f'</span>'
        f'<span class="wf-layer-pill layer-{entry["layer"]}">{html.escape(entry["layer"])}</span>'
        f'<span class="wf-role-pill">'
        f'<span class="i18n-block en-block inline">{html.escape(role_en)}</span>'
        f'<span class="i18n-block zh-block inline">{html.escape(role_zh)}</span>'
        f'</span>'
        f'{medium_pill}'
        f'</div>'
        f'</div>'
        f'<div class="wf-card-oneliner">'
        f'<span class="i18n-block en-block">{html.escape(entry["one_liner_en"])}</span>'
        f'<span class="i18n-block zh-block">{html.escape(entry["one_liner_zh"])}</span>'
        f'</div>'
        f'<div class="wf-card-reason">'
        f'<span class="i18n-block en-block">{html.escape(reason_en)}</span>'
        f'<span class="i18n-block zh-block">{html.escape(reason_zh)}</span>'
        f'</div>'
        f'</article>'
    )


def render_stage_block(stage: dict, entries: list[dict]) -> str:
    name = stage.get("name") or {}
    name_en, name_zh = _bilingual_text(name)
    desc = stage.get("description") or {}
    desc_en, desc_zh = _bilingual_text(desc)
    artifact = stage.get("expected_artifact") or {}
    art_en, art_zh = _bilingual_text(artifact)

    if entries:
        cards_html = "".join(render_card(e) for e in entries)
        body = f'<div class="wf-stage-cards">{cards_html}</div>'
    else:
        body = (
            '<div class="wf-stage-gap">'
            '<span class="wf-gap-icon">⚠</span> '
            '<span class="i18n-block en-block">'
            'No evaluated repo at this stage yet — this is a roadmap gap.'
            '</span>'
            '<span class="i18n-block zh-block">'
            '这一阶段还没有评测过的 repo —— 这是路线图缺口。'
            '</span>'
            '</div>'
        )

    return (
        f'<section class="wf-stage" id="{html.escape(str(stage.get("id","")))}">'
        f'<div class="wf-stage-header">'
        f'<div class="wf-stage-num">{html.escape(str(stage.get("id","")).split("_",1)[0])}</div>'
        f'<div class="wf-stage-titles">'
        f'<h2>'
        f'<span class="i18n-block en-block">{html.escape(name_en)}</span>'
        f'<span class="i18n-block zh-block">{html.escape(name_zh)}</span>'
        f'</h2>'
        f'<p class="wf-stage-desc">'
        f'<span class="i18n-block en-block">{html.escape(desc_en)}</span>'
        f'<span class="i18n-block zh-block">{html.escape(desc_zh)}</span>'
        f'</p>'
        f'<p class="wf-stage-artifact">'
        f'<span class="wf-artifact-label">'
        f'<span class="i18n-block en-block">→ Expected artifact:</span>'
        f'<span class="i18n-block zh-block">→ 预期产物:</span>'
        f'</span> '
        f'<span class="i18n-block en-block">{html.escape(art_en)}</span>'
        f'<span class="i18n-block zh-block">{html.escape(art_zh)}</span>'
        f'</p>'
        f'</div>'
        f'<div class="wf-stage-count">{len(entries)}</div>'
        f'</div>'
        f'{body}'
        f'</section>'
    )


def build_one(wf_id: str) -> Path | None:
    wf = _load_workflow(wf_id)
    if not wf:
        print(f"  SKIP {wf_id} — no workflow YAML", file=sys.stderr)
        return None

    name = wf.get("name") or {}
    name_en, name_zh = _bilingual_text(name)

    stages = wf.get("stages") or []
    by_stage = collect_repos_in_workflow(wf_id)

    stage_blocks = "\n".join(
        render_stage_block(st, by_stage.get(str(st.get("id", "")), []))
        for st in stages
    )

    total_repos = sum(len(v) for v in by_stage.values())
    filled_stages = sum(1 for st in stages if by_stage.get(str(st.get("id", ""))))
    total_stages = len(stages)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(name_en)} · repo-evals</title>
<style>
:root {{
  --bg: #0b0b0d; --surface-1: #14141a; --surface-2: #1c1c24;
  --border: #2a2a36; --border-strong: #3a3a4a;
  --text: #f0f0f5; --text-2: #a0a0b0; --text-3: #6a6a78;
  --accent: #60a5fa;
  --layer-atom: #4ade80; --layer-molecule: #c084fc; --layer-compound: #f87171;
  --cat-production: #4ade80;
  --cat-available:  #60a5fa;
  --cat-risky:      #f59e0b;
  --cat-dont_use:   #f87171;
  --ok: #4ade80; --warn: #f59e0b; --bad: #f87171;
  --font-sans: ui-sans-serif, system-ui, "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
  --font-serif: ui-serif, Georgia, serif;
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{ font-family: var(--font-sans); background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.55; }}
.page {{ max-width: 1400px; margin: 0 auto; padding: 28px 24px 80px; }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.crumb {{ font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-3); margin-bottom: 6px; }}
.crumb a {{ color: var(--text-3); }}
.crumb a:hover {{ color: var(--text-2); }}
h1 {{ font-family: var(--font-serif); font-size: 36px; font-weight: 700; margin: 0 0 8px; line-height: 1.05; }}
.lead {{ color: var(--text-2); max-width: 80ch; margin: 0 0 22px; font-size: 15px; }}

.lang-toggle {{ position: fixed; top: 16px; right: 18px; display: inline-flex; gap: 4px; padding: 4px;
  background: var(--surface-1); border: 1px solid var(--border); border-radius: 999px;
  font-family: var(--font-mono); font-size: 11px; z-index: 100; }}
.lang-toggle button {{ font: inherit; background: transparent; color: var(--text-2);
  border: 0; padding: 4px 10px; border-radius: 999px; cursor: pointer; }}
.lang-toggle button.active {{ background: var(--surface-2); color: var(--text); }}

.i18n-block {{ display: none; }}
html[lang="en"] .en-block {{ display: block; }}
html[lang="en"] .en-block.inline {{ display: inline; }}
html[lang="zh"] .zh-block {{ display: block; }}
html[lang="zh"] .zh-block.inline {{ display: inline; }}
html[lang="en"] span.en-block.i18n-block {{ display: inline; }}
html[lang="zh"] span.zh-block.i18n-block {{ display: inline; }}

.summary-tiles {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 12px 0 28px; }}
@media (max-width: 720px) {{ .summary-tiles {{ grid-template-columns: 1fr; }} }}
.tile {{ background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px; }}
.tile-label {{ font-family: var(--font-mono); font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-3); margin-bottom: 4px; }}
.tile-value {{ font-family: var(--font-serif); font-size: 28px; font-weight: 700; line-height: 1.05; }}

.wf-stage {{
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px 26px;
  margin-bottom: 16px;
}}
.wf-stage-header {{
  display: grid; grid-template-columns: auto 1fr auto;
  gap: 18px; align-items: start; margin-bottom: 14px;
}}
.wf-stage-num {{
  font-family: var(--font-mono); font-size: 26px; font-weight: 700;
  color: var(--accent); line-height: 1;
  padding-top: 4px; min-width: 36px; text-align: center;
}}
.wf-stage-titles h2 {{ font-family: var(--font-serif); font-size: 22px; margin: 0 0 4px; line-height: 1.15; }}
.wf-stage-desc {{ color: var(--text-2); font-size: 13.5px; margin: 0 0 6px; line-height: 1.5; }}
.wf-stage-artifact {{
  font-size: 12.5px; color: var(--text-3); margin: 0;
  font-family: var(--font-mono);
}}
.wf-artifact-label {{ color: var(--text-2); font-weight: 700; letter-spacing: 0.04em; }}
.wf-stage-count {{
  font-family: var(--font-mono); font-size: 11px;
  color: var(--text-3); padding: 4px 10px;
  background: var(--surface-2); border-radius: 999px;
  white-space: nowrap;
}}

.wf-stage-cards {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 12px;
}}
.wf-card {{
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--text-3);
  border-radius: 8px;
  padding: 12px 14px;
  display: flex; flex-direction: column; gap: 6px;
}}
.wf-card.wp-primary     {{ border-left-color: var(--ok); }}
.wf-card.wp-support     {{ border-left-color: var(--accent); }}
.wf-card.wp-alternative {{ border-left-color: var(--warn); }}
.wf-card.wp-reference   {{ border-left-color: var(--text-3); border-left-style: dashed; }}
.wf-card-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; flex-wrap: wrap; }}
.wf-card-name {{ color: var(--text); font-size: 14px; }}
.wf-card-name:hover strong {{ text-decoration: underline; }}
.wf-card-meta {{ display: flex; gap: 4px; flex-wrap: wrap; align-items: center; }}
.wf-score-pill {{
  font-family: var(--font-mono); font-size: 11px;
  padding: 2px 7px; border-radius: 999px; background: var(--bg); color: var(--text-2);
  white-space: nowrap;
}}
.wf-score-pill.cat-production {{ color: var(--cat-production); }}
.wf-score-pill.cat-available  {{ color: var(--cat-available); }}
.wf-score-pill.cat-risky      {{ color: var(--cat-risky); }}
.wf-score-pill.cat-dont_use   {{ color: var(--cat-dont_use); }}
.wf-layer-pill {{
  font-family: var(--font-mono); font-size: 9.5px;
  padding: 2px 6px; border-radius: 4px; background: var(--bg);
  text-transform: uppercase; letter-spacing: 0.08em;
}}
.wf-layer-pill.layer-atom     {{ color: var(--layer-atom); }}
.wf-layer-pill.layer-molecule {{ color: var(--layer-molecule); }}
.wf-layer-pill.layer-compound {{ color: var(--layer-compound); }}
.wf-role-pill {{
  font-family: var(--font-mono); font-size: 9.5px;
  padding: 2px 6px; border-radius: 4px; background: var(--bg);
  color: var(--text-2); text-transform: uppercase; letter-spacing: 0.08em;
}}
.wp-medium-pill {{
  font-family: var(--font-mono); font-size: 9.5px;
  padding: 2px 6px; border-radius: 4px; background: var(--bg); color: var(--text-3);
}}
.wf-card-oneliner {{ font-size: 12.5px; color: var(--text); line-height: 1.5; }}
.wf-card-reason {{
  font-size: 11.5px; color: var(--text-2); line-height: 1.45;
  border-top: 1px dashed var(--border); padding-top: 6px; margin-top: 2px;
}}

.wf-stage-gap {{
  font-size: 13px; color: var(--text-3);
  padding: 14px; background: var(--surface-2);
  border: 1px dashed var(--border-strong); border-radius: 8px;
  text-align: center;
}}
.wf-gap-icon {{ color: var(--warn); margin-right: 6px; }}

footer {{ margin-top: 36px; padding-top: 18px; border-top: 1px solid var(--border);
  font-family: var(--font-mono); font-size: 11px; color: var(--text-3); }}
</style>
</head>
<body>
<div class="lang-toggle">
  <button data-lang="en" class="active">EN</button>
  <button data-lang="zh">中文</button>
</div>

<main class="page">
  <div class="crumb">
    <a href="../all-evals.html">repo-evals</a> ·
    <span class="i18n-block en-block">workflow overlay</span>
    <span class="i18n-block zh-block">workflow overlay (工作流叠加层)</span>
  </div>
  <h1>
    <span class="i18n-block en-block">{html.escape(name_en)}</span>
    <span class="i18n-block zh-block">{html.escape(name_zh)}</span>
  </h1>
  <p class="lead">
    <span class="i18n-block en-block">A workflow overlay maps every evaluated repo onto a stage of {html.escape(name_en)}. Empty stages are roadmap gaps — what to find / build next. The generic catalog (no workflow lens) is at <a href="../all-evals.html">all-evals.html</a>.</span>
    <span class="i18n-block zh-block">workflow overlay 把每个评测过的 repo 映射到 {html.escape(name_zh)} 的某一个 stage。空 stage 就是路线图缺口 —— 下一个该找/造的东西。通用目录(不带 workflow 视角)在 <a href="../all-evals.html">all-evals.html</a>。</span>
  </p>

  <div class="summary-tiles">
    <div class="tile">
      <div class="tile-label"><span class="i18n-block en-block">Total stages</span><span class="i18n-block zh-block">总阶段数</span></div>
      <div class="tile-value">{total_stages}</div>
    </div>
    <div class="tile">
      <div class="tile-label"><span class="i18n-block en-block">Stages filled</span><span class="i18n-block zh-block">已填充阶段</span></div>
      <div class="tile-value">{filled_stages} / {total_stages}</div>
    </div>
    <div class="tile">
      <div class="tile-label"><span class="i18n-block en-block">Repos placed</span><span class="i18n-block zh-block">已放置 repo</span></div>
      <div class="tile-value">{total_repos}</div>
    </div>
  </div>

  {stage_blocks}

  <footer>
    <span class="i18n-block en-block">Generated by scripts/build_workflow_dashboard.py from workflows/{wf_id}.yaml + repos/*/repo.yaml.workflow_placements. Re-run to refresh.</span>
    <span class="i18n-block zh-block">由 scripts/build_workflow_dashboard.py 从 workflows/{wf_id}.yaml + repos/*/repo.yaml.workflow_placements 生成。重新跑脚本即可刷新。</span>
  </footer>
</main>

<script>
const buttons = document.querySelectorAll('.lang-toggle button');
const setLang = (lang) => {{
  document.documentElement.lang = lang;
  buttons.forEach(b => b.classList.toggle('active', b.dataset.lang === lang));
  try {{ localStorage.setItem('repo-evals-master-lang', lang); }} catch (e) {{}}
}};
buttons.forEach(b => b.addEventListener('click', () => setLang(b.dataset.lang)));
let _lang = 'en';
try {{
  const stored = localStorage.getItem('repo-evals-master-lang');
  if (stored === 'zh' || stored === 'en') _lang = stored;
  else if ((navigator.language || '').toLowerCase().startsWith('zh')) _lang = 'zh';
}} catch (e) {{}}
setLang(_lang);
</script>
</body>
</html>
"""

    out_dir = ROOT / "dashboard" / "workflows"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{wf_id.replace('park-', '').replace('-v1', '')}.html"
    out_path.write_text(page)
    print(f"  wrote {out_path}")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow_id", nargs="?",
                        help="e.g. park-content-v1; omit + use --all to build all")
    parser.add_argument("--all", action="store_true",
                        help="Build every workflows/*.yaml")
    args = parser.parse_args(argv)

    if args.all:
        for path in sorted((ROOT / "workflows").glob("*.yaml")):
            build_one(path.stem)
        return 0
    if not args.workflow_id:
        parser.error("specify a workflow_id or --all")
    build_one(args.workflow_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
