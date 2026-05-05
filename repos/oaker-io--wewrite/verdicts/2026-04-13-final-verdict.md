# Final Verdict

## Repo

- Name: oaker-io/wewrite
- Date: 2026-04-13
- Archetype: hybrid-skill
- Final bucket: **usable**
- Confidence: medium

## Why This Bucket

- **Core outcome**: Support layer is impressive — all 6 CLI commands work, converter produces real WeChat HTML, hotspot fetching returns live data, 16 themes + 9 image providers + 5 personas all verified. But the **core LLM workflow (8-step article generation) is untested** — it requires a full Claude Code session with WeChat API credentials.
- **Scenario breadth**: Only tested support layer (deterministic code). Core layer (LLM-driven writing) untested. For a hybrid-skill, this triggers the **hybrid cap**: core layer untested → cannot exceed `usable`.
- **Repeatability**: Converter, hotspots, and CLI commands all work consistently in repeated runs. LLM layer repeatability unknown.
- **Failure transparency**: CLI tools handle missing inputs gracefully. Error messages are actionable.

## Hybrid-Skill Ceiling Applied

Per hybrid-skill archetype rules: the **core user-facing layer (LLM-driven article generation)** was not tested. The support layer (converter, hotspots, themes, personas, image providers) all pass. But without core layer evidence, verdict is **capped at `usable`**.

## Score Summary

| Category | Passed | Failed | Partial | Untested | Total |
|----------|--------|--------|---------|----------|-------|
| Critical (support) | 4 | 0 | 0 | 0 | 4 |
| Critical (core) | 0 | 0 | 0 | 2 | 2 |
| High | 3 | 1 | 0 | 0 | 4 |
| Medium | 3 | 0 | 0 | 0 | 3 |
| **Total** | **10** | **1** | **0** | **2** | **13** |

## What I Would Say In Plain English

**wewrite's support layer is genuinely impressive for a skill repo.** The converter produces real WeChat-compatible HTML (inline CSS, footnoted links, dark mode attributes). Hotspot fetching returns live trends from 3 Chinese platforms. 16 themes, 9 image providers, 5 personas — all verified to exist with correct structure. The eval system (3 structured scenarios) shows maturity.

**But it's a writing skill that I haven't seen write.** The entire 8-step article generation pipeline is LLM-driven and requires WeChat API credentials to test end-to-end. The support layer works, but the core promise — "一句话搞定公众号" — is unverified.

**The one real gap: zero unit tests.** 2,232 lines of Python toolkit code with no pytest tests at all. The eval specs test agent behavior, not code correctness. A converter regression would go undetected.

## Path to `reusable`

1. **Test the core LLM workflow** — run a full agent session, generate an article, score it against the quality contract and humanness_score.py
2. **Add unit tests** — converter.py (548 lines) especially needs test coverage for WeChat HTML edge cases
3. **Verify at least 2 image providers** with real API keys

## Path to `recommendable`

Everything in `reusable` plus:
4. **Multiple article generation runs** showing consistency across personas and frameworks
5. **Anti-slop verification** — generated articles scored against banned phrase list
6. **Publish flow verification** — draft-to-WeChat pipeline tested with real credentials
7. **CI for converter tests** — prevent WeChat HTML regressions

## Remaining Risks

- **Core workflow completely untested** — the entire value prop of the skill is unverified
- **No unit tests** — 2,232 lines of Python with zero pytest coverage
- **Image providers cannot be tested without API keys** — 9 providers verified as code, but none tested for actual image generation
- **WeChat API dependency** — publish flow requires real WeChat Official Account credentials
- **camoufox dependency** — browser-based hotspot fetching may break if source sites change layout
