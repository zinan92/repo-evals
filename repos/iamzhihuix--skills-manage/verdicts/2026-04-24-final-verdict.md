# Final Verdict — iamzhihuix/skills-manage

## Repo

- **Name**: iamzhihuix/skills-manage
- **Version tested**: v0.9.1 (2026-04-23)
- **Date**: 2026-04-24
- **Archetype**: adapter
- **Final bucket**: `usable`
- **Confidence**: low (per verdict_calculator.py)

## Verdict Calculator Output

```
Recommended bucket: usable
Final bucket:       usable
Confidence:         low

Ceiling reasons:
  - core user-facing layer untested → capped at 'usable'
  - evidence_completeness='portable' → capped at 'reusable'

Blocking issues:
  - only 5/6 critical claims covered
```

Inputs: 8 of 9 claims passed (claim-001 passed_with_concerns, claim-009 untested). 5 of 6 critical claims covered; claim-009 is the uncovered one.

## Why This Bucket

### Core Outcome — code path exists, end-to-end not proven

Every claim about install / uninstall / symlink / detection / GitHub import / local-first storage has a concrete, reviewable code path. The prebuilt DMG is byte-identical to the release asset digest. But no real user workflow was executed through the GUI — the adapter archetype says that failing to exercise the *actual user-facing layer* caps the verdict at `usable`, and the rule applied.

### Scenario Breadth — narrow on purpose

Only one scenario was tested: "open the source + download + inspect bundle". No per-platform install smoke, no collection batch-install, no discover scan against a real project tree. The breadth floor is 1, not 28.

### Repeatability — not tested

No repeat runs. Idempotency was verified at the *schema level* (`ON CONFLICT(skill_id, agent_id) DO UPDATE`) but not by running the same install twice and inspecting on-disk state.

### Failure Transparency — good signals in code

- `is_agent_detected()` honestly returns false when both dir and parent are missing.
- `ensure_centralized()` errors out with explicit messages when the source skill is missing.
- GitHub import falls back through 4 mirrors, so a single network failure won't produce a misleading empty import.
- Zero telemetry libraries, so a failure can't be silently phoned home.

## What I Would Say In Plain English

skills-manage is a well-built young project (910 stars in 11 days is not an accident — the code shows it). The README's claims about "central library + symlink to per-platform" are not marketing: they are literally implemented with `std::os::unix::fs::symlink` and a relative-path computation that makes the links portable. Privacy claims are honest — the database is where they say it is, and there is no analytics dependency anywhere.

But this evaluation did not prove the app works for a real user. It proved the code for each claim exists. For a pre-1.0 Tauri desktop app that requires `xattr -dr com.apple.quarantine` to launch and will scan/modify directories many other tools are already managing, "code exists" is not enough to recommend.

**Use it if** you have a clean macOS account or a VM, and your skills live in one place today.
**Wait if** your `~/.claude/skills/`, `~/.agents/skills/`, or `~/.cursor/skills/` are already managed by another tool (dbskill, lobster lock file, plugin registries) — test in isolation first.

## Remaining Risks

1. **claim-009 (runtime E2E) untested**. Everything downstream of "user clicks install" is inferred, not observed.
2. **EasyClaw V2 listed in README but not seeded in code** (`builtin_agents()` has 27 ids vs README's 28 platforms). If a user specifically needs that platform, the adapter is missing.
3. **API keys stored unencrypted** in `~/.skillsmanage/db.sqlite` (README self-discloses; still a real constraint).
4. **adhoc signing + no notarization**. The `xattr` workaround is a permanent requirement until the maintainer signs the build.
5. **3 legacy failing frontend tests** (CLAUDE.md self-discloses). Not in the core path but worth noting.
6. **Schema drift**: README and code disagree about Hermes category and React version. Low-risk but pattern-of-minor-drift is a smell to watch at 1.0.

## What Would Move It To `reusable`

- A live run on a clean macOS user account: launch app, detect platforms, install one skill to two platforms, verify symlinks on disk, uninstall, verify cleanup — all with screenshots/log evidence.
- A repeat run proving idempotency at the filesystem level.
- An unsupported-input run (e.g., custom agent with a read-only dir) proving the failure is loud.

## What Would Move It To `recommendable`

- Everything above, plus:
- A 1.0 release with notarized macOS build and a Linux build (currently source-only).
- The 3 legacy failing frontend tests fixed.
- README-code consistency pass (EasyClaw V2, React version, Hermes category).

## Related Artifacts

- Claim map: `claims/claim-map.yaml`
- Plan: `plans/2026-04-24-eval-plan.md`
- Run: `runs/2026-04-24/run-source-and-dmg-integrity/`
  - DMG: `artifacts/skills-manage_0.9.1_macos_universal.dmg`
  - DMG integrity log: `logs/dmg-integrity.log`
  - Source inspection log: `logs/source-inspection.log`
  - Business notes: `business-notes.md`
- Verdict calculator input: `verdicts/2026-04-24-verdict-input.yaml`
