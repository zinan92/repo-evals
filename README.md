# Repo Evals

Claim-first evaluation harness for repositories, with a strong bias toward skill and capability repos.

This repo separates evaluation into two layers:

- Business-readable evaluation plans
- Technical evidence and execution records

Every evaluated repo ends with one final reliability bucket:

- `unusable`
- `usable`
- `reusable`
- `recommendable`

## What Lives Here

- `docs/`
  Framework rules, naming conventions, and verdict definitions.
- `templates/`
  Reusable starting files for new repo evaluations.
- `scripts/`
  Bootstrap helpers for new repo and area folders.
- `repos/`
  One subfolder per evaluated repo.

## Core Principles

1. Evaluation is claim-first.
   We test what the repo promises, not just what commands exist.
2. Business readability matters.
   Every repo gets an `Eval Plan` that a non-technical reader can review.
3. Technical evidence is preserved.
   Every run should leave behind artifacts, logs, and judgments.
4. Reliability must be classified.
   Every repo ends in one bucket: `unusable`, `usable`, `reusable`, or `recommendable`.

## Standard Flow

1. Create a repo folder under `repos/`.
2. Capture repo metadata in `repo.yaml`.
3. Extract claims into `claims/claim-map.yaml`.
4. Write a business-readable plan in `plans/YYYY-MM-DD-eval-plan.md`.
5. Execute one or more runs and store technical evidence under `runs/`.
6. Write a final verdict under `verdicts/`.

## Bootstrap Commands

```bash
# New repo evaluation
scripts/new-repo-eval.sh owner/repo skill

# Add an area for a complex repo
scripts/new-area.sh owner--repo area-slug

# Create a run folder for one concrete test pass
scripts/new-run.sh owner--repo run-slug
scripts/new-run.sh owner--repo run-slug area-slug
```

## Folder Rule Of Thumb

- Use only the repo root if the target is single-purpose.
- Add `areas/` when the repo has multiple independently meaningful capability clusters.
- For orchestration repos, create one area for orchestration itself and one area per major downstream capability.

See [`docs/NAMING-CONVENTIONS.md`](/Users/wendy/work/repo-evals/docs/NAMING-CONVENTIONS.md) and [`docs/FRAMEWORK.md`](/Users/wendy/work/repo-evals/docs/FRAMEWORK.md) for the full rules.
