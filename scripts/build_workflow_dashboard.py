#!/usr/bin/env python3
"""Build dashboard/workflows/<workflow-id>.html — left-to-right column view.

Layout:
  - 8 stages laid out as 8 columns from left to right
  - Inside each column: repos stacked vertically, sorted by score
  - Stages 02 (acquisition) and 07 (distribution) further break out by
    platform (X / 抖音 / 小红书 / 微信公众号 / etc.) — the per-platform
    sub-headers carry their own logos and contain only the repos that
    cover that platform

Theme:
  - Light / white theme (warm off-white surfaces, dark text)
  - Bilingual EN/ZH toggle preserved

Run:
    python3 scripts/build_workflow_dashboard.py park-content-v1
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


# Per-platform display metadata (logo character + bilingual name).
# Used for sub-headers in stages 02 + 07.
PLATFORM_META: dict[str, tuple[str, str, str]] = {
    "x":            ("𝕏",  "X (Twitter)",   "X"),
    "twitter":      ("𝕏",  "X (Twitter)",   "X"),
    "douyin":       ("🎵", "Douyin",        "抖音"),
    "xiaohongshu":  ("📕", "Xiaohongshu",   "小红书"),
    "wechat-mp":    ("💬", "WeChat 公众号", "微信公众号"),
    "wechat-video": ("📹", "WeChat 视频号", "微信视频号"),
    "bilibili":     ("📺", "Bilibili",      "B 站"),
    "kuaishou":     ("🎬", "Kuaishou",      "快手"),
    "tiktok":       ("🎵", "TikTok",        "TikTok"),
    "youtube":      ("▶️", "YouTube",       "YouTube"),
    "reddit":       ("👽", "Reddit",        "Reddit"),
    "github":       ("🐙", "GitHub",        "GitHub"),
    "weibo":        ("🌐", "Weibo",         "微博"),
    "tieba":        ("📌", "Baidu Tieba",   "贴吧"),
    "zhihu":        ("📖", "Zhihu",         "知乎"),
    "other":        ("•",  "Other",         "其他"),
    "multi":        ("∞",  "Multi-platform","多平台"),
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
    dossier_rel = dossiers[0].relative_to(ROOT).as_posix() if dossiers else None

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


def collect_for_workflow(wf_id: str) -> dict[str, list[dict]]:
    """{stage_id: [card with placement attached, ...]} for a workflow."""

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
    for entries in by_stage.values():
        entries.sort(key=lambda c: -c["score"])
    return by_stage


def render_repo_card(entry: dict) -> str:
    p = entry["placement"]
    role = str(p.get("role", "")).lower()
    role_en, role_zh, role_class = ROLE_LABELS.get(
        role, (role.capitalize(), role, "wp-primary"))
    medium = p.get("medium")
    medium_pill = (
        f'<span class="wf-medium-pill">{html.escape(str(medium))}</span>'
        if medium else ''
    )

    dossier_link = (
        f'../../{html.escape(entry["dossier_rel"])}'
        if entry["dossier_rel"] else "#"
    )

    return (
        f'<article class="wf-card {role_class}">'
        f'<a class="wf-card-link" href="{dossier_link}">'
        f'<div class="wf-card-head">'
        f'<div class="wf-card-name"><strong>{html.escape(entry["owner"])}/{html.escape(entry["display"])}</strong></div>'
        f'<span class="wf-score-pill cat-{entry["category_key"]}">'
        f'{entry["category_emoji"]} {entry["score"]}'
        f'</span>'
        f'</div>'
        f'<div class="wf-card-meta">'
        f'<span class="wf-layer-pill layer-{entry["layer"]}">{html.escape(entry["layer"])}</span>'
        f'<span class="wf-role-pill {role_class}">'
        f'<span class="i18n-block en-block inline">{html.escape(role_en)}</span>'
        f'<span class="i18n-block zh-block inline">{html.escape(role_zh)}</span>'
        f'</span>'
        f'{medium_pill}'
        f'</div>'
        f'<div class="wf-card-oneliner">'
        f'<span class="i18n-block en-block">{html.escape(entry["one_liner_en"][:140])}</span>'
        f'<span class="i18n-block zh-block">{html.escape(entry["one_liner_zh"][:140])}</span>'
        f'</div>'
        f'</a>'
        f'</article>'
    )


def render_platform_section(platform_key: str, entries: list[dict]) -> str:
    logo, en, zh = PLATFORM_META.get(
        platform_key,
        ("•", platform_key.title(), platform_key)
    )
    cards = "".join(render_repo_card(e) for e in entries)
    return (
        f'<div class="wf-platform-section" data-platform="{platform_key}">'
        f'<div class="wf-platform-header">'
        f'<span class="wf-platform-logo">{logo}</span>'
        f'<span class="wf-platform-name">'
        f'<span class="i18n-block en-block inline">{html.escape(en)}</span>'
        f'<span class="i18n-block zh-block inline">{html.escape(zh)}</span>'
        f'</span>'
        f'<span class="wf-platform-count">{len(entries)}</span>'
        f'</div>'
        f'<div class="wf-platform-cards">{cards}</div>'
        f'</div>'
    )


def render_stage_column(stage: dict, entries: list[dict],
                        per_platform: bool) -> str:
    name = stage.get("name") or {}
    name_en, name_zh = _bilingual_text(name)
    artifact = stage.get("expected_artifact") or {}
    art_en, art_zh = _bilingual_text(artifact)

    if not entries:
        body = (
            '<div class="wf-stage-gap">'
            '<span class="wf-gap-icon">⚠</span>'
            '<div class="i18n-block en-block">'
            'No evaluated repo here yet — roadmap gap.'
            '</div>'
            '<div class="i18n-block zh-block">'
            '这一阶段还没有评测过的 repo —— 路线图缺口。'
            '</div>'
            '</div>'
        )
    elif per_platform:
        # Group by platform — entries can have multiple platforms in
        # `placement.platforms` (list); add a card under each platform
        # they cover. Repos without `platforms` go to "other".
        by_platform: dict[str, list[dict]] = {}
        for e in entries:
            placement = e["placement"]
            platforms = placement.get("platforms") or []
            if not platforms:
                platforms = ["other"]
            for plat in platforms:
                key = str(plat).strip().lower()
                by_platform.setdefault(key, []).append(e)
        # Stable ordering: known platforms first in PLATFORM_META order,
        # then anything else alphabetically.
        ordered_keys = [k for k in PLATFORM_META if k in by_platform]
        ordered_keys += sorted(k for k in by_platform if k not in PLATFORM_META)
        body = "".join(render_platform_section(k, by_platform[k]) for k in ordered_keys)
    else:
        body = "".join(render_repo_card(e) for e in entries)

    stage_num = str(stage.get("id", "")).split("_", 1)[0]

    return (
        f'<section class="wf-col" id="{html.escape(str(stage.get("id","")))}">'
        f'<div class="wf-col-head">'
        f'<div class="wf-col-num">{html.escape(stage_num)}</div>'
        f'<div class="wf-col-titles">'
        f'<h2>'
        f'<span class="i18n-block en-block">{html.escape(name_en)}</span>'
        f'<span class="i18n-block zh-block">{html.escape(name_zh)}</span>'
        f'</h2>'
        f'<p class="wf-col-artifact">'
        f'<span class="i18n-block en-block">→ {html.escape(art_en)}</span>'
        f'<span class="i18n-block zh-block">→ {html.escape(art_zh)}</span>'
        f'</p>'
        f'</div>'
        f'<div class="wf-col-count">{len(entries)}</div>'
        f'</div>'
        f'<div class="wf-col-body">{body}</div>'
        f'</section>'
    )


def build_one(wf_id: str) -> Path | None:
    wf = _load_workflow(wf_id)
    if not wf:
        return None

    name = wf.get("name") or {}
    name_en, name_zh = _bilingual_text(name)

    stages = wf.get("stages") or []
    by_stage = collect_for_workflow(wf_id)

    # Stages 02 (acquisition) + 07 (distribution & feedback) get
    # platform breakouts; other stages just stack cards.
    PLATFORM_BREAKOUT_STAGES = {"02_acquisition", "07_distribution"}

    columns = "".join(
        render_stage_column(
            st,
            by_stage.get(str(st.get("id", "")), []),
            per_platform=str(st.get("id", "")) in PLATFORM_BREAKOUT_STAGES,
        )
        for st in stages
    )

    total_repos = sum(len(v) for v in by_stage.values())
    filled_stages = sum(1 for st in stages
                        if by_stage.get(str(st.get("id", ""))))
    total_stages = len(stages)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(name_en)} · repo-evals</title>
<style>
:root {{
  /* Light theme */
  --bg:        #fbf8f3;
  --surface-1: #ffffff;
  --surface-2: #f3eee5;
  --surface-3: #ede5d4;
  --border:    rgba(20, 18, 14, 0.10);
  --border-strong: rgba(20, 18, 14, 0.18);
  --text:   #1a1714;
  --text-2: #5c5246;
  --text-3: #8a7e6f;
  --accent: #2563eb;
  --layer-atom:     #2d7866;
  --layer-molecule: #5a3aa1;
  --layer-compound: #a13d30;
  --cat-production: #16a34a;
  --cat-available:  #2563eb;
  --cat-risky:      #d97706;
  --cat-dont_use:   #dc2626;
  --ok: #16a34a; --warn: #d97706; --bad: #dc2626;
  --font-sans: ui-sans-serif, system-ui, "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
  --font-serif: ui-serif, Georgia, serif;
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  font-family: var(--font-sans); background: var(--bg); color: var(--text);
  font-size: 13.5px; line-height: 1.5;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}}
.page-header {{ max-width: 1400px; margin: 0 auto; padding: 28px 24px 18px; }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.crumb {{ font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-3); margin-bottom: 6px; }}
.crumb a {{ color: var(--text-3); }}
.crumb a:hover {{ color: var(--text-2); }}
h1 {{ font-family: var(--font-serif); font-size: 32px; font-weight: 700; margin: 0 0 10px; line-height: 1.1; }}
.lead {{ color: var(--text-2); max-width: 90ch; margin: 0 0 18px; font-size: 14px; }}

.lang-toggle {{ position: fixed; top: 14px; right: 16px; display: inline-flex; gap: 4px; padding: 4px;
  background: var(--surface-1); border: 1px solid var(--border); border-radius: 999px;
  font-family: var(--font-mono); font-size: 11px; z-index: 100;
  box-shadow: 0 2px 8px rgba(20,18,14,0.06); }}
.lang-toggle button {{ font: inherit; background: transparent; color: var(--text-3);
  border: 0; padding: 4px 10px; border-radius: 999px; cursor: pointer; }}
.lang-toggle button.active {{ background: var(--text); color: var(--surface-1); }}

.i18n-block {{ display: none; }}
html[lang="en"] .en-block {{ display: block; }}
html[lang="en"] .en-block.inline {{ display: inline; }}
html[lang="zh"] .zh-block {{ display: block; }}
html[lang="zh"] .zh-block.inline {{ display: inline; }}
html[lang="en"] span.en-block.i18n-block {{ display: inline; }}
html[lang="zh"] span.zh-block.i18n-block {{ display: inline; }}

.summary-tiles {{ display: flex; gap: 10px; margin: 12px 0 20px; flex-wrap: wrap; }}
.tile {{ background: var(--surface-1); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; min-width: 140px; }}
.tile-label {{ font-family: var(--font-mono); font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-3); margin-bottom: 4px; }}
.tile-value {{ font-family: var(--font-serif); font-size: 22px; font-weight: 700; line-height: 1; color: var(--text); }}

/* Main 8-column grid — horizontal scroll on narrow screens */
.wf-scroll-wrap {{
  overflow-x: auto;
  padding: 0 24px 24px;
  background: var(--bg);
}}
.wf-grid {{
  display: grid;
  grid-template-columns: repeat({total_stages}, minmax(280px, 1fr));
  gap: 12px;
  min-width: {total_stages * 290}px;
  max-width: 1900px;
  margin: 0 auto;
}}

/* Per-stage column */
.wf-col {{
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 14px 16px;
  display: flex; flex-direction: column;
}}
.wf-col-head {{
  display: grid; grid-template-columns: auto 1fr auto;
  gap: 10px; align-items: start;
  padding-bottom: 12px; border-bottom: 1px solid var(--border);
  margin-bottom: 12px;
}}
.wf-col-num {{
  font-family: var(--font-mono); font-size: 18px; font-weight: 700;
  color: var(--accent); line-height: 1; padding-top: 2px;
  background: var(--surface-2); padding: 4px 8px; border-radius: 4px;
  min-width: 38px; text-align: center;
}}
.wf-col-titles h2 {{
  font-family: var(--font-serif); font-size: 16px; font-weight: 700;
  margin: 0 0 3px; line-height: 1.15; color: var(--text);
}}
.wf-col-artifact {{
  font-family: var(--font-mono); font-size: 10.5px;
  color: var(--text-3); margin: 0; line-height: 1.4;
}}
.wf-col-count {{
  font-family: var(--font-mono); font-size: 10.5px;
  color: var(--text-3); padding: 2px 8px;
  background: var(--surface-2); border-radius: 999px;
  white-space: nowrap; align-self: start;
}}
.wf-col-body {{ display: flex; flex-direction: column; gap: 10px; }}

/* Repo card (used in both per-platform sections and direct stage stacks) */
.wf-card {{
  border: 1px solid var(--border);
  background: var(--surface-2);
  border-left: 3px solid var(--text-3);
  border-radius: 6px;
  overflow: hidden;
}}
.wf-card.wp-primary     {{ border-left-color: var(--ok); }}
.wf-card.wp-support     {{ border-left-color: var(--accent); }}
.wf-card.wp-alternative {{ border-left-color: var(--warn); }}
.wf-card.wp-reference   {{ border-left-color: var(--text-3); border-left-style: dashed; }}
.wf-card-link {{ display: block; padding: 10px 12px; color: var(--text); }}
.wf-card-link:hover {{ background: var(--surface-1); text-decoration: none; }}
.wf-card-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }}
.wf-card-name {{ font-size: 12.5px; line-height: 1.3; }}
.wf-card-name strong {{ color: var(--text); }}
.wf-card-meta {{ display: flex; gap: 4px; flex-wrap: wrap; align-items: center; margin-top: 6px; }}
.wf-score-pill {{
  font-family: var(--font-mono); font-size: 10.5px; font-weight: 700;
  padding: 2px 7px; border-radius: 999px; background: var(--surface-1);
  white-space: nowrap; border: 1px solid var(--border);
}}
.wf-score-pill.cat-production {{ color: var(--cat-production); }}
.wf-score-pill.cat-available  {{ color: var(--cat-available); }}
.wf-score-pill.cat-risky      {{ color: var(--cat-risky); }}
.wf-score-pill.cat-dont_use   {{ color: var(--cat-dont_use); }}
.wf-layer-pill {{
  font-family: var(--font-mono); font-size: 9px;
  padding: 2px 6px; border-radius: 3px; background: var(--surface-1);
  text-transform: uppercase; letter-spacing: 0.06em;
  border: 1px solid var(--border);
}}
.wf-layer-pill.layer-atom     {{ color: var(--layer-atom); }}
.wf-layer-pill.layer-molecule {{ color: var(--layer-molecule); }}
.wf-layer-pill.layer-compound {{ color: var(--layer-compound); }}
.wf-role-pill {{
  font-family: var(--font-mono); font-size: 9px;
  padding: 2px 6px; border-radius: 3px; background: var(--surface-1);
  text-transform: uppercase; letter-spacing: 0.06em;
  border: 1px solid var(--border); color: var(--text-2);
}}
.wf-role-pill.wp-primary     {{ color: var(--ok); border-color: rgba(22, 163, 74, 0.2); }}
.wf-role-pill.wp-support     {{ color: var(--accent); border-color: rgba(37, 99, 235, 0.2); }}
.wf-role-pill.wp-alternative {{ color: var(--warn); border-color: rgba(217, 119, 6, 0.2); }}
.wf-medium-pill {{
  font-family: var(--font-mono); font-size: 9px;
  padding: 2px 6px; border-radius: 3px; background: var(--surface-1);
  color: var(--text-3); border: 1px solid var(--border);
}}
.wf-card-oneliner {{
  font-size: 11.5px; color: var(--text-2); line-height: 1.45;
  margin-top: 6px;
}}

/* Per-platform sub-sections (inside 02 + 07) */
.wf-platform-section {{ margin: 0; }}
.wf-platform-section + .wf-platform-section {{ margin-top: 12px; padding-top: 12px; border-top: 1px dashed var(--border); }}
.wf-platform-header {{
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 8px;
  font-family: var(--font-mono); font-size: 11px;
  color: var(--text-2); font-weight: 700;
  letter-spacing: 0.06em;
}}
.wf-platform-logo {{ font-size: 14px; }}
.wf-platform-name {{ flex: 1; }}
.wf-platform-count {{
  font-size: 10px; padding: 1px 6px; border-radius: 999px;
  background: var(--surface-3); color: var(--text-3);
}}
.wf-platform-cards {{ display: flex; flex-direction: column; gap: 8px; }}

.wf-stage-gap {{
  font-size: 11.5px; color: var(--text-3);
  padding: 14px; background: var(--surface-2);
  border: 1px dashed var(--border-strong); border-radius: 6px;
  text-align: center;
}}
.wf-gap-icon {{ color: var(--warn); margin-right: 4px; font-size: 13px; }}

footer {{
  max-width: 1400px; margin: 24px auto 0; padding: 18px 24px;
  border-top: 1px solid var(--border);
  font-family: var(--font-mono); font-size: 11px; color: var(--text-3);
}}
</style>
</head>
<body>
<div class="lang-toggle">
  <button data-lang="en" class="active">EN</button>
  <button data-lang="zh">中文</button>
</div>

<header class="page-header">
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
    <span class="i18n-block en-block">8-stage pipeline view. Stages 02 (acquisition) and 07 (distribution &amp; feedback) are broken out per-platform — X / 抖音 / 小红书 / 微信公众号 / etc. Empty stages are roadmap gaps. Click any card to open the per-repo dossier.</span>
    <span class="i18n-block zh-block">8 阶段流水线视图。02(内容获取) 和 07(分发反馈) 按平台拆开 —— X / 抖音 / 小红书 / 微信公众号 等。空阶段是路线图缺口。点任意卡片进入 repo 详细 dossier。</span>
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
</header>

<div class="wf-scroll-wrap">
  <div class="wf-grid">
    {columns}
  </div>
</div>

<footer>
  <span class="i18n-block en-block">Generated by scripts/build_workflow_dashboard.py from workflows/{wf_id}.yaml + repos/*/repo.yaml.workflow_placements.</span>
  <span class="i18n-block zh-block">由 scripts/build_workflow_dashboard.py 从 workflows/{wf_id}.yaml + repos/*/repo.yaml.workflow_placements 生成。</span>
</footer>

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
    parser.add_argument("workflow_id", nargs="?")
    parser.add_argument("--all", action="store_true")
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
