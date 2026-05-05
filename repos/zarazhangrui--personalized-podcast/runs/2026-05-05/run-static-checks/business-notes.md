# personalized-podcast — static-checks run, 2026-05-05

## Findings

| Claim | Status | Note |
|---|---|---|
| 001 SKILL.md + PROMPT.md | passed | 235 + 33 lines |
| 002 4 Python scripts | passed | bootstrap (352) + publish (295) + speak (254) + utils (195) lines |
| 003 deps coverage | passed | httpx + pydub + Jinja2 + PyYAML — all 4 present |
| 004 RSS template | passed | Real Jinja2-templated RSS XML with `{{ show_name }}` etc. |
| 005 config coverage | passed | All README-promised knobs present (show_name, tone, hosts, voices, length, RSS) |
| 006 LICENSE | **failed** | HTTP 404 — fourth Zara repo missing this |
| 007 README install path | **failed** | README clones `personalized-podcast-skill` but repo is `personalized-podcast`; works via 301 redirect but technically wrong |
| 008 live e2e | untested | needs Fish Audio key + Claude Code session |

## Real findings

1. **README install path typo.** The clone command in README:
   ```
   gh repo clone zarazhangrui/personalized-podcast-skill ~/.claude/skills/personalized-podcast
   ```
   The repo is actually `personalized-podcast` (no `-skill` suffix).
   GitHub redirects (HTTP 301) so installs still succeed, but
   copy-paste users will see a redirect notice. Trivial fix
   upstream.

2. **No LICENSE.** Fourth Zara repo in this batch missing. Pattern.

3. **Sensible config split.** `config.example.yaml` for non-secret
   prefs, `~/.personalized-podcast/.env` for API keys. Honest
   secret-handling.

4. **`bootstrap.py` is 352 lines** — the biggest of the 4 scripts.
   First-run env setup is doing real work (probably venv +
   dependency install + config bootstrap). Reasonable investment
   in zero-config UX.

5. **Recently active** (last push 2026-04-08, ~30 days at eval) —
   gets the +3 maintainer point. This is the fresher of Zara's 4
   newly-evaluated skills.

## Verdict implication

5/7 static claims passed (claim-006 LICENSE failed; claim-007
README typo failed but redirects). Recently-active gives a small
maintainer boost. Ecosystem (338 stars) is just below the +3 band.
Score expected mid-50s.
