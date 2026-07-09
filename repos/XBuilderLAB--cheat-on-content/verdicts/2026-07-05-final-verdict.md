# Final Verdict

## Repo

- **Name**: XBuilderLAB/cheat-on-content（网红作弊器 / Cheat on Content）
- **Version tested**: main@HEAD (tag v0.1.0)
- **Date**: 2026-07-05
- **Archetype**: orchestrator
- **Layer**: compound
- **Score**: 70 /100  (from `verdict_calculator.py`, not judgement)
- **Category**: 🛠 Available / 可使用
- **Tier**: self (≥65) — 自用 OK
- **Confidence**: medium

## Plain English

- Outcome if adopted: You get a genuinely well-engineered discipline for turning content hunches into logged, blind, data-settled predictions — the machinery (immutable predictions, isolated blind scoring, audited rubric upgrades) is real and honest.
- Regret scenario: You believed the README ("1M followers in a month") and expected growth; the tool sharpens *judgment*, not reach, and only pays off after months of disciplined use + platform credentials for auto data-pull.

## Why This Score

The user gets a calibration loop whose *integrity* is enforced in code, not just promised. The score is held to Available (not Production) purely because it's a compound skill with no logged live run — not because anything is broken.

### Top 3 score drivers

- **+15 static_eval**: 6 mechanism claims confirmed by reading source (immutability hook, blind-scorer isolation, bump protocol, migration chain, hype quarantine, 15 sub-skills). Two critical efficacy claims untested (−4 within cap).
- **+12 maintainer_evidence**: release_pipeline (tag + CHANGELOG + migration registry) + recently_active + multilingual README.
- **−3 layer_bonus + hard ceiling**: compound layer, `core_layer_tested=false` → final bucket capped at `usable`, category capped at Available regardless of raw score.

### Core outcome
Observably real (static): the *enforcement* of the three integrity principles — hook-blocked immutable predictions, context-isolated blind scorer with hard-refusal list, 5-step audited rubric bump. Observably NOT shown here: that running the loop actually improves outcomes (growth or prediction accuracy) — needs a longitudinal live run.

### Scenario breadth
Zero live runs (static eval only). Built-in rubric calibrated on ONE Chinese opinion-video creator (25+ videos, per adapter README). Other content formats require the user to author their own rubric.

### Repeatability
Deterministic parts (hook, install.sh, migrations) are repeatable by inspection. The LLM core (blind scoring) is explicitly non-deterministic — the skill itself says to treat each blind score as a sample, not truth.

### Failure transparency
Strong. The immutability hook exits 1 with an actionable remediation message; the blind scorer emits refusal codes + contamination flags; install.sh fails loudly (set -euo pipefail, conflict prompts). Honest ✅/⬜ done-vs-roadmap markers.

## What Would Move The Score Up

1. (~+10 → lifts ceiling) One sandboxed end-to-end live run (init → predict → publish → retro) with a trigger-fire + blind-isolation log → sets `core_layer_tested=true`, breaks the compound cap.
2. (~+? ) Verify one perf-data adapter actually returns data with a real (throwaway) account → covers claim-010.
3. (~+? ) A logged multi-cycle convergence curve (predictions error ↓ over N samples) → begins to cover the efficacy claims 003/004.

## Remaining Risks

| Risk | Severity | Impact | Mitigation |
|---|---|---|---|
| Efficacy unproven ("1M followers"/"10× sharper") | High | User adopts for growth, gets a mirror | Frame as judgment-calibration; ignore README growth hype |
| install.sh symlinks into live ~/.claude/skills | Medium | Pollutes agent skill dir | Run in sandbox / use `--copy`; reversible via uninstall.sh |
| Adapters need platform login + anti-scraping | Medium | Data-pull fragile / rots | Manual data entry fallback; treat adapters as best-effort |
| Rubric only fits one opinion-video creator | Medium | Other formats start cold | Write own rubric from starter-rubrics/*-zero.md |
| Months-long commitment before payoff | Low-Med | Abandonment | Only adopt for a real long-term content line |

## Related Artifacts

- Claim map: `claims/claim-map.yaml`
- Plan: `plans/2026-07-05-eval-plan.md`
- Runs: none (static eval; no live run per no-credentials / compound rule)
- Verdict calculator input: derived from repo.yaml + claim-map by `render_verdict_html.py`
- Rendered HTML dossier: `verdicts/2026-07-05-verdict.html`
- Vault copy: `001_agent-os/skills/_evaluations/260705_XBuilderLAB_cheat-on-content/{dossier.html,summary.md}`
