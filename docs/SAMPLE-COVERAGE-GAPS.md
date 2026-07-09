# Sample Coverage Gaps

Last checked: 2026-07-09, after rebuilding `dashboard/all-evals.html` from 52 evaluated repos.

## What the corpus covers well

- Layer spread is now useful: 11 atom, 30 molecule, 11 compound.
- Content and agent/dev tooling are well represented: content-oriented repos dominate, with a smaller but real finance/trading slice.
- The newer dossiers usually include the product-view fields that make the verdict reader-facing: persona, scenario, without/with, cost, examples, workflow diagram, similar repos.
- The current scoring model has enough negative cases to show ceilings: 42 Available, 10 Don't use, 0 Production, 0 Risky in the regenerated dashboard.

## Gaps to handle next

- Live-run evidence is still thin: 18 repos have no committed `run-summary.yaml`, and 41 repos still have at least one untested claim.
- `business_category` has historical schema drift. Some older repo files used a bilingual prose object instead of the controlled `content | finance | development` value. The renderer now infers the coarse domain, but the YAML should be normalized over time.
- Workflow modeling is not universal: 3 repos still have no `workflow_diagram`, so their verdicts cannot show how the system actually works.
- Similar-repo comparison is close but incomplete: 6 repos have no `similar_repos`, which weakens the "what should I use instead?" section.
- Older dossiers still have weaker adoption guidance: 33 repos are missing `product_view.best_for`. This is less severe now because persona/scenario fields often cover the same job, but it makes fallback rendering uneven.
- The use-case tag vocabulary has outgrown the dashboard filter. Many real tags now exist outside the original controlled list, such as X/Twitter growth, RSS, social-card generation, and finance-news workflows.

## Design implications

- Keep "checked vs still missing" visible near the score. The corpus still has many static-only evaluations.
- Treat `Available` as "usable with bounds", not a production endorsement. The current dashboard has high numeric scores that are still category-capped by final-bucket ceilings.
- Long workflows need scrollable diagrams with fixed node text size. Shrinking the whole SVG hides the exact runtime decision points the verdict is supposed to explain.
- The master dashboard must be regenerated whenever new repo directories are added. GitHub Pages does not build the catalog dynamically.

## Next model improvements

- Add a first-class `evidence_level` field in `repo.yaml` or computed output: static-only, partial live, full live, unsafe-to-run.
- Split adoption blockers into legal, runtime, platform-policy, maintainer-risk, and missing-live-run instead of collapsing all gaps into one `watch_out` paragraph.
- Expand dashboard use-case filters from the current fixed list to data-driven top tags with aliases.
- Add a corpus health check command that fails when a repo has `repo.yaml + claim-map.yaml` but no verdict HTML, no workflow diagram, or a stale dashboard entry.
