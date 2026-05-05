# obra/superpowers — static-checks run, 2026-05-05

## Findings

| Claim | Status | Note |
|---|---|---|
| 001 14 skills present + non-trivial | passed | 5/5 sampled 152–371 lines |
| 002 8-platform install | passed | 4 plugin dirs + 8 README install sections |
| 003 mature versioning | passed | v5.1.0 + RELEASE-NOTES.md present |
| 004 LICENSE | passed | MIT |
| 005 agent-facing docs | passed_with_concerns | CLAUDE.md (106) real; GEMINI.md (2) + AGENTS.md (0) thin |
| 006 tests | passed | 7 test dirs covering most platforms + skill triggering |
| 007 live agent workflow | untested | needs Claude Code session on a real feature task |

## Real findings

1. **AGENTS.md is empty (0 bytes), GEMINI.md is 2 lines.** For a
   project whose audience is *coding agents*, those two docs being
   thin is a polish gap. CLAUDE.md (106 lines) carries the load.
   Suggests Claude Code is the first-class platform; other agents
   are second-class. Worth disclosing.

2. **Mature project: v5.1.0 + RELEASE-NOTES + 7 test dirs.** Most
   "skill catalog" repos in the batch are v1.x with no tests. This
   one has had multiple major versions, ships release notes, and
   tests cover the install paths (claude-code / codex-plugin-sync /
   opencode) plus skill behaviors (brainstorm-server,
   skill-triggering, subagent-driven-dev). Strong maturity signal.

3. **CLAUDE.md is famous for being blunt.** Opens with "This repo
   has a 94% PR rejection rate" + "Almost every rejected PR was
   submitted by an agent that didn't read or didn't follow these
   guidelines". That's both a maintainer-style choice and a real
   anti-slop posture. Worth flagging to potential contributors.

4. **8-platform install is unusually broad.** Most multi-platform
   skills target 2-3; this one covers Claude Code (official
   marketplace) + Codex CLI + Codex App + Factory Droid + Gemini
   CLI + OpenCode + Cursor + GitHub Copilot CLI. The plugin config
   dirs are uneven though — Claude/OpenCode have 2 files each;
   Codex/Cursor only 1. Coverage isn't equal.

5. **The skill list reads like a software methodology, not a tool
   collection.** brainstorming → writing-plans → TDD →
   subagent-driven-development → verification-before-completion →
   finishing-a-development-branch → receiving-code-review. That's
   one coherent methodology pipeline, taught skill-by-skill.

## Verdict implication

6/7 static claims passed (one passed_with_concerns for non-Claude
docs being thin). 179K stars + recently active + MIT + mature
versioning + 7-dir test suite are all strong signals. Score
expected high — likely 80+ (🏭 Team-ready territory).
