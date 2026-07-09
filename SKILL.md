---
name: repo-evals
description: Runs a claim-first evaluation of any open-source repo, tool, or skill against its own README promises and renders an editorial dossier (HTML one-pager) with a 0-100 score, 4-category verdict (🏭 Production / 🛠 Available / ⚠️ Risky / 🛑 Don't use), and prescriptive next-steps. Use this skill whenever the user says "eval 一下这个 repo", "eval 这个项目", "eval 这个 skill", "evaluate this repo", "评测一下", "试用这个 repo", "这个东西好不好用", or pastes a GitHub URL and asks whether to adopt it. Also use when comparing two repos on the same dimensions, or auditing a repo's claim-vs-reality gap. Do not wait for explicit "please use repo-evals" — trigger on the intent, not the skill name.
---

# repo-evals

Both a **skill** (so compatible coding agents trigger it on the right user phrases)
and the full **framework**. Install from GitHub:

```bash
npx skills add zinan92/repo-evals -g
```

For local development, clone wherever you keep repos and symlink that checkout:

```bash
git clone https://github.com/zinan92/repo-evals.git ~/repo-evals
ln -s ~/repo-evals ~/.claude/skills/repo-evals
```

`git pull` updates the local framework and the symlinked skill together.

## ⚠️ Standing rule — output is a product page, not a test report

Every artifact is a **dossier about the evaluated repo** — read by a non-technical adopter asking "should I use this?". Engineers are a secondary reader and their view is collapsed.

Three places where this is enforced:

1. **`repo.yaml`** — must fill the full dossier schema (see template). Missing fields = empty sections in the HTML. Bad: `one_liner: "Tauri desktop app for managing skills"`. Good: `one_liner: "从一个桌面应用管理 28 个 AI 编程工具的技能库 — 一处修改，所有工具同步更新"`.
2. **Each `claim`** — `user_icon` (emoji), `user_title` ({en, zh}), `user_description` ({en, zh}). Phrase as user outcomes. Technical `title` / `statement` / `evidence_needed` stay for reviewers.
3. **HTML dossier** — technical details (claim ledger, run metrics, derivation, raw markdown) are inside `<details>` and collapsed. Above-the-fold: score band + decision card + benefits cards.

Write `product_view.one_liner` FIRST, before claims. Let claims fall out of it. If a claim can't be phrased as a user outcome, demote it below `critical`/`high`.

## Score model (0-100, additive)

The 4-bucket model is gone. Every dossier shows an explicit 0-100 score:

```
SCORE_BASE        = 40   (project is real, not archived, has license)
+ static claims   ±30    (claim pass/fail + priority)
+ maintainer      ±15    (release_pipeline + eval_discipline + recently_active)
+ ecosystem       ±15    (stars band + multilingual_readme)
+ layer_bonus     ±?     (atom/molecule/compound — different ceilings)
- license_penalty       (no LICENSE — penalty scales with stars)
```

**Display: 4 categories** (filter pills + dashboard):

| Score | Category | Emoji | EN / ZH |
|---|---|---|---|
| 80–100 | `production` | 🏭 | Production-ready / 可用于生产 |
| 50–79  | `available`  | 🛠 | Available / 可使用 |
| 30–49  | `risky`      | ⚠️ | Risky / 有风险 |
| 0–29   | `dont_use`   | 🛑 | Don't use / 不可使用 |

**Underneath: 6 tiers** for fine-grained sort:

| Score | Tier | Emoji | EN / ZH |
|---|---|---|---|
| ≥90 | `recommend` | ⭐ | Recommend / 公开推荐 |
| ≥80 | `team`      | 🏭 | Team-ready / 团队就绪 |
| ≥65 | `self`      | 🛠 | Self-use OK / 自用 OK |
| ≥50 | `try`       | 🧪 | Try once / 试一下 |
| ≥30 | `risky`     | ⚠️ | Risky / 慎用 |
| <30 | `broken`    | 🛑 | Don't use / 别用 |

Both the score and category are computed by `scripts/verdict_calculator.py` — never by judgement. The raw score chooses the tier, then the reader-facing category is capped by the final bucket ceiling. Don't write a category into `repo.yaml.current_bucket` and expect it to stick; the calculator overwrites it.

## Dossier sections + which `repo.yaml` field drives each

| HTML section | Driven by |
|---|---|
| 决策快照 (Decision Card) | `current_bucket` + score, derived |
| 它是哪一类? | `business_category` + `use_case_tags` |
| 在这条工作流里 | `workflow_placements[]` |
| 它可用性如何? | score → tier band + 检查过的 vs 还差哪些 |
| 提升评分的下一步 | `product_view.next_step` (bilingual) |
| 它到底能帮你解决什么 | `product_view.{persona, scenario, without_this, with_this, examples[]}` |
| 怎么用 | `product_view.how` + `deployment` |
| 依赖什么外部服务 | `third_party_services[]` |
| 类比的同类 repo | `similar_repos[]` |
| Atom / Molecule / Compound | `layer` + `workflow_diagram.why_layer` |
| 维护层 (trust strip) | `stars`, `recently_active`, `has_license`, `multilingual_readme`, `release_pipeline_score`, `eval_discipline_score` |

If a field is absent the section disappears. **Check `templates/repo/repo.yaml` for the full schema** — every commented-out line is a section the dossier could render.

## Workflow (one screen)

Run from the framework directory.

```bash
cd $(dirname $(readlink -f ~/.claude/skills/repo-evals))
export EVAL_RUNNER=cc EVAL_AGENT="Claude Code" EVAL_MODEL=<model-id>

# 1. Scaffold
scripts/new-repo-eval.sh <owner>/<repo> --archetype <archetype>

# 2. Fill repo.yaml dossier fields FIRST (one_liner → next_step → claims fall out)
$EDITOR repos/<slug>/repo.yaml          # full dossier — see template comments

# 3. Claims (extractor seeds, you finalize)
scripts/extract_claims.py /path/to/target -o repos/<slug>/claims/claim-map.yaml.draft
$EDITOR repos/<slug>/claims/claim-map.yaml

# 4. Plan — reference each claim by id
$EDITOR repos/<slug>/plans/<date>-eval-plan.md

# 5. Eval harness (when applicable)
scripts/new-eval-harness.sh <slug>
scripts/run_evals.py <slug>
scripts/run_evals.py <slug> --baseline   # with/without comparison

# 6. Trigger test (only when target is a skill)
scripts/trigger_test.py /path/to/skill

# 7. Coverage + verdict (calculator computes score from repo.yaml + claims)
scripts/coverage_gap_detector.py repos/<slug>
scripts/verdict_calculator.py repos/<slug>/verdicts/<date>-verdict-input.yaml --md
# (when no sidecar verdict-input exists, render_verdict_html.py derives one
#  from repo.yaml + claim-map.yaml — that's the path we usually take)

# 8. Publish dossier (the HTML the user actually reads) + refresh dashboard
scripts/publish_eval.py <slug> --lang zh          # accepts owner--repo or owner/repo
```

## Archetype picker

| If target is... | Use |
|---|---|
| CLI tool with deterministic output | `pure-cli` |
| SKILL.md only, no code | `prompt-skill` |
| SKILL.md + scripts/templates | `hybrid-skill` |
| Wraps external platforms behind a unified interface | `adapter` |
| Coordinates multiple sub-systems | `orchestrator` |
| HTTP or service endpoint | `api-service` |
| Wraps an MCP server with workflow guidance | `mcp-enhancement` |

When unsure, read `archetypes/<name>/archetype.yaml` for that archetype's evaluation dimensions.

## Layer picker (drives layer_bonus + core_layer_tested)

| Target shape | Layer | core_layer_tested without live run? |
|---|---|---|
| Single user-facing capability, deterministic, no orchestration | `atom` | yes |
| Fixed pipeline of atoms, no LLM-runtime routing | `molecule` | no — needs live e2e |
| LLM-runtime routing, dynamic agent dispatch, multi-step plan generation | `compound` | no — needs live e2e |

Atom can score full marks from static eval. Molecule + compound have a ceiling until a live run is logged. Don't claim atom for something that's actually a molecule — the calculator catches it via the deferred-live-run check.

## Re-eval policy

If a `repos/<slug>/` already has a verdict from a prior date:

- A new eval with **the same questions** (ran the same claims) → update files in place, bump `last_evaluated`.
- A new eval with **different questions** (new angle: marketing-vs-reality, security audit, etc.) → either (a) extend the existing claim map and re-render, or (b) create a separate dated `verdicts/<date>-…` set and surface the conflict to the user. Don't silently overwrite.
- **Always check `last_evaluated` and the existing claim-map BEFORE scaffolding.** If a recent eval exists, ask whether to extend or re-eval.

## Rules

- **Never guess the score / category** — `verdict_calculator.py` + `render_verdict_html.py` are authoritative.
- **Don't install untrusted apps on the live system** to test claims. When the runtime would touch user config (skill dirs, browser profiles, API credentials), skip the claim, record `skip_reason` on the claim, and accept the layer ceiling cap. Source-grep + GitHub API + isolated subprocess are fine substitutes.
- **Every run must have provenance** — `scripts/new-run.sh` captures it from `EVAL_*` env vars.
- **Evidence paths are relative** to the run directory. No `/tmp/...` in committed summaries.
- **Prefer primary-source evidence** (artifacts with checksums, source greps with line numbers, `gh api` JSON dumps) over screenshots over impressions.
- **`repo.yaml` is the input to the dossier renderer.** Filling only `product_view.{one_liner, best_for, watch_out}` produces a stub HTML. Fill the full schema or the dossier is empty.
- **`has_license` is a fact, not a vibe.** Verify with `gh api repos/<owner>/<repo>` (`license` field) AND `gh api .../contents/LICENSE`. README badges lie.

## Output to user when done

In order:

1. Score (0-100) + category emoji + tier (verbatim from calculator)
2. Top 3 score deltas (what cost or earned the most points)
3. Two-line plain-English verdict
4. Path to the rendered HTML — open it (don't just mention it)
5. Offer to commit + push the `repos/<slug>/` artifacts to the repo-evals fork

## Deeper docs (read from disk, not from training)

- `ROADMAP.md` — upcoming changes
- `docs/FRAMEWORK.md` — claim-first philosophy
- `docs/VERDICT-BUCKETS.md` — bucket history (still referenced in some old evals)
- `docs/VERDICT-CALCULATOR.md` — scoring rules + ceiling logic
- `docs/LAYERS.md` — atom/molecule/compound semantics
- `docs/PROVENANCE.md` — evidence capture
- `docs/COVERAGE-GAP-DETECTOR.md` — coverage rules
- `archetypes/<name>/archetype.yaml` — per-archetype dimensions
- `templates/repo/repo.yaml` — full dossier schema (every field commented)
