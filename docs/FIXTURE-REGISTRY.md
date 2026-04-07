# Fixture Registry

A shared catalog of reusable test inputs so evaluators stop re-inventing
fixtures every time they start a new repo eval.

The registry lives at `fixtures/registry.yaml` and is the source of
truth — `scripts/fixtures.py` is only a convenience CLI on top of it.
Anyone (human or agent) can read `registry.yaml` directly without
running any tool.

## Directory layout

```
fixtures/
├── registry.yaml              # the catalog (this is the source of truth)
└── assets/                    # in-repo fixture payloads
    ├── markdown-readme-small-en.md
    ├── html-slide-deck-minimal.html
    └── json-content-item-valid.json
```

Per-repo fixtures are still allowed at `repos/<slug>/fixtures/`. The
shared registry is for fixtures that **multiple** repos can reuse.

## Entry schema

Each entry under `fixtures:` in `registry.yaml`:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable identifier. Use `kind-topic-variant` (e.g. `markdown-readme-small-en`). Must be unique. |
| `description` | string | Plain-English explanation of *what this fixture is for*. |
| `media_type` | enum | `text` / `markdown` / `html` / `json` / `yaml` / `image` / `audio` / `video` / `pdf` / `archive` / `code` / `url` / `mixed` |
| `language` | string | ISO 639-1 code (`en`, `zh`, ...), or `mixed`. |
| `complexity` | enum | `trivial` / `simple` / `moderate` / `complex` |
| `applicable_archetypes` | list | Which repo archetypes this fixture fits: `pure-cli`, `prompt-skill`, `hybrid-skill`, `adapter`, `orchestrator`, `api-service` |
| `privacy` | enum | `public` / `synthetic` / `sanitized` / `restricted` |
| `known_caveats` | string | Honest list of what this fixture will NOT catch, or how it can silently rot. Required for anything non-trivial. |
| `location` | string | `fixtures/assets/<file>` for in-repo, or `external:<url-or-path>` for things that cannot be committed. |
| `added_at` | string | `YYYY-MM-DD` of first addition. |

The file also declares allowed enums under `enums:` — the CLI uses these
to validate new entries.

## CLI

```bash
# Discovery
scripts/fixtures.py list
scripts/fixtures.py list --archetype hybrid-skill
scripts/fixtures.py list --media-type markdown --language en
scripts/fixtures.py find --complexity moderate --privacy public

# Detail
scripts/fixtures.py show markdown-readme-small-en
scripts/fixtures.py show markdown-readme-small-en --json

# Validation (CI-friendly)
scripts/fixtures.py validate

# Check that registry:<id> references in a run actually resolve
scripts/fixtures.py check-refs repos/owner--repo/runs/2026-04-07/run-smoke/run-summary.yaml
```

## Referencing a fixture from a run

In `run-summary.yaml`:

```yaml
fixtures:
  - "registry:markdown-readme-small-en"
  - "registry:json-content-item-valid"
  - "local: repos/owner--repo/fixtures/very-specific-input.txt"
```

The `registry:` prefix is the portable, auditable form. `check-refs`
validates every such reference against `registry.yaml`.

## Privacy rules

- `public` — safe to commit; real public data with no PII.
- `synthetic` — fabricated to match real shape; safest default for new assets.
- `sanitized` — real data with identifying fields removed; document *how* it was sanitized in `known_caveats`.
- `restricted` — must never be committed; use `location: "external:..."` and document retrieval separately.

## Naming rule

```
<kind>-<topic>-<variant>
```

Examples:

- `markdown-readme-small-en`
- `json-content-item-valid`
- `video-url-douyin-public`
- `html-slide-deck-minimal`

Keep ids **short, descriptive, and irreversible** — renaming an id breaks
every run that referenced it. Prefer adding a new fixture over renaming.

## When to add a fixture

- You're about to invent an input from scratch and at least one other repo might need something similar.
- A bug case reproduces on a specific input that is worth preserving.
- You want a deliberately imperfect input to catch "always passes" tools.

## When NOT to add a fixture

- The input is specific to one repo's internal details.
- The input contains secrets, credentials, or real user PII.
- You haven't actually used it yet in a run.

## Follow-up

The registry only covers metadata today. Phase 3 will add re-eval diff
mode, at which point we may want to stamp a content hash for each
in-repo asset so drift is detectable. For now, Git history serves that
purpose.
