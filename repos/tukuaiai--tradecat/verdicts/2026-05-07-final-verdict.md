# TradeCat — final verdict (2026-05-07, full re-eval)

## Repo

- **Name:** tukuaiai/tradecat
- **Branch evaluated:** develop@e1df620 (package version 0.1.0)
- **Archetype:** **hybrid-skill** (changed from `pure-cli` — repo restructured between 2026-05-04 and 2026-05-07)
- **Layer:** **molecule** — Skill shell + 4 dataset readers + sync + probe + TUI wired by predefined orchestration; no LLM-runtime routing
- **Eval framework:** repo-evals layer model v1

## Bucket

**`usable`** — capped by the molecule rule: static layer is unusually clean and even improved since the last eval (CI added, governance shell in place), but actual user value (seeing real market data in a terminal) is still downstream of a live Google Sheets fetch that no static check can validate. The `no-LICENSE-file` defect from the prior eval is still unresolved and now applies to a 935-star repo.

## What was evaluated

### Static layer (this run, all PASS)

| Claim | Status | Notes |
|---|---|---|
| 001 install.sh path migrated to scripts/project/install.sh | passed | 288 lines POSIX shell, 5 env-var overrides + 2 CI skip flags |
| 002 dataset registry coverage (now 2 workbooks) | passed | 4 active datasets across market_data + alternative_data workbooks |
| 003 Python version + entry-points consistency | passed | install.sh 3.12 ↔ pyproject ">=3.12" ↔ 3 entry-points present |
| 004 zero-install request.py | passed | 191 lines, references same dataset_registry.json (raw URL) |
| 005 TUI graceful fallback | passed | TUI_FORCE_CURSES_ENV / TUI_ALLOW_WINDOWS_CURSES_ENV + render_safe_plain_tui present |
| 006 auto-update env vars | passed | install.sh has 8 references to NO_AUTO_UPDATE / FORCE_UPDATE / UPDATE_INTERVAL_SECONDS |
| 008 Skill-shell boundary (NEW) | passed | root SKILL.md (197) + AGENTS.md (98) + scripts/project/AGENTS.md (258); references/ has 8 long docs |
| 009 GitHub Actions CI (NEW) | passed | .github/workflows/ci.yml: validate-skill --strict + secret scan + supply-chain audit |
| 010 Governance scripts (NEW) | passed | 8 root shell scripts, all real bash (~580 lines total) |
| 011 Test coverage density (NEW) | passed | single test_cache_tui.py with 81 test functions / 1622 lines — adequate but brittle to refactor |

### Static layer FAILED

| Claim | Status | Notes |
|---|---|---|
| 012 LICENSE file present | **failed** | gh api license=null + 404 on /contents/LICENSE; README MIT badge does not constitute a license. Unchanged from 2026-05-04. |

### Molecule level (deferred)

| Claim | Status | Required |
|---|---|---|
| 007 e2e live sync | untested (skip) | install + sync + render at least one dataset; framework forbids installing untrusted CLI on evaluator's machine |

## Real findings worth surfacing

1. **Repo restructured to a Skill-shell layout in the last 3 days.** Root holds SKILL.md / AGENTS.md / references/ + thin governance scripts; `scripts/project/` holds the Python package, its own AGENTS.md, install.sh, tests. This is a clean reference layout for "Skill outside, project inside" — recommendable to other skill authors who need to bundle a working Python tool.

2. **CI now exists and is non-trivial.** `.github/workflows/ci.yml` runs `validate-skill.sh --strict` (frontmatter + Codex skill alignment), a secret scan over the diff range (push range or PR base..HEAD), and a supply-chain audit. This earns release_pipeline_score 2 (was 1) but is held below 3 because no e2e sync run is captured as a CI artifact.

3. **Honest README — kept this strength.** Still unusually clear about what the tool *doesn't* do: no PostgreSQL writeback, no SQLite, no cloud accounts, no server credentials. That clarity remains a quality signal.

4. **Single-source dataset contract preserved across the move.** `dataset_registry.json` is now under `scripts/project/src/tradecat_terminal/`, but both the installed CLI *and* the zero-install `request.py` (via raw URL) still consume it. Refactor preserved the single-source guarantee.

5. **2-workbook design is new.** Previous registry had 1 workbook; now `market_data` (3 snapshot datasets) + `alternative_data` (event_stream). This is a healthier separation of concerns — alternative data has a different cadence and ownership profile.

6. **Test concentration is the soft spot.** 81 tests in a single 1622-line file is real coverage but a refactor liability. A reader looking for "where is the cache test" or "where is the TUI test" can't tell from filenames.

7. **License debt grew, not shrank.** README still claims MIT via badge, repo still has no LICENSE file, and the star count grew from 928 to 935 in the 3 days between evals. This is the easiest fix on the list (one file commit) and the highest legal cost of any single missing artifact.

## Score deltas vs. 2026-05-04

- **+** 4 new static claims passed (skill-shell, CI, governance, tests)
- **+** release_pipeline_score 1 → 2 (CI now exists)
- **=** has_license still false (penalty unchanged)
- **=** layer ceiling unchanged (still molecule with deferred e2e)
- **=** archetype changed from pure-cli to hybrid-skill (more accurate, no score effect)

## Next steps to raise the score

1. **Add a LICENSE file** matching the README MIT badge — biggest single-line win. Removes the 935-star unlicensed penalty and unblocks fork/redistribute.
2. **Capture an e2e sync run as CI artifact** (sync exit code + cache size + dataset row count) — would let claim-007 verify without each user running curl|sh, lifting the molecule ceiling.
3. **Split `test_cache_tui.py`** into focused modules (test_cache.py, test_tui.py, test_sync.py) — improves refactor safety and reads cleaner.
