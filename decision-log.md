# Decision Log

## 2026-07-09 repo-evals dashboard and verdict redesign

Objective: make the public repo-evals GitHub/Pages surface show the full current corpus, make verdict pages easier to decide from, and expose corpus coverage gaps without overstating confidence.

### Decisions

- Rebuilt the static corpus index instead of hand-editing `dashboard/all-evals.html`; the regenerated master dashboard now indexes 52 evaluated repos.
- Kept verdict generation template-driven in `scripts/render_verdict_html.py`; all committed verdict HTML pages should be regenerated from the same template so the design stays consistent.
- Replaced the old four-row decision snapshot with a stronger adoption-verdict layout: primary action, next move, do-not-use boundary, and main risk.
- Made workflow diagrams support folded two-row flows and container-fit SVG scaling. This avoids the reader missing content off the right edge while keeping labels legible.
- Added `#workflow` as a stable anchor for workflow screenshots and deep links.
- Added compatibility inference for legacy `business_category` shapes. Older YAML sometimes stores a bilingual prose label instead of `content | finance | development`; generated pages now infer the coarse domain from the label plus use-case tags.
- Added real README screenshots from the generated local pages instead of more ASCII examples.
- Wrote `docs/SAMPLE-COVERAGE-GAPS.md` to record what the larger corpus still does not cover well.
- Made verdict rendering refresh `dashboard/all-evals.html` by default, and added `scripts/publish_eval.py` as the preferred one-command publish path for one or many repo evals.
- Reframed the verdict page as an adoption report rather than a technical dossier: lead with what the repo helps a user do, the boundary of trust, and whether the core promise was actually exercised.
- Moved score proof into the "Can you use it?" section for high-scoring available repos, and replaced claim cards with a scan-friendly claim evidence list.
- Let repos provide `product_view.not_for` and `product_view.main_risk` for the top decision card. This keeps the visible adoption summary user-facing when the generic evidence-derived fallback would sound stale or too technical.
- Added a high-position output-sample section. For generation-style repos, the visible order should be: repo title, concrete input summary, actual generated sample. The renderer reads `runs/<date>/<run>/artifacts/manifest.yaml` so sample galleries are evidence-backed, not decorative.
- Treat missing benchmark metrics as missing data, not zero. Evidence runs may have command/artifact/claim-outcome records without `pass_rate`, `elapsed_time_sec`, or token fields.
- For same-day follow-up runs, newest claim outcomes should win over older evidence so a successful rerun is not hidden by an earlier failed or partial attempt.

### Gotchas

- GitHub Pages serves committed static files; local publish/render commands can refresh `dashboard/all-evals.html`, but the live site changes only after those generated files are committed and pushed.
- The preferred future command is `python3 scripts/publish_eval.py <slug> --lang zh`; it renders the repo dossier with `--no-dashboard` internally and rebuilds the master dashboard once at the end.
- Re-rendering one template change updates many `repos/*/verdicts/*-verdict.html` files. That is expected for a page-template redesign, but diffs should be reviewed as generated output.
- `latest-verdict.html` files and dated `*-verdict.html` files both need to remain valid link targets.
- `business_category` schema drift can silently remove rows from dashboard domain filters if the generator expects only controlled strings.
- Long workflow SVGs should not require hidden horizontal overflow on the public page. Prefer folded layouts and fit-to-container SVG behavior, then verify labels remain readable.
- Port `8765` already had old local services in this environment, causing screenshot attempts to hit 404 pages. Use an explicit clean port when capturing visual proof.
- `run_summary.metrics` is optional in this corpus. If it is absent, the UI must say "not recorded" rather than showing 0% / 0s / 0 tokens.
- Some raw verdict archives preserve technical wording. User-facing verdict pages should translate that into adoption language instead of exposing install-command phrasing as the main recommendation.
- Sample artifacts must use paths relative to the run directory, and the verdict page links to them from `verdicts/*.html` via `../runs/...`. If generated images are not committed/published with the verdict, the gallery becomes broken even though local HTML still exists.
