# Run summary — 2026-05-07 static checks

- runner: cc
- agent: Claude Code
- model: claude-opus-4-7
- target ref: develop@e1df620 (cloned to /tmp/tradecat-eval, depth=1)
- archetype: hybrid-skill
- layer: molecule

## Claims verified (PASS)

- claim-001 install.sh — 288 lines POSIX shell, PYTHON_VERSION=3.12, 8 auto-update env-var refs, 2 CI skip flags
- claim-002 dataset_registry.json — 4 active datasets across 2 workbooks (market_data + alternative_data); modes match README
- claim-003 Python version + entry-points — pyproject requires-python ">=3.12", 3 entry-points (tradecat / tradecat-terminal / tcat)
- claim-004 request.py — 191 lines, references same dataset_registry.json (raw URL), --datasets / --meta / --headers all present
- claim-005 TUI fallback — TUI_FORCE_CURSES_ENV / TUI_ALLOW_WINDOWS_CURSES_ENV constants, render_safe_plain_tui + render_plain_fallback paths exist
- claim-006 auto-update env vars — 8 references in install.sh; throttle / disable / force branches all present
- claim-008 Skill-shell boundary — root SKILL.md (197) + AGENTS.md (98) + references/ (8 docs); scripts/project/AGENTS.md (258); scripts/verify.sh (10) is a thin delegator
- claim-009 GitHub Actions CI — .github/workflows/ci.yml with 19 run steps; validate-skill.sh --strict + secret scan + supply-chain audit
- claim-010 Governance scripts — 8 shell scripts under scripts/, all real bash (not echo placeholders)
- claim-011 Tests — single file test_cache_tui.py, 1622 lines, 81 test functions; coverage real but brittle to refactor

## Claims FAILED

- claim-012 LICENSE — gh api license=null + 404 on contents/LICENSE; README MIT badge does not constitute a license. Unchanged from 2026-05-04 eval.

## Claims SKIPPED (deferred / molecule ceiling)

- claim-007 e2e live sync — skip_reason: framework forbids installing untrusted CLI on live system; recommend project mirrors this in CI artifact

## Provenance

- All paths verified against /tmp/tradecat-eval (commit e1df620)
- gh api repos/tukuaiai/tradecat ran 2026-05-07T13:31Z
