# Archetypes

Different repos need different evaluation shapes. A pure CLI should not
be evaluated the same way as an LLM-driven skill, and an adapter should
not be evaluated the same way as a full orchestrator.

This directory holds archetype-specific scaffolding used by
`scripts/new-repo-eval.sh --archetype <name>`.

## Supported archetypes

| Archetype | Core user value is ... | Typical ceiling |
|---|---|---|
| `pure-cli` | the CLI itself — deterministic output from arguments | none (can reach `recommendable`) |
| `prompt-skill` | what the LLM produces when following a prompt / SKILL.md | `usable` when core untested |
| `hybrid-skill` | LLM output AND supporting deterministic code | `usable` when core untested |
| `adapter` | wrapping an external platform or API cleanly | none — but unsupported platform handling is critical |
| `orchestrator` | coordinating multiple tools end-to-end | none — but every downstream area needs its own coverage |
| `api-service` | HTTP endpoints returning correct shape | none |

See each subdirectory's `archetype.yaml` for:

- `description` — when to use this archetype
- `default_verdict_ceiling` — baseline ceiling the verdict calculator applies
- `evaluation_dimensions` — what a good plan for this archetype must cover
- `recommended_evidence` — what artifacts a reviewer should expect to see
- `default_claim_prompts` — the critical questions a claim map should answer

## Discovery

```bash
scripts/archetypes.py list
scripts/archetypes.py show hybrid-skill
```

## Using an archetype for a new repo

```bash
scripts/new-repo-eval.sh owner/repo --archetype hybrid-skill
```

This copies the archetype's `claim-map.yaml` and `eval-plan.md` as
starting points and stamps `archetype: hybrid-skill` into `repo.yaml`.
Without the flag, scaffolding uses the generic templates from
`templates/repo/` — that path stays for backward compatibility.

## Adopting an archetype retroactively

An existing repo can adopt an archetype by editing two fields:

1. Set `archetype: <name>` in `repos/<slug>/repo.yaml`
2. Optionally merge archetype-specific claim prompts into the existing
   `claims/claim-map.yaml`

The verdict calculator already reasons over the `archetype` field for
ceiling rules, so this retrofit is all that's needed for re-evals to
start benefiting from archetype-aware rules.

## Adding a new archetype

1. Create `archetypes/<name>/archetype.yaml` with every field in the schema
2. Create `archetypes/<name>/claim-map.yaml` with archetype-critical starter claims
3. Create `archetypes/<name>/eval-plan.md` with archetype-flavored sections
4. Add the archetype name to `fixtures/registry.yaml` `enums.applicable_archetypes`
5. Update the verdict calculator's `HYBRID_ARCHETYPES` set if the new
   archetype should inherit the hybrid ceiling rule
6. Add it to the CLI test suite in `tests/test_archetypes.py`
7. Update this README table
