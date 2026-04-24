---
name: repo-evals
description: Runs a claim-first evaluation of any open-source repo, tool, or skill against its own README promises and returns a bucketed verdict (🔴 unusable / ⚪ usable / 🟡 reusable / 🟢 recommendable) backed by evidence. Renders a product-page HTML for the user to read at a glance. Use this skill whenever the user says "eval 一下这个 repo", "eval 这个项目", "eval 这个 skill", "evaluate this repo", "评测一下", "试用这个 repo", "这个东西好不好用", or pastes a GitHub URL and asks whether to adopt it. Also use when comparing two repos on the same dimensions. Do not wait for explicit "please use repo-evals" — trigger on the intent, not the skill name.
---

# repo-evals

This is both a **skill** (so Claude Code triggers it on the right user phrases) and the full **framework** it runs. Install the skill as a symlink:

```bash
git clone https://github.com/zinan92/repo-evals.git ~/work/agents-co/wendy/repo-evals
ln -s ~/work/agents-co/wendy/repo-evals ~/.claude/skills/repo-evals
```

`git pull` on the repo updates both the scripts and the skill.

## ⚠️ Standing rule — output must be user-facing, not engineer-facing

Every artifact produced by this skill is a **product page about the evaluated repo**, not a test report. The primary reader is a non-technical adopter asking "should I use this?". The technical reviewer is a secondary reader whose view is collapsed by default.

Enforce this at three levels:

1. **`repo.yaml.product_view`** — MUST fill `one_liner`, `best_for`, `watch_out` with bilingual `{en, zh}` values. Describe outcomes, not implementation. Bad: "Tauri desktop app managing AI coding agent skills across 28 platforms". Good: "从一个桌面应用管理 28 个 AI 编程工具的技能库 — 技能改一处，所有工具同步更新".
2. **Each `claim`** — MUST add `user_icon` (emoji), `user_title` ({en, zh}), `user_description` ({en, zh}). The technical `title` / `statement` / `evidence_needed` stay for reviewers. Bad user_title: "所有 install 产出同一个 shape（symlink → central）". Good: "一处修改，多处同步".
3. **HTML verdict** — Technical details (ceilings, derivation diagram, claims table, run metrics, raw markdown) MUST be inside `<details>` and collapsed by default. Above-the-fold is: one-liner + bucket + best_for + watch_out + capability cards.

Write the user-facing one-liner FIRST, before claims. Let the claims fall out of it. If a claim can't be phrased as a user outcome, either rephrase it or demote it below `critical`/`high` priority.

## Four verdict buckets

| Emoji | Name | Meaning |
|---|---|---|
| 🔴 | `unusable` | Core claims fail or pass only by accident |
| ⚪ | `usable` | Works once, low confidence |
| 🟡 | `reusable` | Stable across multiple real scenarios |
| 🟢 | `recommendable` | Boundaries clear, safe to share with others |

The final bucket MUST come from `scripts/verdict_calculator.py`, never from judgement.

## Workflow (one screen)

Run from the skill / framework directory — the scripts resolve `repos/<slug>/` relative to themselves.

```bash
cd $(dirname $(readlink -f ~/.claude/skills/repo-evals))   # or wherever you cloned
export EVAL_RUNNER=cc EVAL_AGENT="Claude Code" EVAL_MODEL=<model-id>

# 1. Scaffold
scripts/new-repo-eval.sh <owner>/<repo> --archetype <archetype>

# 2. Claims (hand-edit then rename .draft → final)
scripts/extract_claims.py /path/to/target -o repos/<slug>/claims/claim-map.yaml.draft

# 3. Plan — reference every claim by id (claim-001, claim-002, ...)
$EDITOR repos/<slug>/plans/<date>-eval-plan.md

# 4. Eval harness
scripts/new-eval-harness.sh <slug>
scripts/run_evals.py <slug>                # fills results_by_claim + metrics
scripts/run_evals.py <slug> --baseline     # with/without comparison

# 5. Trigger test (when target is a skill)
scripts/trigger_test.py /path/to/skill

# 6. Coverage + verdict
scripts/coverage_gap_detector.py repos/<slug>
scripts/verdict_calculator.py repos/<slug>/verdicts/<date>-verdict-input.yaml --md

# 7. HTML verdict (what the user actually reads)
scripts/render_verdict_html.py <slug> --lang zh   # or --lang auto (default) / en
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

## Rules

- **Do not guess the bucket** — `verdict_calculator.py` is authoritative.
- **Do not install untrusted apps on the live system** to test claims. When runtime would touch the user's active configuration (skill dirs, browser profiles, API credentials), skip the claim, record `skip_reason`, and accept the archetype ceiling cap.
- **Every run must have provenance** — `scripts/new-run.sh` captures it from `EVAL_*` env vars.
- **Evidence paths are relative** to the run directory. No `/tmp/...` in committed summaries.
- **Prefer primary-source evidence** (artifacts with checksums, source greps with line numbers) over screenshots over subjective impressions.

## Output to user

When done, deliver in order:

1. Bucket emoji + name + confidence (verbatim from calculator)
2. Ceiling reasons + blocking issues
3. A two-line plain-English verdict
4. Path to the rendered HTML (open it, don't just mention it)
5. Offer to commit + push the `repos/<slug>/` artifacts to the repo-evals fork

## Deeper docs

Read these from the same directory, not by re-deriving:

- `ROADMAP.md` — upcoming changes to the framework
- `docs/FRAMEWORK.md` — claim-first philosophy
- `docs/VERDICT-BUCKETS.md` — bucket definitions
- `docs/VERDICT-CALCULATOR.md` — rules + ceiling logic
- `docs/PROVENANCE.md` — evidence capture
- `docs/COVERAGE-GAP-DETECTOR.md` — coverage rules
- `archetypes/<name>/archetype.yaml` — per-archetype dimensions
