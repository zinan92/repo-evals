# anthropics/skill-creator — static-checks run, 2026-05-05

## TL;DR

The most evidence-rich skill in the entire eval batch. Every static
claim passed, and uniquely earns `eval_discipline_score=3` because it
literally ships a full LLM-output evaluation harness.

## Findings

| Claim | Status | Note |
|---|---|---|
| 001 SKILL.md substantial + frontmatter | passed | 485 lines, multi-intent triggers |
| 002 9 scripts non-trivial | passed | 7 scripts 102–401 lines |
| 003 3 sub-agent prompts | passed | 274 / 202 / 223 lines |
| 004 eval-viewer real | passed | 471 lines Python + 1,325 lines HTML |
| 005 schemas.md substantial | passed | 430 lines of JSON schemas |
| 006 LICENSE | passed | Apache 2.0 in skill subdir |
| 007 live "create a skill" e2e | untested | needs Anthropic API + Claude Code session |

## Real findings

1. **eval-discipline=3 is rare and well-earned.** Of 19 repos in the
   batch, this is the only one with a real LLM-output-quality
   evaluation harness. It ships:
   - `run_eval.py` (310 lines): runs evals
   - `run_loop.py` (328 lines): iterative improvement loop
   - `aggregate_benchmark.py` (401 lines): multi-run variance analysis
   - 3 LLM grader/comparator/analyzer agents in `agents/`
   - 1,325-line `viewer.html` for browsing eval results
   This isn't a "skill that mentions evals"; it's a skill **about**
   evaluating skills, with the infrastructure to do so.

2. **Heavyweight, but justifies its weight.** 485-line SKILL.md +
   ~70 KB of Python + 1.3K-line HTML viewer is a lot to absorb for
   a "skill that creates skills". But the scope it claims (create /
   modify / eval / benchmark / optimize description) genuinely needs
   that much. Worth flagging in `watch_out` so users with simpler
   needs don't reach for this prematurely.

3. **Sub-directory of a catalog, not a standalone repo.** Living
   inside `anthropics/skills/skills/skill-creator/` means:
   - install path is "clone catalog + cp folder", not `npm install`
   - parent's 128K stars are a fair ecosystem signal (the catalog IS
     what users star)
   - LICENSE is in the skill subdir (Apache 2.0) — does not depend on
     parent
   The framework was originally designed for whole repos, but this
   eval works fine treating the subdir as the unit.

4. **Apache 2.0 in subdir is reassuring.** Many in-house Anthropic
   projects ship without LICENSE. This skill bundles its own.

5. **3 sub-agents do honest blind comparison.** Reading the
   prompts: analyzer is post-hoc, comparator is **blind** (doesn't
   know which version it's evaluating), grader scores against
   expectations. That's the right shape for variance-aware skill
   benchmarking.

## What is still untested (claim-007)

End-to-end skill creation:

1. Install: clone anthropics/skills + copy `skill-creator/` into
   `~/.claude/skills/`.
2. In Claude Code, say "create a skill that turns YouTube videos
   into mind maps".
3. Verify the agent walks through draft → eval → iterate per
   SKILL.md's documented process.
4. Run one iteration of `run_loop.py`; verify grader/comparator/analyzer
   all fire and produce a viewer.html report.
5. Log under `runs/<date>/run-live-skill-creation/`.

Token budget: each loop round invokes ≥4 LLM calls (skill execution +
3 agents). Budget accordingly before kicking off.

## Verdict implication

All 6 static claims passed. eval_discipline=3 + Apache 2.0 + recently
active + 128K-star parent catalog + atom contract... wait no it's
molecule (multi-capability). Even at molecule, score should be
unusually high — this is the exemplar repo for the framework.
