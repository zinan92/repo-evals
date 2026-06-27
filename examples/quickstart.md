# Quickstart Example

Use this as the first smoke test after installing the skill.

## User Prompt

```text
Evaluate https://github.com/owner/repo against its README promises. Write the result in Chinese, and tell me whether I should adopt it.
```

## Expected Flow

```bash
scripts/new-repo-eval.sh owner/repo skill
$EDITOR repos/owner--repo/repo.yaml
$EDITOR repos/owner--repo/claims/claim-map.yaml
python3 scripts/coverage_gap_detector.py repos/owner--repo
python3 scripts/render_verdict_html.py owner--repo --lang zh
python3 scripts/build_master_dashboard.py
```

## Expected Artifacts

- `repos/owner--repo/repo.yaml`
- `repos/owner--repo/claims/claim-map.yaml`
- `repos/owner--repo/verdicts/<date>-final-verdict.md`
- `repos/owner--repo/verdicts/<date>-verdict.html`
- `dashboard/all-evals.html`

## Acceptance Check

The final answer should include:

- score and reader-facing category from `scripts/verdict_calculator.py`
- the top evidence gaps, not a vague impression
- a link to the rendered HTML dossier
- a clear "use / avoid / use only for self" recommendation

If the eval only used static evidence, the visible category must not outrank
the final bucket ceiling. For example, a raw score of 80 can still render as
`Available` when the core layer has not been fully exercised.
