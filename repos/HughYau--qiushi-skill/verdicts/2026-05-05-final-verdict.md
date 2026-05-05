# qiushi-skill — final verdict (2026-05-05)

## Repo

- **Name:** HughYau/qiushi-skill · **Stars:** 3,007
- **Archetype:** hybrid-skill (reclassified from default prompt-skill)
- **Layer:** molecule
- **License:** MIT · **Language:** JavaScript · **Pushed:** 2026-05-01

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 10 methodology skills | passed | All 10 SKILL.md exist (HTTP 200) |
| 002 7-platform install configs | passed | each platform has dedicated config dir with files |
| 003 npm + bin | passed | 307-line CLI; npm registry has v1.4.1 |
| 004 bilingual + cross-platform tests | passed | EN README + bash + PowerShell validators |
| 005 original-texts depth | passed_with_concerns | 1 of 3 sampled is empty (arming-thought/original-texts.md = 0 bytes) |
| 006 LICENSE | passed | MIT |
| 007 live agent workflow | untested | needs real Claude Code / OpenClaw session |

## Real findings

1. **`arming-thought/original-texts.md` is empty (0 bytes).** The
   other two sampled skills have ~2 KB of classical-text excerpts.
   arming-thought is the *总原则* (overarching principle, "实事求是")
   — the most important skill — and it's missing its references.
   One-line upstream fix.

2. **Genuinely cross-platform install path.** 7 dedicated
   `.<platform>/` config dirs (Claude Code / Codex / Cursor / Hermes
   / NanoBot / OpenClaw / OpenCode). Most personal skill catalogs
   target 1-3; this one cared enough to ship 7.

3. **Cross-platform test discipline.** validate.sh (216 lines) +
   validate.ps1 (212 lines) — Windows install path is actually
   tested, not just "should work".

4. **Methodology granularity is honest.** 10 distinct methodologies
   are genuinely different reflexes (contradiction analysis vs
   investigation-first vs protracted-strategy). User picks 2-3 that
   match a workflow; not 10 pieces of one skill.

5. **Cultural / branding consideration.** Methodology rooted in
   Mao-era dialectical materialism. README explicitly disclaims
   ("this is methodology, not politics"), but corporate adopters
   should think before installing in a public skill catalog.
   Worth surfacing in `watch_out`.

## Why the score lands where it does

Predicted ~70 (🛠 Self-use OK). Drivers:
- 7 SKILL.md claims passed (mostly +5 each, capped at +30)
- claim-005 passed_with_concerns
- maintainer evidence: release_pipeline=2 (+5) + multilingual (+2) + recently_active (+5) = +12 maintainer
- ecosystem: 3K stars → +3
- layer_bonus: molecule → 0
- penalties: 0 (MIT)

## Path forward

1. Fill `skills/arming-thought/original-texts.md` (the most important
   skill is missing references).
2. Run a live agent workflow on a complex problem; verify the agent
   actually invokes contradiction-analysis (or another methodology)
   rather than going straight to the answer.
3. Log under `runs/<date>/run-live-agent/`.
