# obra/superpowers — final verdict (2026-05-05)

## Repo

- **Name:** obra/superpowers · **Stars:** 178,762 · **License:** MIT
- **Archetype:** hybrid-skill · **Layer:** molecule
- **Version:** v5.1.0 · **Pushed:** 2026-05-04 (yesterday)

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 14 methodology skills | passed | All 5 sampled 152-371 lines |
| 002 8-platform install | passed | 4 plugin config dirs + 8 README install sections |
| 003 mature versioning | passed | v5.1.0 + RELEASE-NOTES.md |
| 004 LICENSE | passed | MIT |
| 005 agent-facing docs | passed_with_concerns | CLAUDE.md (106 lines) is real, but GEMINI.md (2) and AGENTS.md (0 bytes empty) are thin |
| 006 tests | passed | 7 test dirs covering install paths + skill triggering |
| 007 live agent workflow | untested | needs Claude Code session on a real feature task |

## Real findings

1. **AGENTS.md empty + GEMINI.md only 2 lines.** For a project whose
   audience is *coding agents*, that's an ironic gap. Claude Code is
   first-class; everything else is second-class. Worth disclosing in
   `watch_out`.

2. **Mature for a methodology bundle.** v5.1.0 + 7-dir test suite +
   release notes — most personal skill catalogs evaluated in this
   batch are v1.x with no tests. This one has been iterated on
   significantly.

3. **The skill list reads as a coherent methodology pipeline.**
   brainstorming → writing-plans → TDD → subagent-driven-development
   → verification-before-completion → finishing-a-development-branch
   → receiving-code-review. That's one opinionated software-engineering
   approach, taught skill-by-skill — not a random utilities catalog.

4. **CLAUDE.md is famously blunt.** "94% PR rejection rate" + "slop
   PRs" naming and shaming. That's a maintainer culture choice — fits
   the anti-slop posture of the methodology, but contributors should
   know the bar before submitting.

5. **8-platform install with uneven coverage.** Claude / OpenCode get
   2-file plugin configs each; Codex / Cursor only 1 file each.
   README lists 8 install paths but the depth-of-integration varies.
   Verify your platform's plugin contract is what you expect before
   relying on a non-Claude install.

## Why the score lands where it does

- 6/7 static claims passed; 1 passed_with_concerns
- 179K stars puts ecosystem at +12 (50K+ band)
- Recently active (+5) + release_pipeline=2 (+5) → +10 maintainer
- Molecule layer +0
- LICENSE present, no penalties

Predicted score: ~85 — solidly **🏭 Team-ready** territory.

## Path to ⭐ Recommend

1. Fill AGENTS.md and GEMINI.md properly (not 0/2 lines).
2. Run a logged live-agent scenario in Claude Code — kick off a
   feature with brainstorming, watch superpowers chain through
   writing-plans → TDD → subagent-driven-development → verify.
3. Multi-evaluator coverage on a non-Claude platform (e.g. Cursor)
   to validate the thinner plugin configs work.
4. Update claim-007 to passed; re-run verdict_calculator.

## Recommended

```yaml
status: evaluated
```
