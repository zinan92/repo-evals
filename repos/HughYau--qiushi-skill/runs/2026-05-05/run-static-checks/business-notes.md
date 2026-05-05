# qiushi-skill — static-checks run, 2026-05-05

## Findings

| Claim | Status | Note |
|---|---|---|
| 001 10 skills present | passed | all SKILL.md HTTP 200 |
| 002 7-platform configs | passed | each platform has its own config dir with files |
| 003 npm package + bin | passed | 307-line CLI; npm v1.4.1 matches package.json |
| 004 i18n + tests | passed | 165-line EN README + 216-line bash + 212-line PS1 validators |
| 005 original-texts depth | **passed_with_concerns** | 1 of 3 sampled is **empty** (arming-thought/original-texts.md = 0 bytes) |
| 006 LICENSE | passed | MIT |
| 007 live agent workflow | untested | needs Claude Code session on a real complex problem |

## Real findings

1. **arming-thought/original-texts.md is empty (0 bytes).**
   The other two sampled skills have ~2 KB of original quotations
   each. arming-thought is the *总原则 (overarching principle)* —
   the most important skill in the taxonomy — and it's the one
   missing references. Easy upstream fix.

2. **7-platform install support is unusually broad.** Most skill
   catalogs target 1-3 platforms; this one ships dedicated config
   dirs for Claude Code / Codex / Cursor / Hermes / NanoBot /
   OpenClaw / OpenCode. The maintainer cared enough about
   distribution to do this.

3. **Cross-platform test discipline.** validate.sh + validate.ps1
   each ~210 lines. Most personal Claude skills don't test their
   install path on Windows; this one does.

4. **CN-rooted methodology, EN README, MIT license — clean
   internationalization pattern.** Methodology is from Mao-era
   dialectical materialism, but presentation is bilingual + MIT —
   makes it usable in non-CN engineering contexts as long as the
   adopter has read the README's "this is methodology not politics"
   framing.

5. **Skill granularity is honest.** 10 distinct methodologies
   (contradiction analysis vs investigation-first vs protracted-
   strategy etc.) are genuinely different reflexes — not a single
   skill split into 10 pieces for marketing. User picks the 2-3
   they need; that maps cleanly to molecule-layer "multiple
   user-invocable atoms".

## Verdict implication

6/7 static claims passed (one passed_with_concerns for the empty
file). MIT + multilingual + cross-platform + npm bin + tests give
solid maintainer signal. Score expected around 70 (Self-use OK).
