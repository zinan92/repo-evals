# Business Notes — run-source-and-dmg-integrity

## Scenario

Source-inspection + prebuilt artifact integrity for iamzhihuix/skills-manage v0.9.1. Runtime GUI workflow was deliberately skipped to protect the tester's active skill environment (260+ skills across live Claude Code session).

## What I Did

1. Cloned `iamzhihuix/skills-manage` at commit `d416e0a` (default branch, 2026-04-23 push).
2. Downloaded `skills-manage_0.9.1_macos_universal.dmg` from GitHub Releases; verified SHA256 matches the asset digest byte-for-byte (`da1a1578…2913e5`).
3. Mounted the DMG read-only with `hdiutil attach`, verified Mach-O universal binary (arm64 + x86_64), `codesign -dv` reports `adhoc, linker-signed` (consistent with README's "not notarized" disclosure). Unmounted.
4. Grep-mapped every README claim to a concrete source line:
   - Symlink syscall: `linker.rs:75` (unix), `:80` (windows)
   - Central dir: `path_utils.rs:46-48` → `~/.agents/skills/`
   - SQLite path: `lib.rs:22-24`, `path_utils.rs:42` → `~/.skillsmanage/db.sqlite`
   - Agent detection: `agents.rs::is_agent_detected()` (live fs check, no cache)
   - GitHub import mirrors: `github_import.rs:222,227,232,237` (api.github.com + 3 mirrors)
   - Idempotent install: `db.rs::upsert_skill_installation` uses `ON CONFLICT(skill_id, agent_id) DO UPDATE`
   - Bidirectional centralize: `linker.rs:154::ensure_centralized`
5. Zero telemetry/analytics matches in `package.json` or `src-tauri/Cargo.toml`.
6. Compared README "Supported Platforms" table (28 rows) against `builtin_agents()` seed (27 ids). Missing: **EasyClaw V2** (`easyclaw-20260322-01`).

## What I Did Not Do

- No `pnpm install && pnpm tauri dev` (skipped — would add 2+ GB of deps to machine)
- No actual app launch, no install/uninstall of any skill through the GUI
- No `cargo test` / `pnpm test` run (CLAUDE.md self-reports 3 legacy frontend failures)

## Business Outcome

The code path for every README claim exists and is reviewable in the source tree. The prebuilt artifact is bit-identical to the published release. Any user running the app will hit real code for install/uninstall/symlink/GitHub-import/detection flows.

However, **"code exists" ≠ "workflow succeeds for a real user"**. That bar requires runtime validation that this eval did not perform.

## Recommendation

For a user who already keeps their skills in one place: proceed with confidence in a clean macOS user account or VM. For a user like the tester, whose `~/.agents/` and `~/.claude/skills/` are already under management by other tools, run a full backup first and evaluate whether yet another "source of truth" layer helps or conflicts.

## Known Caveats Discovered

| Finding | Severity | Impact |
|---|---|---|
| README lists 28 platforms, code seeds 27 (missing EasyClaw V2) | Low | Users who pick EasyClaw V2 see "not implemented" |
| README says React 19, package.json ships React 18.3 | Info | Cosmetic |
| README says "Apple Silicon macOS", DMG is universal | Info | Favorable under-claim |
| Hermes categorized `Coding` in README, `lobster` in code | Info | UI grouping only |
| API keys stored unencrypted in SQLite | Medium | Honest README disclosure; user must judge |
| v0.9.1 is 11 days old, adhoc-signed | Medium | Expected for pre-1.0 project |
| 3 legacy failing frontend tests (self-disclosed in CLAUDE.md) | Low | Unrelated to core claims |
