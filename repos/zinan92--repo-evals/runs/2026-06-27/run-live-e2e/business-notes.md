# repo-evals live e2e onboarding check

This run validates the onboarding path behind `claim-010`: a clean clone-style
workspace can scaffold a new repo evaluation, fill the minimum dossier inputs,
render a bilingual HTML dossier, and rebuild the dashboard.

Result: passed.

Evidence:

- `logs/live-e2e.txt` records the executed commands and outputs.
- `artifacts/demo-repo.yaml` preserves the filled demo dossier input.
- `artifacts/demo-claim-map.yaml` preserves the filled demo claim map.
- `artifacts/demo-verdict.html` preserves the rendered dossier.

Scope note: this is an onboarding smoke test, not a full evaluation of a real
third-party repository. It proves the documented path can produce an artifact;
it does not replace deeper adoption-quality testing on an unseen real repo.
