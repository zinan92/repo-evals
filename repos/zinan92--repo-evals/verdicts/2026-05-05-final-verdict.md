# zinan92/repo-evals — final verdict (2026-05-05)

## Repo

- **Name:** zinan92/repo-evals · **Stars:** 0 (private/personal)
- **Archetype:** pure-cli · **Layer:** **molecule**
- **License:** README claims MIT but no LICENSE file
- **Pushed:** 2026-05-05 (today, commit `b94031e`)

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 score is auditable | passed | 6 named breakdown buckets, math tested |
| 002 bilingual EN/ZH | passed | All 30 dossiers + new SVG diagrams toggle correctly |
| 003 4-category mapping | passed | All 6 boundaries tested |
| 004 3-layout workflow diagrams | passed | io / linear / tree all rendered in 3 golden dossiers |
| 005 similar-repos live scores | passed | _load_other_repo_for_compare calls compute_verdict at render time |
| 006 30-repo corpus exists | passed | 30 dirs under repos/ |
| 007 tests pass | passed | 142/142 |
| 008 LICENSE | **failed** | README says MIT but no LICENSE file (HTTP 404 if browsed) |
| 009 README is current | **failed** | README still describes the deprecated 4-bucket model |
| 010 live e2e onboarding | untested | needs a fresh user + logged session |

## Real findings — meta-eval edition

1. **The framework caught its own LICENSE gap.** This is the same defect
   we flagged on `karpathy/autoresearch`: README has a `## License — MIT`
   section + a license-MIT badge but no LICENSE file. The score model
   correctly applies the −2 penalty (small repo tier, <1K stars). Same
   one-line fix.

2. **README is now stale.** The framework migrated to the 0-100 score
   + 4-category model on 2026-05-05. README still says:
     > 评测分两层 ... 每个被评测的 repo 最终落入且只落入一个可靠性桶
     > unusable / usable / reusable / recommendable
   That's the deprecated 4-bucket model. Anyone reading README will
   form a mental model that doesn't match what the dossiers actually
   show.

3. **Score-model auditability is the real product.** Six named
   components — base 40, static_eval ±30, maintainer +15, ecosystem +15,
   layer_bonus, penalties — every dossier shows the breakdown. That's
   the API for methodology debate. A reader who disagrees can challenge
   any single number.

4. **30-repo corpus is past cold-start.** When the similar-repos block
   was added, it had 30 candidates to draw from. For repo-evals itself
   though, the corpus has zero peers — none of our 30 are eval
   frameworks, so we honestly say so in `similar_repos_pending` rather
   than forcing a wrong comparison.

5. **Self-eval as discipline test.** A framework that's unwilling to
   flag its own gaps will always shade its own claims. This eval found
   2 real defects (LICENSE, stale README) and 1 honest gap (no live
   e2e logged). That's the pattern we want to keep.

## Why the score lands where it does

- 7/9 testable claims passed; 2 failed (LICENSE + stale README); 1 untested
- 0 stars → ecosystem +0
- Recently active +5 + eval_discipline_score=3 (max +5) +
  release_pipeline_score=1 (no release tags yet) → maintainer +10
- Molecule layer: +0
- LICENSE missing: −2 (small-repo tier)
- High claim failed (claim-009 README): −4
- Critical claim failed (claim-008 LICENSE): −10

Predicted score: roughly **45-50** — somewhere between ⚠️ Risky and
🛠 Available. The honest read is that repo-evals scores its own
status correctly: usable for its current author + immediate audience,
but not yet at "share with strangers" because of the LICENSE +
out-of-date README.

## Path to higher score

1. **Add LICENSE file.** One commit. Recovers +10 from the failed
   critical claim → ~55-60 (mid 🛠 Available).
2. **Update README to describe 0-100 + 4-category model.** Recovers
   +4 + the failed-high deduction → ~60-65 (firm 🛠 Available).
3. **Run a logged live e2e** — fresh clone, scaffold a new repo,
   render its dossier, log the session. Moves claim-010 to passed
   and unblocks the path to 70+ (entering 🏭 Production-ready
   territory).
4. **Build the live-eval tooling** the framework keeps assuming
   exists. Right now no claim can earn the "evidence_completeness:
   full" tier without a manual logged session.

## Recommended

```yaml
status: evaluated
```
