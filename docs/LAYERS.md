# Layer model: atom · molecule · compound

> **Status:** v1, introduced 2026-05-02.
> **Why:** archetypes describe *shape* (CLI, adapter, orchestrator). Layers
> describe *composition depth*. Two repos can share an archetype but need
> very different evaluations because one is a single deterministic unit
> and the other is an LLM-driven coordinator.

## TL;DR

| Layer | One-line definition | Eval levels that apply |
|---|---|---|
| **Atom** | Single responsibility. Same input → same output (within tolerance). Does not call other *skill-level* units. | atom only |
| **Molecule** | 2–10 atoms wired by **predefined** orchestration. Call order, stop conditions, handoff triggers all written into code/config — **not** decided by an LLM at runtime. | atom + molecule |
| **Compound** | Coordinates multiple molecules where the **call graph is decided at runtime** by an LLM (or human-in-the-loop). Needs goal/quality judgment to be useful. | atom + molecule + compound |

## Why levels stack

If a molecule uses three atoms and one of them is broken, the molecule
cannot be reusable — even if its own workflow code is fine. So a
molecule's eval must include atom-level evidence for each atom it
depends on. Same logic propagates up to compound.

But we **do not re-test** atoms inside a molecule's eval. We require
that each declared atom dependency has a passing eval somewhere
(co-located in the same repo, or in another repo with its own eval).
This mirrors how SBOM / supply-chain attestations work.

For compounds, the call graph cannot be enumerated up-front because
the LLM picks routes at runtime. So compound eval is **scenario-driven
+ trace-observed**: you run real scenarios, observe which sub-skills
were called, and require each observed sub-skill to have a passing
eval.

## Atom-level eval dimensions

These apply to **every** repo, regardless of layer — every layer
contains atoms.

| Dimension | Question |
|---|---|
| **Input contract** | Does the atom reject malformed input with a clear, actionable error? |
| **Output contract** | Does the output shape match what the README/SKILL.md claims? |
| **Determinism** | Same input → same output within stated tolerance. (LLM atoms: tolerance is "structurally equivalent", not byte-equal.) |
| **Idempotence** | Re-running with the same input produces the same observable end state. |
| **No skill-level callouts** | The atom does not invoke other documented skills — only primitives (LLM API, stdlib, third-party packages, OS). |
| **Failure mode clarity** | Each documented failure mode produces a distinct, recognisable error. |

## Molecule-level eval dimensions

Apply to molecule + compound. Atom dimensions still apply for each
atom this molecule contains.

| Dimension | Question |
|---|---|
| **Workflow correctness** | An end-to-end happy path runs from initial input to final output. |
| **Declared call graph** | The atoms the molecule documents as using are in fact the ones it calls. No undocumented hidden dependencies. |
| **Stop conditions** | Documented stop conditions (success, max-retries, timeout) actually trigger and halt cleanly. |
| **Handoff points** | When the molecule should hand back to a human, it does so at the documented trigger — not earlier, not later. |
| **Atom evidence** | Every declared atom dependency has a passing atom-level eval (referenced or co-located). |
| **Error propagation** | A downstream atom failure surfaces at the molecule boundary with enough info to act, instead of being swallowed. |
| **Partial failure handling** | When one atom fails, the molecule does not silently produce an incomplete "success". |

## Compound-level eval dimensions

Apply to compound only. Molecule + atom dimensions still apply for
each molecule this compound contains.

Compound eval is **scenario-driven**. You cannot enumerate the call
graph up-front because the LLM decides at runtime.

| Dimension | Question |
|---|---|
| **Goal achievement** | In N real scenarios, does the system reach a useful end state — not just "ran without error"? |
| **Direction judgment** | When the goal is ambiguous, does the system ask, pick a reasonable default, or wedge? |
| **Quality judgment** | Does the system stop when output is good enough, instead of overshooting or stopping too early? |
| **Meaningful autonomy** | When left to drive itself, does it actually make progress, or does it spin / loop / hallucinate? |
| **Human handoff timing** | When the system asks for help, is that the right moment? |
| **Observed call graph** | Record which sub-molecules got called during each scenario, then verify each has a passing molecule-level eval. |
| **Failure recovery** | When a sub-call fails, does the LLM adapt (try alternative, ask user) or wedge? |

## How to evaluate a compound (the experimental playbook)

Because the call graph is runtime-determined, compound eval needs the
human in the loop. Each compound repo's eval should include a
`compound-experiments.md` file with at least three scenarios in the
shape:

```markdown
### Scenario {n}: {one-line goal}

**System prompt / starting message:**
> {the exact prompt to give the system}

**What to watch for:**
- {behavior 1 — pass/fail criteria}
- {behavior 2 — pass/fail criteria}
- {behavior 3 — pass/fail criteria}

**Sub-molecules expected to be called:** {list, or "TBD — observe"}

**Verdict log:**
| Date | Run | Goal reached? | Right sub-molecules? | Notes |
|---|---|---|---|---|
| YYYY-MM-DD | 1 |   |   |   |
```

Each compound repo's per-repo dashboard page renders these scenarios
as a checklist so the operator can fill them in over multiple sessions.

## Layer ↔ archetype heuristic

Layer is an explicit field in `repo.yaml`. The default suggestion based
on archetype:

| Archetype | Default layer | Notes |
|---|---|---|
| `pure-cli` | `atom` | Single deterministic CLI. |
| `adapter` | `atom` or `molecule` | Atom if it wraps one platform; molecule if it routes across several with internal logic. |
| `api-service` | `molecule` | Usually a fixed pipeline: route → handler → response. Becomes compound only if the service hosts an agent. |
| `prompt-skill` | `atom` or `molecule` | Atom if SKILL.md prompts one task; molecule if it chains documented sub-tasks. |
| `hybrid-skill` | `molecule` | LLM + supporting deterministic code is by definition >1 unit. |
| `orchestrator` | `molecule` or `compound` | Molecule if the routing is rule-based; compound if an LLM picks routes. |

These are heuristics. The author sets `layer:` explicitly in
`repo.yaml`; the dashboard renders whatever is set there.

## Ceiling rules (interaction with verdict_calculator)

| Layer | Ceiling rule |
|---|---|
| Atom | No layer-based ceiling. Determinism + contract evidence is the bar. |
| Molecule | Cannot exceed `usable` if the declared atom dependencies do not have passing atom-level eval evidence. |
| Compound | Cannot exceed `usable` without at least one fully logged compound scenario. Cannot exceed `reusable` without three. |

These are **additive** to the existing hybrid-cap rule already in
`verdict_calculator.py`. Whichever rule produces the lower ceiling
wins.
