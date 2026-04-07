# Eval Plan — prompt-skill

This is a starter plan for a repo whose user value lives in prompt
material (SKILL.md, references, templates). Replace every placeholder.

> **Ceiling reminder.** A prompt-skill repo whose core LLM-driven layer
> is untested caps the overall verdict at `usable`. Scanning SKILL.md
> references and frontmatter is necessary but not sufficient.

## What This Repo Claims

- Claim 1:
- Claim 2:
- Claim 3:

## What We Will Validate

Two validation layers — both are required for a verdict above `usable`:

### Static layer (support)

- SKILL.md frontmatter parses cleanly
- Every relative reference in SKILL.md resolves
- README capabilities ↔ skill workflow coverage table
- Available commands ↔ actual files

### Live layer (core)

- At least one real agent session executing the skill end-to-end
- Transcript + produced artifacts preserved under `runs/.../artifacts/`
- Artifact compared against the SKILL.md quality contract
- Anti-slop rules the skill declares compared against what it produced

## Real Inputs We Will Use

Prefer fixtures from `fixtures/registry.yaml`:

- Input A:
- Input B:

## How Many Times We Will Test

- Static checks: run once per commit
- Live runs: at least 2 independent agent sessions

## What Counts As Passing

- Static: zero unresolved references, zero missing files, every README capability mapped
- Live: produced artifact scores ≥ N/M on the quality contract checklist, anti-slop clean

## If Everything Passes, What We Can Trust

- Minimum trust level: `usable` — structure is real but core untested
- Stretch trust level: `reusable` — at least 2 live runs pass quality contract
- Remaining risk: rare scenarios, adversarial inputs, agent-runtime drift
