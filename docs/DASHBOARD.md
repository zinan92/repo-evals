# Dashboard

`scripts/generate_dashboard.py` builds a static operator dashboard from the
existing repo-evals source of truth.

It does **not** introduce a database or any hidden state. Everything shown in the
dashboard is derived from committed files already present in this repo:

- `repos/<slug>/repo.yaml`
- `repos/<slug>/claims/claim-map.yaml`
- `repos/<slug>/runs/**/run-summary.yaml`
- `repos/<slug>/gap-reports/*.md`
- `repos/<slug>/diffs/*/diff.yaml`
- `repos/<slug>/diffs/*/summary.md`

## Why

Phase 1 made evals auditable.
Phase 2 made them more scalable and type-aware.
Phase 3 made them longitudinal.

Phase 4 makes the system operable at a glance:

- which repos are `usable` / `reusable` / `recommendable`
- which repos still have unresolved critical gaps
- which repos have weak provenance
- which repos have low-confidence or medium-confidence diffs
- what changed most recently

## Output

Run:

```bash
python3 scripts/generate_dashboard.py
```

This writes:

```text
dashboard/
  index.html
  repos/<slug>.html
  data/index.json
  data/repos/<slug>.json
  assets/style.css
  assets/app.js
```

## What the dashboard trusts

The dashboard is intentionally conservative.

It will happily surface:

- `provenance: missing`
- `comparison confidence: medium`
- `comparison confidence: low`
- missing diff data
- markdown-only baseline gap reports

It will **not** normalize those away just to make the UI look cleaner.

## Current data model

### Top-level dashboard

The generated `dashboard/data/index.json` contains:

- generation timestamp
- source commit
- aggregate stats
- one summary object per evaluated repo

### Per-repo detail

Each `dashboard/data/repos/<slug>.json` contains:

- repo metadata
- claim status summary
- run and provenance summary
- latest gap report counts + extracted critical/warning items
- latest diff summary + comparison confidence
- source file paths for drill-down
- area metadata for orchestrator-style repos

## Regeneration

Whenever repo-evals data changes:

```bash
python3 scripts/generate_dashboard.py
git add dashboard
```

## Limitations

- Gap reports are currently markdown-only baselines, so historical gap trend lines
  remain coarse until a structured gap artifact exists on both sides.
- Some repos still have missing run-level provenance, so their diff confidence is
  honestly not `high`.
- The dashboard summarizes the root claim-map for each repo. Area-level claim maps
  are linked, but not merged into the root verdict view.
