# Eval Plan — hybrid-skill

This is a starter plan for a repo with both deterministic support code
and an LLM-driven core user value.

> **Ceiling reminder.** A hybrid-skill whose core user-facing layer is
> untested caps the overall verdict at `usable`, no matter how clean
> the support layer is. This is the rule content-extractor, visual-explainer,
> and frontend-slides all hit.

## What This Repo Claims

Split the claims into two buckets explicitly — **support** and **core**.

### Support claims (deterministic)
- Claim 1:
- Claim 2:

### Core claims (LLM-driven user value)
- Claim 101:
- Claim 102:

## What We Will Validate

### Support layer

- Install from a clean environment
- Every shipped template renders
- SKILL.md references resolve
- Support scripts fail transparently

### Core layer

- At least one real agent session per README-promised capability
- Produced artifacts compared against the SKILL.md quality contract
- Anti-slop rules compared against actual output
- Repeatability: run the same prompt at least twice

## Real Inputs We Will Use

- Input A:
- Input B:
- Input C:

Prefer fixtures from `fixtures/registry.yaml` (see `hybrid-skill` archetype).

## How Many Times We Will Test

- Support checks: once per commit
- Core live runs: at least 2 independent agent sessions per capability

## What Counts As Passing

- Support: zero failed deterministic checks
- Core: produced artifact scores ≥ N/M on the quality contract, anti-slop clean, repeat run stays in the same quality band

## If Everything Passes, What We Can Trust

- Minimum trust level: `usable` — support strong, core unverified
- Stretch trust level: `reusable` — core verified across ≥2 capabilities with repeatability
- Remaining risk: agent-runtime drift, prompt-model compatibility, rare-scenario slop
