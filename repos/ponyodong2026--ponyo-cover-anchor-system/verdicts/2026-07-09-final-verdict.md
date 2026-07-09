# Final Verdict

## Repo

- **Name**: ponyodong2026/ponyo-cover-anchor-system
- **Version tested**: main@HEAD (2026-06-22 push), commit f03b7bc
- **Date**: 2026-07-09
- **Archetype**: prompt-skill
- **Layer**: molecule
- **Score**: 55 /100  (from `verdict_calculator.py`, not judgement)
- **Category**: 🛠 Available / 可使用
- **Tier**: 🧪 Try once (try ≥50)

## Plain English

- Outcome if adopted: Vera gets a disciplined 小红书 cover-prompt system — an explicit 信息密度 × 视觉锚点 formula, 6 template/style families (incl. real-photo doodle-outline & sunlit-scrapbook looks), a 10-point diagnosis checklist, and a copy-paste ChatGPT Image 2 prompt — that turns "make a cover" into a decided anchor/palette/type plan in seconds.
- Regret scenario: You need it for Park's 公众号 channel — but it has NO 公众号 finished-cover template (all 13 prompts hard-code 3:4 小红书) and, more decisively, NO LICENSE at all (all-rights-reserved), so you have no legal right to embed or redistribute it; the cover image also comes from an external image model whose quality this eval never verified.

## Why This Score

The user-visible outcome — a topic/title turned into a finished-cover image prompt on an explicit hook formula — is real at the prompt layer: SKILL.md loads, all 6 references resolve, the formulas carry HEX/anchor/contrast/thumbnail specifics, 13 finished-cover prompts + two lifestyle style packs ship, and 16 example PNGs prove the pipeline produces covers. But the thing the user actually keeps — the rendered cover — is made by an external image model (ChatGPT Image 2 / DALL-E) this eval had no credentials to run, so core quality is unverified; and the repo is unlicensed and 小红书-only.

### Top 3 score drivers

- +12 : static structure — 2/2 support-critical claims passed (frontmatter + references resolve) plus 4 high support claims (coverage, concrete formulas, prompt library, anti-slop declared); net of the −4 for the 公众号-fit gap and −2 for the untested core promise.
- +5 / 0 / 0 : maintainer +5 (pushed within 90d) is the only maintainer point — no releases/CI (release_pipeline 0), no tests/eval harness (eval_discipline 0); ecosystem +0 (134★ < 1000 band); layer_bonus +0 (molecule, not atom).
- −2 : NO LICENSE penalty (small-repo band). The real cost of no-license is the adoption FLAG, not these 2 points; and the core promise stays untested (image-model-dependent) so no atom bonus and evidence capped at partial.

### Core outcome
Observably works (static): SKILL→references integrity, quantified template formulas, a runnable cover-diagnosis rubric, a 13-prompt finished-cover library, and a shipped example gallery.
Observably NOT verified: the rendered cover's quality / on-brand-ness / hook strength / Chinese-text fidelity (image-model-dependent, not run — no credentials); cross-model portability; trigger precision; and finished 公众号 covers, which the default workflow does not produce at all.

### Scenario breadth
Zero live renders in this eval. Static breadth is good — 4 templates × HEX palettes, 2 lifestyle style packs, 16 example covers across all 4 base templates — but every core-quality dimension (platform, subject, model) is unexercised → evidence_completeness = partial.

### Repeatability
File-level reproducible: the prompt library and formulas are fixed text, so the same brief yields the same *prompt*. The rendered *image* is not reproducible here — image models vary run-to-run, and this eval never ran one, so image-level repeatability is unmeasured.

### Failure transparency
No runtime/error surface to speak of (it emits text prompts). The honest failure mode is silent: an off-brand or garbled-Chinese cover only shows up when a human looks at the render — the skill has no self-check that the image met its own Quality Bar.

## What Would Move The Score Up

1. Obtain a license from the author (issue/email). This is the adoption gate, not a scoring line — until it exists, Park cannot legally embed or redistribute it regardless of score. (unblocks adoption; ~+2 direct)
2. Render 2+ live covers through ChatGPT Image 2 and score them against the SKILL.md Quality Bar (80px thumbnail, one anchor, crisp correct Chinese) → lifts core_layer_tested and evidence partial→portable (~+layer/evidence, moves toward reusable).
3. Add a real finished 公众号 3:1 + 1:1 template to finished-cover-prompts.md (or scope ponyo to 小红书-only and route 公众号 to guizang-social-card) → clears the failed_partial platform-fit claim (~+4).

## Remaining Risks

Ranked. Each risk with severity + impact + mitigation if known.

| Risk | Severity | Impact | Mitigation |
|---|---|---|---|
| NO LICENSE (all-rights-reserved) | Critical | No legal right to use/modify/redistribute in Park's pipeline; fork/embed exposes Park. | Get explicit license from author before any pipeline use; until then treat as read-only reference. |
| 小红书-only, not 公众号 | High | Park's channel is 公众号; default workflow emits zero 公众号 finished covers (all 13 prompts 3:4). | Use guizang-social-card as 公众号 primary; scope ponyo to 小红书 lane, or author a 公众号 template. |
| Image-model dependency (core unverified) | High | Cover quality / on-brand / Chinese fidelity depend on ChatGPT Image 2; not run here; garbled Chinese is a known image-model weakness. | Live-render + score vs Quality Bar; pin model + settings; human review each render. |
| Bus-factor 1 / very young | Medium | Created 2026-06-21, one push 2026-06-22, single committer, no releases/CI/tests — longevity untested. | Watch maintenance 2–4 weeks; vendor the folder so Park isn't exposed to upstream churn. |
| No trigger eval / anti-slop only declared | Low | Trigger precision unmeasured; anti-slop rules stated but not verified on real output. | Add eval-cases with negative examples; check watermark/anti-slop on live renders. |

## Related Artifacts

- Claim map: ../claims/claim-map.yaml
- Plan: ../plans/2026-07-09-eval-plan.md
- Runs: ../runs/ (no live run — core is image-model-dependent, no credentials)
- Verdict calculator input: ./2026-07-09-verdict-input.yaml
- Rendered HTML dossier: ./2026-07-09-verdict.html

## Verdict

Conditional. As a 小红书 cover-prompt reference it is genuinely useful and well-built, and belongs to Vera in the 封面 lane — but as a BACKUP, not the primary. For Park's 公众号 pipeline the primary is guizang-social-card (公众号 21:9+1:1 pairs, deterministic HTML→PNG, AGPL-3.0, 4809★). Do NOT embed ponyo in Park's pipeline until the author grants a license; until then, use it only as a read-only 小红书 idea/formula reference. Next minimal action: open a license request, then live-render 2 covers against the Quality Bar to lift core evidence.
