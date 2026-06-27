# zinan92/repo-evals — final verdict (2026-06-27)

## Repo

- **Name:** zinan92/repo-evals · **Stars:** 0 (private/personal)
- **Archetype:** pure-cli · **Layer:** **molecule**
- **License:** MIT LICENSE file present
- **Pushed baseline:** `e9d45a19`; this pass validates the current credibility fixes

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 score is auditable | passed | 6 named breakdown buckets, math tested |
| 002 bilingual EN/ZH | passed | Rendered dossiers carry EN/ZH fields and runtime language toggle |
| 003 4-category mapping | passed | Boundary tests cover Production / Available / Risky / Don't use |
| 004 3-layout workflow diagrams | passed | io / linear / tree branches exist and render |
| 005 similar-repos live scores | passed | Peer cards compute current verdict data at render time |
| 006 corpus exists for cross-comparison | passed | The corpus is past cold start and dashboard-indexed |
| 007 tests pass | passed | `151 passed` on 2026-06-27 |
| 008 LICENSE | passed | MIT LICENSE exists at repo root |
| 009 README is current | passed | README describes the current 0-100 + 4-category model |
| 010 live e2e onboarding | passed | Fresh-clone style scaffold → fill → render → dashboard smoke test logged |

## Real findings

1. **The P0 test failures were real and fixed.** Four archetype starter
   claim maps had unescaped Chinese double quotes that made PyYAML fail.
   The generic claim template also drifted from its scaffold test contract.
   After the fix, the focused archetype suite passes and the full suite is
   green.

2. **The self-eval evidence chain is now explicit.** Claims 001-009 now state
   `evidence_needed`, so the coverage gap detector no longer has to infer what
   would prove each claim. Claim 010 has a dated live e2e run with preserved
   command log and rendered HTML artifact.

3. **The test output is now clean.** The prior pytest warnings came from
   unregistered custom marks (`unit`, `integration`) in `tests/test_layers.py`.
   `pytest.ini` now registers both marks.

## Why the verdict improved

- All 10 self-eval claims are now passed.
- The full test suite is green: `151 passed`.
- License and README drift were already fixed; the stale self-eval wording has
  been replaced by this fresh verdict.
- Live e2e onboarding evidence now exists under
  `runs/2026-06-27/run-live-e2e/`.

The honest status is **Available and close to team-ready**: the framework is
usable and internally auditable, but still needs a public packaging pass
before broad distribution as an installable skill.

## Path to higher score

1. Add public-skill packaging: demo GIF/video, `.claude-plugin/marketplace.json`,
   one-line `npx skills add` path, and skills.sh badge if this will be
   distributed as a public skill.
2. Run the same live e2e on a genuinely unseen third-party repo, not only a
   smoke fixture.

## Recommended

```yaml
status: evaluated
category: available
next_step: register_pytest_marks_then_package_public_skill
```
