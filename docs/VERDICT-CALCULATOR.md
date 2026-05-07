# Verdict Calculator

`scripts/verdict_calculator.py` produces two outputs from the same inputs:

1. **A 0-100 score** — primary output, used by the editorial dossier
2. **A 4-bucket recommendation** — legacy compatibility, surfaced in some old verdicts

The tool does **not** replace the human verdict document — it produces a reviewable, auditable recommendation that a human can accept or override with a written reason.

## Why two outputs

The 4-bucket model (`unusable / usable / reusable / recommendable`) was too coarse — once a repo crossed `usable`, everything looked OK. The 0-100 score gives every dossier an explicit number with a clear pass-line (60), with every point traceable to a specific signal (claim outcome, maintainer activity, license presence, …).

Both outputs are computed from the same input file. New evals should think in score; legacy evals still reference buckets.

## Inputs

Pass a YAML (or JSON) file like:

```yaml
repo: nicobailon/visual-explainer
archetype: hybrid-skill          # pure-cli | prompt-skill | hybrid-skill
                                 # | adapter | orchestrator | api-service
                                 # | mcp-enhancement
layer: molecule                  # atom | molecule | compound
core_layer_tested: false         # did the eval exercise the user-facing layer?
evidence_completeness: partial   # none | partial | portable | full

# Maintainer / ecosystem signals — feed the 0-100 score
stars: 142
archived: false
has_license: true
multilingual_readme: false
release_pipeline_score: 1        # 0..3 — 0=none, 1=manual, 2=CI, 3=tagged
eval_discipline_score: 2         # 0..3
recently_active: true

claims:
  - id: claim-001
    priority: critical           # critical | high | medium | low
    status: passed                # passed | passed_with_concerns
                                  # | failed | failed_partial | untested
    area: core                    # used for privacy/security penalty
  - id: claim-007
    priority: critical
    status: untested

override:                        # optional — must include a reason
  apply: false
  bucket: null
  reason: null
```

When you run `render_verdict_html.py` without a hand-written verdict-input sidecar, the renderer auto-derives this shape from `repo.yaml` + `claim-map.yaml` (`_derive_verdict_input` in `render_verdict_html.py`).

## Output

```bash
python3 scripts/verdict_calculator.py input.yaml             # YAML
python3 scripts/verdict_calculator.py input.yaml --json      # JSON
python3 scripts/verdict_calculator.py input.yaml --md        # Markdown report
python3 scripts/verdict_calculator.py input.yaml -o rec.yaml # write to file
python3 scripts/verdict_calculator.py input.yaml --no-html   # don't auto-open dossier
```

Recommendation fields:

| Field | Meaning |
|---|---|
| `score` | 0–100 number — primary verdict |
| `tier_key` | `recommend` (≥90) / `team` (≥80) / `self` (≥65) / `try` (≥50) / `risky` (≥30) / `broken` (<30) |
| `category_key` | `production` (80+) / `available` (50–79) / `risky` (30–49) / `dont_use` (0–29) |
| `breakdown` | Where every point came from — see "Score model" below |
| `recommended_bucket` | Legacy: `unusable / usable / reusable / recommendable` from rule table |
| `final_bucket` | Same as recommended unless override applied |
| `confidence` | `low` / `medium` / `high` based on untested critical claims + active ceilings |
| `ceiling_reasons` | Every ceiling rule that fired |
| `blocking_issues` | What needs to change to move up |
| `inputs_summary` | Normalised counts the calculator reasoned over |
| `override` | `{applied, bucket, reason}` — explicit, auditable |

## Score model (0–100, additive)

Source: `compute_score()` in `verdict_calculator.py`.

```
base                              = +40
+ static eval (claim outcomes)    = ±30 (clamped)
+ maintainer evidence             = +0..+15
+ ecosystem validation (stars)    = +0..+15
+ layer bonus                     = -3..+5
+ penalties                       = negative
─────────────────────────────────────────
= score, clamped to [0, 100]
```

### Static eval contribution (per claim, then clamped)

| Priority | Status | Δ |
|---|---|---|
| critical | passed | +5 |
| critical | passed_with_concerns | +3 |
| critical | failed / failed_partial | -10 |
| critical | untested | -2 |
| high | passed | +2 |
| high | passed_with_concerns | +1 |
| high | failed / failed_partial | -4 |
| any | passed_with_concerns + area∈{privacy,security,safety} | extra -3 each |

Sum is clamped to [-30, +30].

### Maintainer evidence (cap +15)

| Signal | Δ |
|---|---|
| `release_pipeline_score >= 2` (CI in place) | +5 |
| `eval_discipline_score >= 2` (real eval harness) | +5 |
| `recently_active` (release/commit in 90 days) | +5 |
| `multilingual_readme` | +2 |

### Ecosystem validation (cap +15)

Stars-band lookup (`_stars_band_points`):

| Stars | Δ |
|---|---|
| ≥ 10,000 | +15 |
| ≥ 5,000 | +12 |
| ≥ 1,000 | +6 |
| < 1,000 | +3 |
| 0 | +0 |

### Layer bonus

| Layer | Δ | Why |
|---|---|---|
| `atom` | +5 | Static checks fully validate the user-facing contract |
| `molecule` | 0 | Structure validatable; orchestration not |
| `compound` | -3 | Static checks miss runtime LLM-driven behaviour |

### Penalties

| Condition | Δ |
|---|---|
| `archived: true` | -50 (this drops most repos to `dont_use` outright) |
| Privacy/security `passed_with_concerns` | -3 each |
| No LICENSE, ≥10K stars | -5 |
| No LICENSE, ≥1K stars | -3 |
| No LICENSE, <1K stars | -2 |

## Tier + category lookup

Score → tier → category:

| Score | Tier | Category |
|---|---|---|
| ≥90 | ⭐ `recommend` | 🏭 `production` |
| ≥80 | 🏭 `team` | 🏭 `production` |
| ≥65 | 🛠 `self` | 🛠 `available` |
| ≥50 | 🧪 `try` | 🛠 `available` |
| ≥30 | ⚠️ `risky` | ⚠️ `risky` |
| <30 | 🛑 `broken` | 🛑 `dont_use` |

The 4 categories are what filter pills + dashboard headers show. The 6 tiers are for fine-grained sort.

## Legacy 4-bucket rule table (still emitted for compatibility)

### Baseline bucket from claim results

| Condition | Bucket |
|---|---|
| Any critical claim failed | `unusable` |
| Zero critical claims covered | `unusable` |
| No critical claims defined at all | `usable` (+ blocking issue) |
| Critical coverage partial | `usable` |
| All critical passed, coverage ≥ 80%, no high failures | `recommendable` |
| All critical passed, coverage ≥ 50% | `reusable` |

### Ceilings (always applied after the baseline)

| Rule | Effect |
|---|---|
| `core_layer_tested: false` | cap at `usable` |
| `archetype ∈ {hybrid-skill, prompt-skill, orchestrator}` and core untested | second reason surfaced |
| `evidence_completeness < portable` | cap at `usable` |
| `evidence_completeness < full` | cap at `reusable` |

All applicable ceilings are recorded in `ceiling_reasons` even when a lower bucket was already set by the baseline.

## Confidence

| Signal | Confidence |
|---|---|
| No claims at all | `low` |
| Any untested critical claim, or > 1/3 of all claims untested | `low` |
| Any ceiling fired, or any high-priority claim untested | `medium` |
| Otherwise | `high` |

## Override path

If a human reviewer decides the rules are too conservative (or generous) for a specific case, they can override the bucket:

```yaml
override:
  apply: true
  bucket: reusable
  reason: |
    Manual B-layer spot-check covered in
    runs/2026-04-07/run-llm-e2e/business-notes.md sections 3-5.
```

Rules:

- `override.bucket` must be one of the four legacy buckets
- `override.reason` is **required** — the tool errors out without it
- `recommended_bucket` is unchanged; `final_bucket` becomes the override bucket
- `override.applied: true` is recorded for audit
- The override does NOT change the 0-100 score — score is computed from signals, not bucket judgment

## Typical flow

1. Finish runs, fill `claims/claim-map.yaml` statuses
2. Make sure `repo.yaml` has the maintainer + ecosystem fields filled (`stars`, `has_license`, `release_pipeline_score`, etc.) — these drive 30+ score points
3. Either:
   - Hand-write `verdicts/<date>-verdict-input.yaml`, OR
   - Let `render_verdict_html.py` derive it from `repo.yaml` + `claim-map.yaml`
4. Run `python3 scripts/verdict_calculator.py verdicts/<date>-verdict-input.yaml --md -o verdicts/<date>-recommendation.md`
5. Render the dossier: `python3 scripts/render_verdict_html.py <slug> --lang zh`
6. Write `verdicts/<date>-final-verdict.md` by hand, citing the score breakdown + any override reasoning
7. Commit input, recommendation, dossier HTML, and final verdict together

## Tests

See `tests/test_verdict_calculator.py`. Run:

```bash
python3 tests/test_verdict_calculator.py     # no pytest required
python3 -m pytest tests/test_verdict_calculator.py -v
```
