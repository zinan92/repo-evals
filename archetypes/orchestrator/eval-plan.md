# Eval Plan — orchestrator

This is a starter plan for a repo that coordinates multiple downstream
tools or skills.

> **Structural reminder.** Orchestrators should use `areas/` — set
> `uses_areas: true` in `repo.yaml` and scaffold one area per downstream
> capability. The orchestrator-level claim map here is only for routing,
> propagation, and end-to-end flow.

## What This Repo Claims

- Routing rule 1:
- Routing rule 2:
- End-to-end flow:

## What We Will Validate

### Orchestration layer (this file)

- Routing: every documented routing rule sends input to the correct downstream
- End-to-end happy path: full pipeline from initial input to final output
- Error propagation: induced downstream failures surface at the orchestrator boundary
- Partial failure: partial successes are honestly reported, not dressed up as full success

### Downstream layer (under areas/<slug>/)

- Each downstream capability has its own claim map and runs
- Each area gets its own verdict

## Real Inputs We Will Use

- Input A (exercises routing rule 1):
- Input B (exercises routing rule 2):
- Input C (exercises end-to-end):

Prefer fixtures from `fixtures/registry.yaml` with archetype filter set
to `orchestrator`.

## How Many Times We Will Test

- Each routing rule: at least once
- Happy path: at least 2 runs on different inputs
- Error propagation: at least 1 induced failure per downstream
- Per-area: see `areas/<slug>/plans/*.md`

## What Counts As Passing

- Routing is correct for every documented rule
- End-to-end happy path produces the promised final output
- Induced failures surface with enough info to identify the failing downstream
- Partial failures are labeled, not hidden
- Every area has at least one `passing` run

## If Everything Passes, What We Can Trust

- Minimum trust level: `usable` — at least one end-to-end run and one error trace
- Stretch trust level: `reusable` — every area covered, every routing rule validated
- Remaining risk: downstream drift, rare routing edge cases, unhandled partial-failure patterns
