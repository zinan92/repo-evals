# Verdict Calculator

`scripts/verdict_calculator.py` is a rule-guided recommendation engine for
the final reliability bucket. It does **not** replace the human verdict
document — it produces a reviewable recommendation that a human can accept
or override with a written reason.

## Why

Verdicts have historically been thoughtful but evaluator-dependent.
Two reviewers looking at the same `claim-map.yaml` could land in different
buckets. The calculator makes the rule table explicit and auditable:

- same structured inputs → same recommended bucket
- ceilings are enforced in code, not just in docs
- overrides must carry a reason

## Inputs

Pass a YAML (or JSON) file like:

```yaml
repo: nicobailon/visual-explainer
archetype: hybrid-skill          # pure-cli | prompt-skill | hybrid-skill
                                 # | adapter | orchestrator | api-service
core_layer_tested: false         # did the eval exercise the user-facing layer?
evidence_completeness: full      # none | partial | portable | full
claims:
  - id: claim-001
    priority: critical           # critical | high | medium | low
    status: passed                # passed | passed_with_concerns
                                  # | failed | failed_partial | untested
  - id: claim-007
    priority: critical
    status: untested
override:                        # optional — must include a reason
  apply: false
  bucket: null
  reason: null
```

## Output

```bash
python3 scripts/verdict_calculator.py input.yaml             # YAML
python3 scripts/verdict_calculator.py input.yaml --json      # JSON
python3 scripts/verdict_calculator.py input.yaml --md        # Markdown report
python3 scripts/verdict_calculator.py input.yaml -o rec.yaml # write to file
```

Recommendation fields:

| Field | Meaning |
|---|---|
| `recommended_bucket` | What the rules say, before any override |
| `final_bucket` | Same as recommended, unless override applied |
| `confidence` | `low` / `medium` / `high`, based on untested critical claims and active ceilings |
| `ceiling_reasons` | Every ceiling rule that fires (explained below) |
| `blocking_issues` | Things that would need to be fixed to move up a bucket |
| `inputs_summary` | Normalised counts the calculator actually reasoned over |
| `override` | `{applied, bucket, reason}` — explicit, auditable |

## Rule table

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

| Rule | Effect | Reason string |
|---|---|---|
| `core_layer_tested: false` | cap at `usable` | *"core user-facing layer untested → capped at 'usable'"* |
| `archetype ∈ {hybrid-skill, prompt-skill, orchestrator}` and core untested | second reason surfaced | *"hybrid-repo rule: archetype 'X' requires end-to-end evaluation of the user-facing layer"* |
| `evidence_completeness < portable` | cap at `usable` | — |
| `evidence_completeness < full` | cap at `reusable` | — |

All applicable ceilings are recorded in `ceiling_reasons`, even when a lower
bucket was already set by the baseline rules. This keeps the full set of
constraints visible to reviewers.

### Confidence

| Signal | Confidence |
|---|---|
| No claims at all | `low` |
| Any untested critical claim, or > 1/3 of all claims untested | `low` |
| Any ceiling fired, or any high-priority claim untested | `medium` |
| Otherwise | `high` |

## Override path

If a human reviewer decides the rules are too conservative (or too
generous) for a specific case, they can override:

```yaml
override:
  apply: true
  bucket: reusable
  reason: |
    Manual B-layer spot-check covered in
    runs/2026-04-07/run-llm-e2e/business-notes.md sections 3-5.
```

Rules:

- `override.bucket` must be one of the four buckets
- `override.reason` is **required** — the tool errors out without it
- `recommended_bucket` is unchanged; `final_bucket` becomes the override bucket
- `override.applied: true` is recorded in the output for audit

## Using it with a real repo

Typical flow:

1. Finish runs, fill `claims/claim-map.yaml` statuses
2. Create `verdicts/<date>-verdict-input.yaml` with the structured inputs
3. Run `python3 scripts/verdict_calculator.py verdicts/...-verdict-input.yaml --md -o verdicts/<date>-recommendation.md`
4. Write `verdicts/<date>-final-verdict.md` by hand, citing the recommendation
   and any override reasoning
5. Commit all three: input, recommendation, and final verdict

This keeps the rule-driven reasoning and the human judgment both in git.

## Tests

See `tests/test_verdict_calculator.py`. Run:

```bash
python3 tests/test_verdict_calculator.py     # no pytest required
# or
python3 -m pytest tests/test_verdict_calculator.py -v
```
