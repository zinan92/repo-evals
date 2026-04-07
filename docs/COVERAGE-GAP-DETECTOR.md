# Coverage Gap Detector

`scripts/coverage_gap_detector.py` compares a repo's claim map against
its eval plan and its runs, and surfaces gaps a reviewer should look
at before accepting a verdict.

This is a prompt for human review, not a gate. The tool is deliberately
conservative — it flags things worth a second look, not things it
refuses to let ship.

## Usage

```bash
# YAML (default)
scripts/coverage_gap_detector.py repos/owner--repo

# JSON
scripts/coverage_gap_detector.py repos/owner--repo --json

# Markdown report
scripts/coverage_gap_detector.py repos/owner--repo --md

# CI-friendly: exit non-zero if any critical gap exists
scripts/coverage_gap_detector.py repos/owner--repo --fail-on critical
```

## Inputs

The tool reads these files from the repo directory, all optional except
the claim map:

| File | Required | Used for |
|---|---|---|
| `claims/claim-map.yaml` | yes | every rule |
| `plans/*-eval-plan.md` | no | plan coverage rules (latest by name) |
| `runs/**/run-summary.yaml` | no | run evidence rules (`results_by_claim`) |
| `repo.yaml` | no | `archetype`-aware rules |

No file is modified. Output is stdout only.

## Severity levels

| Level | Meaning |
|---|---|
| `critical` | Would block a strong verdict. Must be addressed before accepting anything above `usable`. |
| `warning` | Likely weakens the eval. Should be addressed. |
| `info` | Worth noting for plan review. |

## Rule table

| Code | Severity | Condition |
|---|---|---|
| `EVIDENCE_NEEDED_BLANK` | critical (if priority=critical), else warning | `evidence_needed` is empty on a claim |
| `CRITICAL_CLAIM_MISSING_FROM_PLAN` | critical | A critical claim's id and title are both absent from the latest `eval-plan.md` |
| `CRITICAL_CLAIM_UNTESTED` | critical | A critical claim still has `status: untested` |
| `CRITICAL_CLAIM_FAILED` | critical | A critical claim has `status: failed` |
| `HIGH_CLAIM_UNTESTED` | warning | A high-priority claim still has `status: untested` |
| `CLAIM_STATUS_BUT_NO_RUN_EVIDENCE` | warning | A critical / high claim has a non-untested status but no run's `results_by_claim` references it |
| `ORPHAN_PLAN_REFERENCE` | info | The plan mentions a `claim-NNN` id that is not in the claim map |
| `HYBRID_ARCHETYPE_NO_CORE_CLAIMS` | warning | `archetype` is `hybrid-skill` / `prompt-skill` but no claim's `area` contains `core` or `llm` |

## Plan-matching rule

A claim is considered "in the plan" if its `id` **or** its `title`
(case-insensitive) appears anywhere in the plan body.

This is intentionally loose. Evaluators can use either reference style.
If a claim title changes, the plan will start flagging it as missing —
that is the point. A rename should trigger a re-review.

## Run evidence rule

A run is said to cover a claim when the run's `results_by_claim` has
a key that is exactly the claim id or starts with `<claim-id>-`. So
`claim-001` matches `claim-001` and `claim-001-install` but not
`claim-0011`.

## Interpreting the output

Example YAML fragment:

```yaml
repo: zinan92--content-downloader
archetype: unknown
plan_path: plans/2026-04-07-eval-plan.md
runs_scanned: 1
claims_scanned: 7
summary:
  total: 6
  critical: 5
  warning: 1
  info: 0
gaps:
  - severity: critical
    code: CRITICAL_CLAIM_FAILED
    claim_id: claim-003
    message: "claim-003 is critical and marked failed — must be resolved before a strong verdict"
```

A reviewer should:

1. Fix or re-explain every `critical` gap before accepting anything
   above `usable`.
2. Resolve every `warning` before accepting anything above `reusable`.
3. Use `info` as context for plan rewrites.

## When to run it

- Before filling in the verdict document
- After every plan revision
- In CI, against every repo that has been re-evaluated, with `--fail-on critical`

## What the detector will not catch

- Claims the repo **should** have but doesn't — that's the job of the
  Claim Extraction Assistant (`scripts/extract_claims.py`)
- Claims whose evidence is technically present but substantively weak
  (screenshot of an empty page, log with only happy prints)
- LLM-layer quality issues — those require a human or the live-run
  evidence itself

Use this alongside `verdict_calculator.py` and human review, not as
a replacement for either.
