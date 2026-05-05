# zinan92/doc-driven-dev-workflow — final verdict (2026-05-05)

## Repo

- **Name:** zinan92/doc-driven-dev-workflow · **Stars:** 1
- **Archetype:** pure-cli · **Layer:** **molecule** · **Domain:** development
- **License:** **missing** (README implies open distribution; no LICENSE / COPYING file at root)
- **Pushed:** 2026-03-27 (~5 weeks ago, recent enough to count as active per 90-day window)
- **Visible history:** 1 commit ("docs: productize README")

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 5 phases × 22 stages exact | passed | docs/canonical-workflow.json v2.0; counts verified |
| 002 6 Python scripts non-trivial | passed | 102-251 lines each, 921 lines total |
| 003 test suite passes | passed | 52/52 pytest tests in 0.2s |
| 004 frontend dashboard real React/TS code | passed | full Vite + React 19 project, ~80 KB TypeScript |
| 005 docs/ substantive | passed | development-workflow.md + build-anything-workflow.md + 6-file workflow-driven-developer/ subdir |
| 006 examples show real task layout | passed | 2 example tasks with status.md + decision-log.md + handoffs/ + system/state.json |
| 007 LICENSE | **failed** | no LICENSE file at root; same defect as karpathy/autoresearch + earlier repo-evals |
| 008 multilingual README | passed_with_concerns | README.md is CN-only; workflow JSON / script names / log formats are EN, so the system is bilingual *in practice* but not by README convention |
| 009 live e2e (Codex + Claude Code drives a real task) | **untested** | needs a logged session running scaffold → all 22 stages → done |
| 010 workflow_guard enforces state transitions | passed | 251-line workflow_guard.py + tests/test_workflow_guard.py cover rejection paths |

## Real findings

1. **The architecture is ambitious and the scaffolding is real.** 921 lines
   of Python across 6 scripts + 52 passing tests + a working React 19 +
   Vite + Vitest observer dashboard + a 22-stage canonical JSON spec.
   This is not a "I had an idea" repo; it's a "I built a working
   skeleton" repo.

2. **The role split is the load-bearing design assumption.** README
   declares Codex = planner / reviewer, Claude Code = coder. The
   workflow_guard.py + state-machine + decision-log.md infrastructure
   only pays off if a real Codex + Claude Code pairing actually drives
   a 22-stage task to maintenance. We can't test that statically.

3. **No LICENSE is the obvious gap.** The whole framework is meant to
   be cloned into someone's repo (or used as a submodule). Without a
   LICENSE file, every adopter has a legal question to answer first.
   One commit fixes this.

4. **README is Chinese-only but the *system* is bilingual.** Stage IDs
   (`clarify_objective`, `gate_major_phase`, `final_revision`) are
   English. Script names are English. Log formats are English. The
   only Chinese surface is the README and some prose docs. Non-CN
   readers can use the framework — they just need to read CLAUDE.md
   instead of README.md.

5. **Two example tasks are non-placeholder.** examples/example-task/
   and examples/medium-example-task/ both ship with a real status.md
   showing actual workflow state ("current stage:
   `update_backlog_and_debt`, current owner: `codex`, latest
   conclusion: ..."). This is harder than it looks — most "example
   project" repos ship a 3-line README and call it done.

6. **Closer in philosophy to obra/superpowers than to most workflow
   tooling, but at a different maturity.** Both bet "explicit
   methodology beats ad-hoc chat-driven coding". superpowers ships
   14 skills + 8-platform install + 179K stars + v5.1.0. doc-driven
   is single-author v0.1.0 with 1 star. Same family, different tier.
   The `similar_repos` block in the dossier cross-links them and
   explains the trade-off honestly.

## Why the score lands where it does

Actual breakdown (from verdict_calculator):

- base                  +40
- static_eval           +11 (3 critical passed +15; 1 critical failed −10; 1 critical untested −2; 4 high passed +8; rest)
- maintainer_evidence   +10 (recent_active +5, eval_discipline=2 +5)
- ecosystem             +0  (1 star)
- layer_bonus           +0  (molecule)
- penalties             −2  (no LICENSE, small-repo tier)
- ────────────────────
- **59 / 🛠 Available · 🧪 Try once**

The big swing is the failed critical LICENSE claim: −10 in static_eval
plus −2 in penalties (a single −12 cost from one missing file). Fixing
that one file would lift the score by ~+15 (from −10 to +5 in static_eval
+ removing the −2 penalty) → ~74. Layer the live e2e on top → ~80.

The honest read: a thoughtful, well-engineered single-author framework
with strong static evidence + zero live evidence. Author can use it
confidently; strangers should run a small task as proof-of-concept
before depending on it.

## Path to higher score

1. **Add LICENSE file** (claim-007 fix). +2 from penalty + clearer
   contribution path. Trivial commit.
2. **Run one logged real task end-to-end.** Scaffold a small feature
   on a real repo, drive it through all 22 stages with Codex + Claude
   Code, save the resulting tasks/TASK-.../ + run-log.jsonl. Updates
   claim-009 to passed. Pushes 70-72 → 80+.
3. **Get a second evaluator.** Have someone else clone + scaffold a
   task on their own machine + send back the resulting task folder.
   Validates the workflow doesn't depend on Wendy's tribal knowledge.
4. **Add an English README** (or a translation block at the top of
   the existing CN one). Raises claim-008 from passed_with_concerns
   to passed.

## Recommended

```yaml
status: evaluated
```
