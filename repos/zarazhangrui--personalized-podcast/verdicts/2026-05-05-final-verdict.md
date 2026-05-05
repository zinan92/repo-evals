# personalized-podcast — final verdict (2026-05-05)

## Repo

- **Name:** zarazhangrui/personalized-podcast · **Stars:** 338
- **Archetype:** hybrid-skill · **Layer:** molecule
- **Branch:** main@HEAD · **Last push:** 2026-04-08 (recently active)

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 SKILL.md + PROMPT.md | passed | 235 + 33 lines |
| 002 4 Python scripts | passed | bootstrap / publish / speak / utils — 195–352 lines each |
| 003 deps coverage | passed | httpx + pydub + Jinja2 + PyYAML |
| 004 RSS feed template | passed | Real Jinja2-templated RSS XML |
| 005 config coverage | passed | show_name + tone + hosts + voices + length + RSS publish |
| 006 LICENSE | **failed** | HTTP 404 |
| 007 install path correctness | **failed** | README clones `-skill` repo; redirects work but README is wrong |
| 008 live `/podcast` e2e | untested | needs Fish Audio key + session |

## Real findings

1. **README install typo.** `gh repo clone zarazhangrui/personalized-podcast-skill`
   should be `personalized-podcast`. GitHub returns HTTP 301 redirect,
   so it works, but it's a polish gap. Trivial upstream fix.

2. **No LICENSE.** Fourth time across Zara's batch. Worth noting as
   a maintainer-level habit, not a per-repo defect.

3. **Sensible secret split.** Config (show settings) vs `.env` (API
   keys) is split correctly. `bootstrap.py` (352 lines) is the most
   substantial script — it does real first-run setup work.

4. **`/podcast` slash command + `/eavesdrop` self-reflection use case.**
   The "feed your own writing in and have hosts comment" angle is
   creative but warrants a privacy disclaimer the README is missing.

## Path forward

1. Add LICENSE.
2. Fix README clone path (`personalized-podcast-skill` →
   `personalized-podcast`).
3. Add a privacy note about Anthropic + Fish Audio seeing user
   content.
4. Run a live `/podcast` test with Fish Audio key; log under
   `runs/<date>/run-live-e2e/`.
