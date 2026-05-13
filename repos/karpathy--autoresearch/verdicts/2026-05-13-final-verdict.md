# karpathy/autoresearch — refreshed verdict (2026-05-13)

## Bucket

⚪ **usable** (manual override applied — matches 2026-05-05 verdict).

The calculator's raw output is 🔴 unusable, driven entirely by the
LICENSE-missing claim being marked critical+failed. Override is applied
because the LICENSE gap affects redistribution legality, not the repo's
runnability; on actual hardware the pipeline works. The override is
documented in `2026-05-13-verdict-input.yaml`.

Bucket stays at `usable` (not `reusable`) because the compound runtime
layer (claim-007) is still untested — that gap is real and would need a
live H100 run to close.

## Repo state

- **Name:** karpathy/autoresearch · **Stars:** ~79K · **Archetype:** hybrid-skill · **Layer:** compound
- **Upstream:** unchanged since prior eval — last commit `228791fb` on 2026-03-25
- **Refresh trigger:** user invoked `/repo-evals` — re-running because policy says new run overwrites old

## Claims (8 total)

| Claim | Priority | Status | Notes |
|---|---|---|---|
| 001 3-file pipeline shape | critical | ✅ passed | prepare 389 + train 630 + program 114 lines |
| 002 pyproject + uv.lock | critical | ✅ passed | Python 3.10+, pytorch-cu128, locked |
| 003 program.md is real | critical | ✅ passed | 5 sections (Setup / Experimentation / Output / Logging / Loop) |
| 004 train.py model+optim | high | ✅ passed | 25 model/optimizer signatures |
| 005 LICENSE file | critical | ❌ failed | README says MIT, no LICENSE at root (HTTP 404) |
| 006 4 community forks | high | ✅ passed | All HTTP 200 (Mac / MLX / Win-RTX / AMD) |
| 007 e2e H100 training | critical | ⏭ untested | needs H100 + GPU time — skipped, no test rig |
| 008 agent safety scope | critical | ✅ passed | program.md explicitly fences `prepare.py` as read-only |

## Calculator output (authoritative)

- **Recommended:** 🔴 unusable
- **Confidence:** high
- **Ceiling reasons:**
  - core user-facing layer untested → capped at `usable`
  - hybrid-skill requires end-to-end evaluation of the user-facing layer
  - `evidence_completeness=partial` → capped at `usable`
- **Blocking issue:** critical claim claim-005 (LICENSE) failed → drops below `usable` to `unusable`

## What this actually means

Two-line plain English:

1. The repo is real, well-shaped, and the static pieces are healthy — 6/8 claims pass on direct inspection of the code.
2. We can't bless it as "usable / reusable / recommendable" because (a) nobody on this machine has actually run the 5-minute training experiment on an H100 to confirm end-to-end, and (b) Karpathy says MIT in the README but didn't ship a LICENSE file, so legal status for forks is technically unclear.

## Real findings worth surfacing

1. **`program.md` is the single best published example of agent-safety
   scope I've seen.** It explicitly declares `prepare.py` read-only and
   names `evaluate_bpb` as the ground-truth metric. Most "AI does my
   research overnight" repos hand-wave this; this one fences it. Worth
   recommending as a template even if you don't use the rest.

2. **Missing LICENSE on a 79K-star Karpathy repo is striking.** README
   closes with `## License — MIT` but the LICENSE file is HTTP 404.
   License scanners / SBOM tools / risk-averse adopters will all flag.
   One-line upstream fix.

3. **Community fork ecology is healthy.** All 4 listed forks live
   (Mac / MLX / Win-RTX / AMD). Unusual for a single-author repo —
   suggests the audience forks actively rather than waiting upstream.

4. **Compound classification is honest.** The agent decides at runtime
   what to change, runs the 5-min experiment, parses `val_bpb`, decides
   keep-or-discard, iterates. Static eval can't validate that; only a
   live run can. This is why core_layer_tested=false.

## Path to a higher bucket

- Ship a `LICENSE` file upstream → claim-005 passes → bucket can move to `usable`
- Run one logged H100 baseline (`uv sync && uv run prepare.py && uv run train.py`) → claim-007 passes + `core_layer_tested=true` → bucket can move to `reusable`
- Run one adversarial agent-safety probe (tell agent to modify `prepare.py`, watch it refuse) → strengthens claim-008 from static to live
