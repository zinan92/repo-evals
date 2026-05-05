# follow-builders — final verdict (2026-05-05)

## Repo

- **Name:** zarazhangrui/follow-builders
- **Branch:** main@HEAD · **Stars:** 3,689
- **Archetype:** hybrid-skill · **Layer:** molecule

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 SKILL.md ≥ 200 lines | passed | 466-line SKILL.md with frontmatter |
| 002 5 prompt files | passed | All present, 1.0–2.6 KB each |
| 003 source list = README | passed | config/default-sources.json: 25 X + 6 podcasts + 2 blogs |
| 004 Node.js pipeline | passed | generate-feed (38 KB) + prepare-digest (5 KB) + deliver (7 KB) |
| 005 bilingual | passed | README.zh-CN.md + prompts/translate.md |
| 006 LICENSE | **failed** | HTTP 404 |
| 007 live e2e | untested | needs Claude Code session + delivery channel |

## Real findings

1. **No LICENSE** — same gap as `codebase-to-course`. Author-level
   pattern. Easy upstream fix.

2. **The "no API keys needed" architecture is clever.** The user-facing
   skill is light because Zara runs a central Node.js pipeline that
   pre-fetches and summarizes everything. Trade-off: every user is
   tightly coupled to her server uptime — single point of failure
   with no documented SLA or fallback.

3. **466-line SKILL.md is unusually thorough.** Most skills are
   100-200 lines. The depth here suggests serious investment in
   making the conversational setup work without config files.

4. **38 KB `generate-feed.js`** — this is real engineering, not a
   demo. The maintainer has invested in the central pipeline.

## Why not higher

- LICENSE missing (-5 score, claim-006 failed).
- Live e2e not logged (molecule layer cap; central pipeline single
  point of failure means a live test is more important than usual).

## Path forward

1. Add LICENSE to repo root.
2. Run a real setup + delivery scenario, ideally with Telegram bot
   token, log first-digest delivery.
3. Test "central server unreachable" scenario; verify error surfaces
   to the user (not silent skip).
4. Update claim-006 + claim-007.
