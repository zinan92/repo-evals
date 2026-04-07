# Eval Plan — adapter

This is a starter plan for a repo that wraps an external platform or API.

## What This Repo Claims

List each supported platform or external system explicitly.

- Platform 1:
- Platform 2:
- Platform 3:

## What We Will Validate

- Happy path on every listed platform (at least one real input each)
- Unsupported input → loud error (not silent success)
- Auth failure → actionable error
- Shape conformance across platforms (same normalized output)
- Dedup: same input twice → second run is a no-op
- Upstream drift: at least one adversarial "interface changed" simulation

## Real Inputs We Will Use

Prefer fixtures from `fixtures/registry.yaml` with `applicable_archetypes`
containing `adapter`:

- Input A:
- Input B:
- Input C:

## How Many Times We Will Test

- Core path: once per platform
- Dedup check: 2 consecutive runs
- Failure modes: once per documented failure class

## What Counts As Passing

- Every platform produces a non-empty normalized output
- Every output parses under the same schema
- Every unsupported input fails loudly with an actionable error
- Second dedup run writes no new files / appends nothing new
- At least one simulated upstream drift scenario fails loudly

## If Everything Passes, What We Can Trust

- Minimum trust level: `usable` — one platform works end-to-end
- Stretch trust level: `reusable` — every claimed platform works and dedup is real
- Remaining risk: untested platforms, rare upstream quirks, cold-start auth flows
