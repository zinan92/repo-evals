# anthropics/skill-creator — final verdict (2026-05-05)

## Repo

- **Slug:** anthropics/skill-creator
- **Actual location:** github.com/anthropics/skills/tree/main/skills/skill-creator
- **Archetype:** hybrid-skill · **Layer:** molecule
- **Parent stars:** 128,303 · **License:** Apache 2.0 (in subdir) · **Pushed:** 2026-05-03

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 SKILL.md substantive + frontmatter | passed | 485 lines, multi-intent triggers |
| 002 9 scripts non-trivial | passed | 7 of 9 scripts 102–401 lines (utils intentionally small) |
| 003 3 sub-agent prompts | passed | analyzer 274 / comparator 202 / grader 223 lines |
| 004 eval-viewer real | passed | 471-line Python + 1,325-line HTML |
| 005 schemas.md depth | passed | 430 lines of JSON schemas |
| 006 LICENSE in subdir | passed | Apache 2.0 (201 lines) |
| 007 live "create a skill" e2e | untested | needs Claude Code + Anthropic API |

## Real findings

1. **Eval-discipline = 3, the only repo in the batch to earn it.**
   This skill IS an eval framework. It ships:
   - `run_eval.py` (310 lines)
   - `run_loop.py` (328 lines, iterative improvement)
   - `aggregate_benchmark.py` (401 lines, variance analysis)
   - 3 LLM grader/comparator/analyzer agents
   - 1,325-line HTML viewer for browsing results
   No other repo evaluated has even half this depth on its own
   output quality. This is the canonical example for the
   `eval_discipline_score=3` field.

2. **Heavyweight by design.** 485-line SKILL.md + ~70 KB Python +
   1.3K-line HTML viewer is an unusual amount of surface for a
   single skill. The scope (create / modify / eval / benchmark /
   optimize description) genuinely needs that much, but users
   evaluating "should I install this for a 50-line skill?" should
   know the overhead in advance — covered in `watch_out`.

3. **Sub-directory of a catalog (not a standalone repo) is a
   first-class case for the framework.** All other 18 repos in this
   batch are standalone; skill-creator lives inside
   `anthropics/skills/skills/skill-creator/`. The framework handled
   it gracefully — repo_url points to the subtree, parent's stars
   inherited as ecosystem signal, LICENSE bundled in subdir
   sufficed.

4. **Apache 2.0 inside the subdir is a great pattern.** Many
   in-house Anthropic projects ship without LICENSE; here it's
   self-contained at the skill level, so anyone copying just this
   one folder still has clear legal cover. Worth recommending as
   the default pattern for sub-skills inside catalog repos.

5. **3 sub-agents implement actually-honest evaluation:**
   - **comparator** is *blind* — doesn't know which version it's
     judging
   - **grader** scores against documented expectations, not vibes
   - **analyzer** is post-hoc — only looks at results, doesn't
     write or judge live runs
   That's the right shape for variance-aware skill evaluation.

## Why the score is high

This is the exemplar repo for what the score model rewards:

- Static evidence: 6/7 claims passed → near-cap static eval points
- Maintainer evidence: eval-discipline=3 (+5) + recently_active (+5) → +10 of +15
- Ecosystem: 128K-star parent (+12)
- Layer bonus: molecule (+0)
- Penalties: 0

Predicted score: ~89/100, **🏭 Team-ready** territory.

## Why not higher

`recommendable` (90+) requires multi-evaluator coverage and live e2e
evidence. We have neither. claim-007 (live skill-creation flow) is
the gating evidence — until someone runs `run_loop.py` end-to-end
and logs the results, the dossier honestly says "team-ready" not
"recommend".

## Path to ⭐ Recommend

1. Run a happy-path scenario: in Claude Code, ask the skill to
   create a new skill, let it walk through draft → eval → iterate.
   Log in `runs/<date>/run-live-skill-creation/business-notes.md`.
2. Run a benchmark variance scenario: invoke
   `scripts/aggregate_benchmark.py` on an existing skill with ≥10
   trials; verify variance numbers + viewer.html report.
3. Multi-evaluator: have a second person on a different machine run
   the same flow and confirm reproducibility.
4. Update claim-007 to passed; re-run verdict_calculator.

## Recommended

```yaml
status: evaluated
```
