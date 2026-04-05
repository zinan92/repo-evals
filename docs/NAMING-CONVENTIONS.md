# Naming Conventions

## Top-Level Repo Folder

Each evaluated repo gets exactly one folder under `repos/`.

Format:

`<owner>--<repo>/`

Examples:

- `zinan92--content-toolkit`
- `zinan92--content-downloader`
- `openai--whisper`

Why:

- Stable across time
- Safe for filesystems
- Easy to sort
- Avoids ambiguity when different owners use the same repo name

## When To Create A New Repo Folder

Create a new repo folder when:

- The GitHub repo is different
- The evaluation target is meaningfully separate
- You want a separate final verdict

Do not create a new repo folder when:

- You are just running another test cycle for the same repo
- You are testing a new scenario within the same repo
- You are evaluating a sub-capability that still belongs to the same repo

Those should go inside the existing repo folder.

## Standard Repo Layout

```text
repos/<owner>--<repo>/
  repo.yaml
  claims/
    claim-map.yaml
  plans/
    YYYY-MM-DD-eval-plan.md
  verdicts/
    YYYY-MM-DD-final-verdict.md
  fixtures/
  runs/
    YYYY-MM-DD/
      run-<slug>/
  areas/
```

## When To Create `areas/`

Create `areas/` only when the repo is complex enough that one flat plan becomes unreadable.

Create `areas/` when at least one of these is true:

1. The repo has 3 or more distinct capability clusters.
2. The repo is an orchestrator that calls multiple downstream tools or repos.
3. Different parts of the repo need different fixtures, evidence, or pass criteria.
4. One part can pass while another part fails, and you want that reflected clearly.

Do not create `areas/` for a simple single-purpose repo.

## Area Folder Names

Format:

`areas/<area-slug>/`

Examples:

- `areas/orchestration`
- `areas/content-downloader`
- `areas/content-rewriter`
- `areas/content-extractor`

Rules:

- Use lowercase
- Use hyphens
- Keep names capability-oriented
- Do not include dates in area folder names

## Run Folder Names

Runs are nested under a day folder.

Format:

`runs/YYYY-MM-DD/run-<short-slug>/`

Examples:

- `runs/2026-04-05/run-basic-pdf-to-ppt`
- `runs/2026-04-05/run-three-random-pdfs`
- `runs/2026-04-05/run-orchestration-smoke`

Rules:

- The date folder groups a testing session
- The run slug says what was actually tested
- Keep the slug short and human-readable

### Standard Run Layout

```text
runs/YYYY-MM-DD/run-<slug>/
  run-summary.yaml
  business-notes.md
  logs/
  artifacts/
  screenshots/
```

Use:

- `run-summary.yaml` for the structured technical record
- `business-notes.md` for plain-English observations
- `logs/` for raw execution logs
- `artifacts/` for produced outputs
- `screenshots/` for visual evidence when useful

## Plan File Names

Format:

`plans/YYYY-MM-DD-eval-plan.md`

If you need multiple plans on the same day:

`plans/YYYY-MM-DD-eval-plan-<scope>.md`

Examples:

- `plans/2026-04-05-eval-plan.md`
- `plans/2026-04-05-eval-plan-orchestration.md`

## Verdict File Names

Format:

`verdicts/YYYY-MM-DD-final-verdict.md`

If you need an area-specific verdict:

`areas/<area-slug>/verdicts/YYYY-MM-DD-area-verdict.md`

## Fixture Naming

Use fixture names that explain the business case, not just the file type.

Good:

- `three-page-product-brochure.pdf`
- `noisy-short-podcast.mp3`
- `mixed-language-interview.mp4`

Bad:

- `test1.pdf`
- `sample-final-v2.mp3`
- `input.mov`
