#!/usr/bin/env python3
"""Build dashboard/all-evals.html — master index of every evaluated repo.

Surfaces the 5 pieces of key info Wendy locked in (2026-05-05):
  1. tech classification (atom / molecule / compound)
  2. 0-100 score
  3. cost / external deps (API key etc.)
  4. benefits (what scenario this skill solves)
  5. category (Production / Available / Risky / Don't use)

Sortable client-side, filter pills are 4 categories (not 6 tiers).
Bilingual EN/ZH toggle reuses the dossier i18n pattern.

Run:
    python3 scripts/build_master_dashboard.py
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verdict_calculator as vc


def find_dossier(repo_dir: Path) -> Path | None:
    """Latest <date>-verdict.html under verdicts/."""

    vds = sorted(repo_dir.glob("verdicts/*-verdict.html"), reverse=True)
    return vds[0] if vds else None


def _bilingual(val) -> tuple[str, str]:
    """Pull (en, zh) out of either a {en, zh} dict or a plain string."""

    if isinstance(val, dict):
        en = val.get("en", "")
        zh = val.get("zh", "")
        return (en or zh, zh or en)
    s = str(val or "")
    return (s, s)


def load_repo(slug_dir: Path) -> dict | None:
    repo_yaml = slug_dir / "repo.yaml"
    if not repo_yaml.exists():
        return None
    repo = yaml.safe_load(repo_yaml.read_text()) or {}
    claim_map_path = slug_dir / "claims" / "claim-map.yaml"
    if not claim_map_path.exists():
        return None
    cm = yaml.safe_load(claim_map_path.read_text()) or {}
    claims = cm.get("claims") or []

    inp = {
        "repo": f"{repo.get('owner','?')}/{repo.get('repo','?')}",
        "archetype": repo.get("archetype", "unknown"),
        "layer": repo.get("layer", "unknown"),
        "core_layer_tested": repo.get("layer", "") == "atom",
        "evidence_completeness": "partial",
        "claims": [
            {
                "id": c.get("id", ""),
                "priority": c.get("priority", "medium"),
                "status": c.get("status", "untested"),
                "area": c.get("area", ""),
            }
            for c in claims
        ],
    }
    for k in (
        "stars", "archived", "has_license", "multilingual_readme",
        "release_pipeline_score", "eval_discipline_score", "recently_active",
    ):
        if k in repo:
            inp[k] = repo[k]

    try:
        result = vc.compute_verdict(inp)
    except Exception as exc:
        print(f"  WARN {slug_dir.name}: compute_verdict failed: {exc}", file=sys.stderr)
        return None

    pv = repo.get("product_view") or {}
    one_liner_en, one_liner_zh = _bilingual(pv.get("one_liner"))

    # When-to-use: prefer the new `scenario` field (benefits-driven schema);
    # fall back to the first `use_for` entry for repos still on the old
    # schema. Either way we display ONE concise line in the dashboard,
    # readers click into the dossier for the full benefits-cards block.
    when_en = when_zh = ""
    if pv.get("scenario"):
        when_en, when_zh = _bilingual(pv["scenario"])
    elif pv.get("use_for"):
        first = (pv["use_for"] or [None])[0]
        if first:
            when_en, when_zh = _bilingual(first)

    cost_en, cost_zh = _bilingual(pv.get("cost_summary"))

    dossier = find_dossier(slug_dir)
    rel_dossier = (
        dossier.relative_to(ROOT).as_posix() if dossier else None
    )

    return {
        "slug": slug_dir.name,
        "owner": repo.get("owner", ""),
        "repo": repo.get("repo", ""),
        "display": repo.get("display_name") or repo.get("repo", ""),
        "stars": int(repo.get("stars", 0) or 0),
        "archetype": repo.get("archetype", "unknown"),
        "layer": repo.get("layer", "unknown"),
        "score": result.get("score", 0),
        "tier_key": result.get("tier_key", "unknown"),
        "tier_emoji": result.get("tier_emoji", ""),
        "category_key": result.get("category_key", "unknown"),
        "category_emoji": result.get("category_emoji", ""),
        "category_en": result.get("category_en", ""),
        "category_zh": result.get("category_zh", ""),
        "one_liner_en": one_liner_en,
        "one_liner_zh": one_liner_zh,
        "when_en": when_en,
        "when_zh": when_zh,
        "cost_en": cost_en,
        "cost_zh": cost_zh,
        "has_new_schema": bool(pv.get("scenario") or pv.get("with_this") or pv.get("cost_summary")),
        "dossier": rel_dossier,
        "url": repo.get("repo_url", ""),
    }


def _bilingual_cell(en: str, zh: str, kind: str = "block") -> str:
    """Render an EN/ZH pair using the i18n-block CSS pattern.

    `kind` controls whether the spans render block-level or inline; "inline"
    is right for tight cells, "block" for paragraph-style cells.
    """

    en_e = html.escape(en or zh or "")
    zh_e = html.escape(zh or en or "")
    if kind == "inline":
        return (
            f'<span class="i18n-block en-block inline">{en_e}</span>'
            f'<span class="i18n-block zh-block inline">{zh_e}</span>'
        )
    return (
        f'<span class="i18n-block en-block">{en_e}</span>'
        f'<span class="i18n-block zh-block">{zh_e}</span>'
    )


def build():
    rows: list[dict] = []
    for slug_dir in sorted((ROOT / "repos").iterdir()):
        if not slug_dir.is_dir():
            continue
        row = load_repo(slug_dir)
        if row is not None:
            rows.append(row)
    rows.sort(key=lambda r: (-r["score"], -r["stars"]))

    print(f"  collected {len(rows)} evaluated repos")

    table_rows: list[str] = []
    for i, r in enumerate(rows, start=1):
        dossier_link = (
            f'<a href="../{html.escape(r["dossier"])}">→</a>'
            if r["dossier"] else '<span class="muted">—</span>'
        )
        repo_link = (
            f'<a href="{html.escape(r["url"])}" target="_blank" rel="noopener">↗</a>'
            if r["url"] else ""
        )

        cost_cell = (
            _bilingual_cell(r["cost_en"], r["cost_zh"])
            if r["cost_en"] or r["cost_zh"]
            else '<span class="muted">—</span>'
        )

        table_rows.append(
            f'<tr data-score="{r["score"]}" data-stars="{r["stars"]}" '
            f'data-category="{r["category_key"]}" data-tier="{r["tier_key"]}" '
            f'data-layer="{r["layer"]}">'
            f'<td class="num">{i}</td>'
            f'<td class="repo-cell">'
            f'<div class="repo-name"><strong>{html.escape(r["owner"])}/{html.escape(r["display"])}</strong> {repo_link}</div>'
            f'<div class="repo-meta">⭐ {r["stars"]:,} · '
            f'<span class="tag arche-{r["archetype"]}">{html.escape(r["archetype"])}</span> · '
            f'<span class="tag layer-{r["layer"]}">{html.escape(r["layer"])}</span>'
            f'</div>'
            f'</td>'
            f'<td>{_bilingual_cell(r["one_liner_en"], r["one_liner_zh"])}</td>'
            f'<td>{_bilingual_cell(r["when_en"], r["when_zh"]) if (r["when_en"] or r["when_zh"]) else "<span class=muted>—</span>"}</td>'
            f'<td class="cost-cell">{cost_cell}</td>'
            f'<td class="score-cell category-{r["category_key"]}">'
            f'<div class="score-num">{r["score"]}</div>'
            f'<div class="score-cat">'
            f'<span>{r["category_emoji"]}</span> '
            f'{_bilingual_cell(r["category_en"], r["category_zh"], kind="inline")}'
            f'</div></td>'
            f'<td class="num">{dossier_link}</td>'
            f'</tr>'
        )

    # Category counts (4 buckets)
    cat_counts: dict[str, int] = {}
    for r in rows:
        cat_counts[r["category_key"]] = cat_counts.get(r["category_key"], 0) + 1

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>repo-evals · all evaluated repos</title>
<style>
:root {{
  --bg: #0b0b0d; --surface-1: #14141a; --surface-2: #1c1c24;
  --border: #2a2a36; --text: #f0f0f5; --text-2: #a0a0b0; --text-3: #6a6a78;
  --accent: #60a5fa; --good: #4ade80; --warn: #f59e0b; --bad: #f87171;
  --layer-atom: #4ade80; --layer-molecule: #c084fc; --layer-compound: #f87171;
  --cat-production: #4ade80;
  --cat-available:  #60a5fa;
  --cat-risky:      #f59e0b;
  --cat-dont_use:   #f87171;
  --font-sans: ui-sans-serif, system-ui, "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
  --font-serif: ui-serif, Georgia, serif;
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{ font-family: var(--font-sans); background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.55; }}
.page {{ max-width: 1500px; margin: 0 auto; padding: 28px 24px 80px; }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.crumb {{ font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-3); margin-bottom: 6px; }}
h1 {{ font-family: var(--font-serif); font-size: 36px; font-weight: 700; margin: 0 0 8px; line-height: 1.05; }}
.lead {{ color: var(--text-2); max-width: 80ch; margin: 0 0 22px; font-size: 15px; }}

/* lang toggle */
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
html[lang="en"] span.en-block, html[lang="en"] span.en-block.i18n-block {{ display: inline; }}
html[lang="zh"] span.zh-block, html[lang="zh"] span.zh-block.i18n-block {{ display: inline; }}

/* tile stats — 4 categories */
.tiles {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 12px 0 24px; }}
@media (max-width: 900px) {{ .tiles {{ grid-template-columns: repeat(2, 1fr); }} }}
.tile {{ background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }}
.tile-label {{ font-family: var(--font-mono); font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-3); margin-bottom: 4px; white-space: nowrap; }}
.tile-value {{ font-family: var(--font-serif); font-size: 24px; font-weight: 700; line-height: 1.05; }}
.tile.cat-production .tile-value {{ color: var(--cat-production); }}
.tile.cat-available .tile-value  {{ color: var(--cat-available); }}
.tile.cat-risky .tile-value      {{ color: var(--cat-risky); }}
.tile.cat-dont_use .tile-value   {{ color: var(--cat-dont_use); }}

/* search + filter pills */
.controls {{ display: flex; gap: 12px; align-items: center; margin-bottom: 14px; flex-wrap: wrap; }}
.controls input[type="search"] {{
  flex: 1; min-width: 240px; max-width: 380px;
  background: var(--surface-1); border: 1px solid var(--border); color: var(--text);
  padding: 8px 12px; border-radius: 8px; font: inherit;
}}
.controls input[type="search"]:focus {{ outline: 0; border-color: var(--accent); }}
.controls .filter-pill {{
  background: transparent; border: 1px solid var(--border); color: var(--text-2);
  padding: 4px 12px; border-radius: 999px; font-family: var(--font-mono); font-size: 11px;
  cursor: pointer;
}}
.controls .filter-pill.active {{ background: var(--surface-2); color: var(--text); border-color: var(--text-3); }}

/* main table */
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--border);
  font-family: var(--font-mono); font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--text-3); font-weight: 600; cursor: pointer; user-select: none; white-space: nowrap; }}
th.sort-active {{ color: var(--text); }}
th.sort-active::after {{ content: " ↓"; }}
td {{ padding: 12px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }}
tr:hover {{ background: var(--surface-1); }}
td.num {{ font-family: var(--font-mono); text-align: center; color: var(--text-3); }}

.repo-cell {{ min-width: 200px; max-width: 240px; }}
.repo-name strong {{ font-size: 14px; color: var(--text); }}
.repo-meta {{ font-family: var(--font-mono); font-size: 10px; color: var(--text-3); margin-top: 4px; line-height: 1.6; }}
.tag {{ display: inline-block; padding: 1px 6px; border-radius: 4px; background: var(--surface-2); margin-right: 2px; }}
.tag.layer-atom {{ color: var(--layer-atom); }}
.tag.layer-molecule {{ color: var(--layer-molecule); }}
.tag.layer-compound {{ color: var(--layer-compound); }}

.cost-cell {{ font-size: 12px; color: var(--text-2); max-width: 240px; line-height: 1.5; }}

/* score cell */
.score-cell {{ text-align: center; min-width: 110px; }}
.score-cell .score-num {{ font-family: var(--font-serif); font-size: 28px; font-weight: 700; line-height: 1; }}
.score-cell .score-cat {{ font-family: var(--font-mono); font-size: 10px; color: var(--text-2); margin-top: 4px; white-space: nowrap; }}
.score-cell.category-production .score-num {{ color: var(--cat-production); }}
.score-cell.category-available .score-num  {{ color: var(--cat-available); }}
.score-cell.category-risky .score-num      {{ color: var(--cat-risky); }}
.score-cell.category-dont_use .score-num   {{ color: var(--cat-dont_use); }}

.muted {{ color: var(--text-3); font-style: italic; }}

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
  <div class="crumb"><span class="i18n-block en-block">repo-evals · all evaluated repos</span><span class="i18n-block zh-block">repo-evals · 所有评测过的仓库</span></div>
  <h1><span class="i18n-block en-block">All Evaluated Skills &amp; Repos</span><span class="i18n-block zh-block">已评测的所有 skill 和仓库</span></h1>
  <p class="lead">
    <span class="i18n-block en-block">Master index of every repo evaluated under repo-evals. Click into any row for the full bilingual dossier — claims, evidence, score breakdown, deployment notes, and the full benefits block (who / when / without / with). Sort by clicking a column header; filter by category or search by name.</span>
    <span class="i18n-block zh-block">repo-evals 评测过的所有仓库总目录。点任意一行进入完整双语 dossier —— claim、证据、分数明细、部署成本、完整 benefits 块（谁 / 什么时候 / 没它 / 有它）。点列头排序；按类别过滤或搜名字。</span>
  </p>

  <div class="tiles">
    <div class="tile"><div class="tile-label"><span class="i18n-block en-block">Total</span><span class="i18n-block zh-block">总数</span></div><div class="tile-value">{len(rows)}</div></div>
    <div class="tile cat-production"><div class="tile-label">🏭 <span class="i18n-block en-block">Production</span><span class="i18n-block zh-block">可用于生产</span></div><div class="tile-value">{cat_counts.get('production', 0)}</div></div>
    <div class="tile cat-available"><div class="tile-label">🛠 <span class="i18n-block en-block">Available</span><span class="i18n-block zh-block">可使用</span></div><div class="tile-value">{cat_counts.get('available', 0)}</div></div>
    <div class="tile cat-risky"><div class="tile-label">⚠️ <span class="i18n-block en-block">Risky</span><span class="i18n-block zh-block">有风险</span></div><div class="tile-value">{cat_counts.get('risky', 0)}</div></div>
    <div class="tile cat-dont_use"><div class="tile-label">🛑 <span class="i18n-block en-block">Don't use</span><span class="i18n-block zh-block">不可使用</span></div><div class="tile-value">{cat_counts.get('dont_use', 0)}</div></div>
  </div>

  <div class="controls">
    <input type="search" id="search-box" placeholder="Search repo / owner ..." />
    <button class="filter-pill active" data-category="">All</button>
    <button class="filter-pill" data-category="production">🏭 <span class="i18n-block en-block">Production</span><span class="i18n-block zh-block">可用于生产</span></button>
    <button class="filter-pill" data-category="available">🛠 <span class="i18n-block en-block">Available</span><span class="i18n-block zh-block">可使用</span></button>
    <button class="filter-pill" data-category="risky">⚠️ <span class="i18n-block en-block">Risky</span><span class="i18n-block zh-block">有风险</span></button>
    <button class="filter-pill" data-category="dont_use">🛑 <span class="i18n-block en-block">Don't use</span><span class="i18n-block zh-block">不可使用</span></button>
  </div>

  <table id="all-evals-table">
    <thead>
      <tr>
        <th>#</th>
        <th data-sort="repo"><span class="i18n-block en-block">Repo</span><span class="i18n-block zh-block">仓库</span></th>
        <th data-sort="one"><span class="i18n-block en-block">What it does</span><span class="i18n-block zh-block">做什么</span></th>
        <th data-sort="when"><span class="i18n-block en-block">When you'd use it</span><span class="i18n-block zh-block">什么时候用上</span></th>
        <th><span class="i18n-block en-block">Cost &amp; deps</span><span class="i18n-block zh-block">成本 / 依赖</span></th>
        <th data-sort="score" class="sort-active"><span class="i18n-block en-block">Score</span><span class="i18n-block zh-block">分数</span></th>
        <th><span class="i18n-block en-block">Dossier</span><span class="i18n-block zh-block">详细</span></th>
      </tr>
    </thead>
    <tbody>
      {''.join(table_rows)}
    </tbody>
  </table>

  <footer>
    <span class="i18n-block en-block">Generated by scripts/build_master_dashboard.py from repos/*/repo.yaml + claim-map.yaml. Re-run to refresh.</span>
    <span class="i18n-block zh-block">由 scripts/build_master_dashboard.py 从 repos/*/repo.yaml + claim-map.yaml 生成。重新跑脚本即可刷新。</span>
  </footer>
</main>

<script>
// Lang toggle
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

// Sort + filter + search
const tbody = document.querySelector('#all-evals-table tbody');
const allRows = Array.from(tbody.querySelectorAll('tr'));
let activeCategory = '';
let activeQuery = '';

function applyFilters() {{
  for (const row of allRows) {{
    const cat = row.dataset.category || '';
    const matchesCat = !activeCategory || cat === activeCategory;
    const text = row.textContent.toLowerCase();
    const matchesSearch = !activeQuery || text.includes(activeQuery);
    row.style.display = (matchesCat && matchesSearch) ? '' : 'none';
  }}
}}

document.querySelectorAll('.filter-pill').forEach(pill => {{
  pill.addEventListener('click', () => {{
    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeCategory = pill.dataset.category || '';
    applyFilters();
  }});
}});

document.querySelector('#search-box').addEventListener('input', e => {{
  activeQuery = e.target.value.trim().toLowerCase();
  applyFilters();
}});

// Click sort
document.querySelectorAll('th[data-sort]').forEach(th => {{
  th.addEventListener('click', () => {{
    document.querySelectorAll('th').forEach(h => h.classList.remove('sort-active'));
    th.classList.add('sort-active');
    const key = th.dataset.sort;
    const sorted = allRows.slice().sort((a, b) => {{
      if (key === 'score') return (+b.dataset.score) - (+a.dataset.score);
      if (key === 'repo' || key === 'one' || key === 'when') {{
        return a.textContent.localeCompare(b.textContent);
      }}
      return 0;
    }});
    sorted.forEach(r => tbody.appendChild(r));
  }});
}});
</script>
</body>
</html>
"""

    out = ROOT / "dashboard" / "all-evals.html"
    out.write_text(page)
    print(f"  wrote {out}")


if __name__ == "__main__":
    build()
