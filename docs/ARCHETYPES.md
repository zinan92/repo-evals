# Archetypes

Not every repo should be evaluated the same way. A deterministic CLI
has different failure modes than an LLM-driven skill, and an adapter
wrapping an external API has different risks than an orchestrator
chaining multiple downstream tools.

Archetypes let evaluators pick a scaffold that already asks the right
questions for a given repo shape.

## Six archetypes

| Archetype | Core user value | Default ceiling | Verdict-calculator hybrid cap? |
|---|---|---|---|
| `pure-cli` | Deterministic CLI output from arguments | none | no |
| `prompt-skill` | LLM output following a SKILL.md / prompt | `usable` when core untested | yes |
| `hybrid-skill` | LLM output plus supporting deterministic code | `usable` when core untested | yes |
| `adapter` | Wrapping an external platform or API cleanly | none | no |
| `orchestrator` | Coordinating multiple downstream tools end-to-end | none | no (but `uses_areas: true` is expected) |
| `api-service` | HTTP endpoints with documented shape / auth / errors | none | no |

The verdict calculator (`scripts/verdict_calculator.py`) applies the
hybrid cap to `prompt-skill`, `hybrid-skill`, and `orchestrator`. See
`HYBRID_ARCHETYPES` in that file for the authoritative list.

## Directory layout

```
archetypes/
├── README.md
├── pure-cli/
│   ├── archetype.yaml       # metadata: ceiling, dimensions, evidence, default claims
│   ├── claim-map.yaml       # starter claim map for this archetype
│   └── eval-plan.md         # archetype-flavored plan template
├── prompt-skill/ ...
├── hybrid-skill/ ...
├── adapter/ ...
├── orchestrator/ ...
└── api-service/ ...
```

## Discovery

```bash
scripts/archetypes.py list
scripts/archetypes.py show hybrid-skill
scripts/archetypes.py show hybrid-skill --json
scripts/archetypes.py validate                    # schema-check all archetypes
```

## Using an archetype for a new repo

```bash
scripts/new-repo-eval.sh nicobailon/visual-explainer --archetype hybrid-skill
```

What this does:

1. Creates `repos/nicobailon--visual-explainer/` as usual
2. Copies `archetypes/hybrid-skill/claim-map.yaml` → `repos/.../claims/claim-map.yaml`
3. Copies `archetypes/hybrid-skill/eval-plan.md` → `repos/.../plans/<date>-eval-plan.md`
4. Stamps `archetype: hybrid-skill` into `repos/.../repo.yaml`

Without `--archetype`, the command falls back to the generic templates
from `templates/repo/`. Existing workflows keep working.

## Adopting an archetype retroactively

Existing repos (created before Phase 2) can opt in by editing two things:

1. In `repos/<slug>/repo.yaml`, set `archetype: <name>`
2. Optionally cherry-pick archetype-specific prompts into the existing
   `claims/claim-map.yaml`

That's all the verdict calculator needs to start applying archetype-aware
ceiling rules on the next re-eval. No scaffolding churn, no schema
migration.

## Metadata contract

Every archetype's `archetype.yaml` must have:

| Field | Purpose |
|---|---|
| `name` | Must match the directory name |
| `description` | When to use this archetype (plain English) |
| `default_verdict_ceiling` | `none` or a string that describes the ceiling — the calculator reads the archetype name, not this string, but it's the canonical human explanation |
| `evaluation_dimensions` | List of what a good plan must cover |
| `recommended_evidence` | List of artifacts a reviewer should expect |
| `default_claim_prompts` | The critical questions a claim map should answer |

Each archetype's `claim-map.yaml` must:

- have a non-empty `claims:` list
- have at least one `critical` priority claim
- keep every claim at `status: untested` (starter status)

These invariants are enforced by `scripts/archetypes.py validate` and
by `tests/test_archetypes.py`.

## Adding a new archetype

1. Create `archetypes/<name>/archetype.yaml` following the metadata contract
2. Create `archetypes/<name>/claim-map.yaml` with at least one critical claim
3. Create `archetypes/<name>/eval-plan.md`
4. Add `<name>` to `fixtures/registry.yaml` under `enums.applicable_archetypes`
5. If the archetype should inherit the hybrid ceiling, add it to
   `HYBRID_ARCHETYPES` in `scripts/verdict_calculator.py`
6. Update `archetypes/README.md` and this doc's table
7. Run `scripts/archetypes.py validate` and `python3 tests/test_archetypes.py`
