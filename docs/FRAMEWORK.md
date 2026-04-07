# Evaluation Framework

## Goal

Make repository evaluation a first-class workflow, especially for skill, capability, and orchestration repos where quality is not captured by simple command success.

## Two-Layer Output

### 1. Business Validation

This is what a non-technical reviewer should read.

For each repo, the business layer answers:

- What does this repo claim it can do?
- Which real-world scenarios are we validating?
- How many times are we testing each scenario?
- What counts as passing?
- If all planned tests pass, how much should we trust this repo?

The main artifact is:

- `plans/YYYY-MM-DD-eval-plan.md`

### 2. Technical Testing

This is where execution evidence is preserved.

For each run, the technical layer stores:

- Inputs and fixtures used
- Commands or agent flows executed
- Raw outputs and produced artifacts
- Failures, retries, and anomalies
- Structured run summaries
- Provenance for who ran the evaluation, when, and against which repo revision

The main artifact lives under:

- `runs/YYYY-MM-DD/run-<slug>/`

## Evaluation Sequence

1. Capture the target repo and its scope.
2. Extract claims from `README`, `SKILL.md`, docs, examples, and failure notes.
3. Group claims into capability areas if needed.
4. Write a business-readable eval plan.
5. Execute planned test runs.
6. Save technical evidence for each run.
7. Decide the final reliability bucket.

## Provenance Is Mandatory

An eval is not fully auditable unless a later reviewer can answer:

- Which commit of the target repo was evaluated?
- Which commit of `repo-evals` defined the framework at the time?
- Who or what ran the evaluation?
- Which terminal or agent session produced the result?

Every run summary should capture, when available:

- `repo_evals_commit`
- `target_repo_ref`
- `target_repo_commit`
- `runner`
- `agent`
- `model`
- `terminal_session_id`
- `agent_session_id`
- `evaluated_at`

If an older run did not capture these, mark provenance as partial instead of pretending it exists.

## Evidence Must Be Portable

Technical evidence should remain reviewable from GitHub alone.

That means:

- Prefer paths relative to the run folder, not `/tmp/...`
- Copy or mirror representative artifacts into `runs/.../artifacts/`
- Treat local scratch paths as transient implementation details, not durable evidence

## What To Evaluate For Skill Repos

Every skill-oriented evaluation should cover these dimensions:

### Core Outcome

Can it do the main thing it claims to do?

### Scenario Breadth

Can it handle different but realistic inputs, not just one lucky case?

### Repeatability

If we run the same workflow multiple times, do we get consistently usable outcomes?

### Failure Transparency

When it cannot complete the task, does it fail clearly instead of pretending to succeed?

## Reliability Buckets

The final verdict must land in exactly one bucket.

### `unusable`

The repo fails its core claim, works only accidentally, or produces outputs too poor to rely on.

### `usable`

The repo can complete its main job at least once, but confidence is still limited.
Good for experimentation, not yet good for routine use.

### `reusable`

The repo succeeds across multiple realistic scenarios with acceptable consistency.
Good for repeated internal use.

### `recommendable`

The repo is stable, clear about its boundaries, and reliable enough that you would feel comfortable recommending it to others.

## Decision Rule

Passing all tests in a weak plan does not justify a strong verdict.
The verdict depends on both:

- How well the repo performed
- How demanding the eval plan was

That means:

- A repo can pass all tests and still only be `usable`
- A hybrid repo cannot score above the strongest layer that was actually validated
- A repo should not be called `recommendable` unless the plan included multiple realistic scenarios and repeatability checks

## Hybrid Repos

Some repos have multiple evidence layers.

Common example:

- A prompt or skill layer that defines the real user-facing value
- A deterministic script layer that only supports that value

For these hybrid repos:

- If only the support layer is tested, the verdict can describe that support layer as strong
- But the overall repo verdict is capped by the untested core layer

Practical rule:

- Untested core user-facing layer → overall verdict capped at `usable`
- Tested core layer across realistic scenarios → eligible for `reusable`
- Broad, repeated, trustworthy core coverage → eligible for `recommendable`
