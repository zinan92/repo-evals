# TradeCat — final verdict (2026-05-04)

## Repo

- **Name:** tukuaiai/tradecat
- **Branch evaluated:** develop@HEAD (package version 0.1.0)
- **Archetype:** pure-cli
- **Layer:** **molecule** — 4 dataset readers + sync + probe + TUI
  wired by predefined orchestration; no LLM
- **Eval framework:** repo-evals layer model v1 (fe256e5)

## Bucket

**`usable`** — capped by the molecule rule. Static layer is unusually
clean, but the actual user value (seeing real market data in a
terminal) is downstream of a live Google Sheets fetch that no static
check can validate.

## What was evaluated

### Atom + molecule level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 install.sh shape | passed | 5 env-var overrides + 2 CI skip flags, real POSIX shell |
| 002 dataset registry | passed | 4 active datasets, modes match README (3 snapshot + 1 stream) |
| 003 Python version + entry-points | passed | install.sh 3.12 ↔ pyproject >=3.12 ↔ 3 entry-points present |
| 004 zero-install request.py | passed | 7468-byte real script, shares dataset_registry.json with installed CLI |
| 005 TUI graceful fallback | passed | tui.py has 22 references to documented fallback env vars + plain mode |
| 006 auto-update env vars | passed | install.sh has 8 references to NO_AUTO_UPDATE / FORCE_UPDATE / UPDATE_INTERVAL |

### Molecule level (deferred)

| Claim | Status | Required |
|---|---|---|
| 007 e2e live sync | untested | install + sync + render at least one dataset; confirm cache + idempotency |

## Real findings worth surfacing

1. **Honest README.** Unusually clear about what the tool *doesn't* do:
   no PostgreSQL writeback, no SQLite, no cloud accounts, no server
   credentials. That clarity is itself a quality signal — it cuts
   support burden and sets reader expectations correctly.

2. **Single-source dataset contract.** `dataset_registry.json` is
   shared by the installed CLI *and* the zero-install `request.py` —
   one file, one truth. If users start writing scripts against the
   contract, this design keeps them stable across `pip install` vs
   `curl|sh` paths.

3. **Google Sheets is the data backbone.** The 4 datasets resolve to
   workbook + tab GIDs in Google Sheets — clever for a small project
   (zero infra cost, public read), but the project owners can rename
   tabs at any time and break every install. The auto-update path
   means a registry change can ship silently. Note this in the
   `watch_out` field of repo.yaml; users who want stability should
   set `TRADECAT_NO_AUTO_UPDATE=1`.

4. **`develop` as default branch.** Most repos cut releases against
   `main`; tradecat develops + installs from `develop` directly. Worth
   knowing if you pin a fork.

## Why not higher

`usable` is the right ceiling because:

- No live sync logged on this evaluator's machine. Static layer is
  fully clean, but the molecule rule explicitly requires evidence of
  the actual orchestrated outcome (cache populated, TUI shows real
  rows) before claiming `reusable`.
- Single-evaluator, single-day pass — even one clean live run wouldn't
  justify `recommendable` until a second machine confirms.

## Path to `reusable`

1. Run `curl -fsSL https://raw.githubusercontent.com/tukuaiai/tradecat/develop/install.sh | sh` on a fresh shell.
2. Confirm `tradecat sync` returns 0 and `~/.tradecat/app/.tradecat/cache/snapshots/*.json` is non-empty.
3. Run `tradecat tui --plain` and capture row count of the first
   dataset.
4. Re-run sync and confirm idempotency.
5. Log under `runs/<date>/run-live-sync/business-notes.md`. Update
   claim-007 to `passed` and re-run verdict_calculator.

## Recommended

```yaml
current_bucket: usable
status: evaluated
```
