# Re-Eval Diff Mode

`scripts/reeval_diff.py` compares two evaluation states of the same
repo and surfaces what actually changed — across claims, verdict
bucket, runs, archetype, and coverage gaps — so a reviewer can
answer *"did this repo get better, worse, or just different?"*.

Re-Eval Diff Mode is the piece that turns repo-evals from a
one-shot report system into a continuous evaluation system. Every
re-eval produces a diff that can be committed next to the old one.

## Design principles

- **Git is the source of truth.** Historical state is read via
  `git show <ref>:<path>`, never reconstructed from metadata.
- **No mutation.** Output goes to stdout or to files the caller
  explicitly names via `--output`.
- **Missing data is preserved truthfully.** Partial baseline
  provenance, missing claim maps, and unknown buckets are surfaced
  as explicit confidence-downgrade reasons rather than papered over.
- **Every comparison carries a confidence score** (`high | medium | low`)
  with a list of reasons if the level is less than `high`.

## Snapshots

A snapshot is the tuple:

```
(repo_meta, claims, verdict_bucket, runs, provenance_quality, gap_report)
```

resolved at a given reference point. Reference points are:

- A **git ref** (`HEAD`, `HEAD~5`, `abc1234`, a branch or tag name)
- The literal string **`working`** (the current filesystem state)

The loader:

- Reads `repo.yaml`, `claims/claim-map.yaml`, verdicts, run summaries,
  and the latest plan from Git (or the working tree).
- Classifies `provenance_quality` as `full`, `partial`, or `missing`
  based on the `captured` and `partial` flags Phase 1 wrote on every run.
- Computes a live coverage gap report for working-tree snapshots via
  `coverage_gap_detector.build_report`. For git-ref snapshots it
  falls back to the committed `gap-reports/*.md` files.

## CLI

```bash
# Compare working tree against a past commit
scripts/reeval_diff.py repos/owner--repo --from HEAD~5

# Compare two commits
scripts/reeval_diff.py repos/owner--repo --from 45d6c91 --to HEAD

# Write a committable diff artifact directory
scripts/reeval_diff.py repos/owner--repo --from HEAD~5 \
    --output repos/owner--repo/diffs/2026-04-07-baseline_to_working

# Output formats on stdout
scripts/reeval_diff.py repos/owner--repo --from HEAD~5 --md      # human
scripts/reeval_diff.py repos/owner--repo --from HEAD~5 --json    # agent
scripts/reeval_diff.py repos/owner--repo --from HEAD~5 --yaml    # default

# CI exit codes
scripts/reeval_diff.py repos/owner--repo --from HEAD~5 --fail-on regression
scripts/reeval_diff.py repos/owner--repo --from HEAD~5 --fail-on any-change
```

When `--output <dir>` is given, the tool writes three files:

```
diff.yaml       # full structured diff (source of truth)
diff.json       # identical data in JSON
summary.md      # human-readable Markdown
```

## Diff dimensions

### Claims

| Field | Contents |
|---|---|
| `added` | claims in head but not in baseline |
| `removed` | claims in baseline but not in head |
| `status_changes` | per-claim from / to / transition |
| `priority_changes` | per-claim priority delta |
| `title_changes` | per-claim title rewrite |
| `area_changes` | per-claim area rename |

Transitions are classified:

| From | To | Transition |
|---|---|---|
| `untested` | `passed` | `improvement` |
| `failed` | `passed` | `improvement` |
| `passed` | `failed` | `regression` |
| `passed` | `untested` | `regression` |
| `untested` | `failed` | `newly_failing` |
| same | same | `unchanged` |
| other pairs | — | `unknown` (treated conservatively) |

`passed_with_concerns` normalizes to `passed` for transition purposes.

`newly_failing` is its own category because it reflects *discovered
bad news* — not a regression (there was nothing to regress from) but
not a neutral either. Dashboards and reviewers should treat it as real
information.

### Verdict

Ordered as `unknown < unusable < usable < reusable < recommendable`.
A move up the ladder is an `improvement`, a move down is a
`regression`, same is `unchanged`. Any move involving `unknown` is
`unclassifiable` — the diff is honest that nothing meaningful can be
said yet.

### Archetype

Simple `from / to / changed`. A changed archetype is surfaced because
it changes what rules the verdict calculator applies.

### Runs

Set difference on the run file path. Reports `added`, `removed`,
and before/after counts. This is how a reviewer sees "did we
actually run anything new since last time?".

### Coverage gaps

Two modes:

- **Structured diff** (preferred): both sides have live structured
  reports from `coverage_gap_detector`. Produces `closed`, `opened`,
  and a `summary_delta` with the per-severity count changes.
- **Committed-markdown fallback**: git-ref snapshots can only see the
  `gap-reports/*.md` files, which are not structured. The tool
  honestly reports `structured diff unavailable` and points the
  reviewer at those markdown files + the working-tree gap detector.

### Comparison confidence

The block `comparison_confidence` has:

```yaml
comparison_confidence:
  level: high | medium | low
  reasons:
    - "..."
```

Downgrade triggers:

| Condition | Effect |
|---|---|
| Baseline snapshot has no usable data | `low` |
| Head snapshot has no usable data | `low` |
| Baseline has zero claims | `low` |
| Baseline `provenance_quality` is not `full` | at least `medium` |
| Head `provenance_quality` is `missing` | at least `medium` |
| Baseline `verdict_bucket` is `None` or `unknown` | at least `medium` |
| Any parse errors from either snapshot | reasons appended |

This is how the tool honors the rule *"be conservative and explicit
when comparison confidence is limited"*. A consumer (dashboard,
agent, human) should always read `comparison_confidence` before
trusting any delta.

### Snapshot integrity

Every diff also exposes the raw errors each snapshot collected while
loading — missing files, YAML parse errors, and so on — under
`baseline.errors` and `head.errors`. Silent failure is never the
answer; the errors surface in both the structured form and the
Markdown summary.

## Reproducibility

Relative refs like `HEAD~2` resolve to their short SHA at diff time
and get stamped into the output as `from_sha` / `to_sha`. A committed
diff artifact from yesterday still points to the exact commit it
meant, even after HEAD has moved.

## Typical workflow

A re-eval usually looks like:

```bash
# 1. Record the pre-change state
git log --oneline -1             # e.g. f62b2d7

# 2. Rerun the evaluation: update claims, add runs, rewrite the verdict
# ... do actual eval work ...

# 3. Generate the diff and commit it next to the new verdict
scripts/reeval_diff.py repos/owner--repo \
    --from f62b2d7 \
    --output repos/owner--repo/diffs/2026-04-20-f62b2d7_to_working

git add repos/owner--repo
git commit -m "eval(owner/repo): re-run"
```

The committed `diffs/<date>-<from>_to_working/` directory is the
durable record of what moved.

## Partial baseline reality

None of the five repos currently evaluated in this tree have
`captured: true` run-level provenance on their baseline snapshots.
That is the honest state. The Re-Eval Diff tool **does not hide it**:

```
Comparison confidence: medium
  - baseline provenance quality is 'missing' — changes attributed to
    'HEAD~1' may be historical artifacts, not genuine eval movement
```

Reviewers reading a diff against one of these baselines should know
up front that any "movement" might reflect the eval apparatus getting
stricter, not the repo changing. That is exactly the information
needed to make a trustworthy judgment.

## What re-eval diff does NOT do

- **It does not rewrite history.** Baselines with partial provenance
  stay partial. Running `append-provenance.sh` on old runs retroactively
  is a separate, explicit step.
- **It does not infer intent.** If a claim id changes from `claim-001`
  to `claim-101`, the tool sees a removed + an added claim. A human
  has to recognize the rename.
- **It does not replace the verdict calculator.** A diff shows movement;
  `verdict_calculator.py` still decides what bucket the new state
  deserves.

## Example worked diffs

Every evaluated repo in this tree has a concrete example at:

```
repos/<slug>/diffs/2026-04-07-pre-archetype_to_working/
    diff.json        # machine-readable
    diff.yaml        # source of truth
    summary.md       # human summary
```

These compare HEAD~2 (the Phase 2.4 commit, before archetypes were
stamped) against the working tree at the moment the Phase 3 prep was
committed. Every one of them correctly surfaces the `archetype:
None -> <name>` change and honestly downgrades confidence because
the baseline runs have no captured provenance.
