# RedBox — final verdict (2026-05-04)

## Repo

- **Name:** Jamailar/RedBox
- **Release evaluated:** v1.11.0 (browser-extension v1.9.7)
- **Archetype:** orchestrator
- **Layer:** **compound** — RedClaw automation console runs LLM-driven
  multi-step tasks; background scheduler keeps long-running work alive
- **Eval framework version:** repo-evals layer model v1 (cee2351)

## Bucket

**`usable`** — capped by the compound-layer ceiling rule.

The static layer is in good shape and the distribution / provider /
extension foundations all check out. But the user-facing value
proposition (creation flow, RedClaw automation, background scheduling,
failure-mode UX) is compound-level and has zero logged scenarios on
this evaluator's machine. Per `docs/LAYERS.md`, compound cannot exceed
`usable` without ≥1 logged scenario, and cannot exceed `reusable`
without ≥3.

## What was evaluated

### Atom + molecule level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 distribution | passed | All 7 assets resolve, sizes 14–24 MB (small for Electron — heavy assets likely deferred per build script) |
| 002 capture coverage | passed_with_concerns | 9/10 platforms covered; **YouTube missing from `host_permissions` despite manifest description listing it** |
| 003 ai providers | passed | Vercel `ai` v6 + Anthropic + OpenAI + openai-compatible + Google; Electron 39.6.0 |

### Compound level (deferred)

| Claim | Status | Required for promotion |
|---|---|---|
| 004 end-to-end creation flow | untested | install + provider key + run a real article through workspace |
| 005 RedClaw single-session autonomy | untested | live RedClaw session with multi-step task |
| 006 background scheduling | untested | scheduled task that survives window close |
| 007 user-friendly failure modes | untested | deliberately broken inputs at three layers |

## Real bugs / mismatches surfaced

1. **YouTube capture promised but unimplemented.** The browser-extension
   manifest's own `description` field lists YouTube alongside the other
   capture sources, but `host_permissions` has no `*.youtube.com`
   entries. A user attempting to capture from YouTube will silently
   fail to inject content scripts. Either add the host permission or
   remove YouTube from the description.

2. **Desktop package version lags release tag (cosmetic).**
   `desktop/package.json` is at `1.9.0` while the release tag is
   `v1.11.0`. Not user-visible during install, but a sign the release
   pipeline is not bumping the package version automatically.

## Why not higher

`usable` is the right ceiling now because:

- The framework's compound rule explicitly caps at `usable` until ≥1
  scenario passes, and at `reusable` until ≥3 — same logic that caps
  hybrid-skill repos with untested LLM layers.
- Even ignoring layers, claim-002 has a real defect (YouTube capture)
  that should not be papered over by averaging.
- Single-evaluator, single-OS, single-day pass — even a clean compound
  scenario would not justify `recommendable` until repeated by other
  operators on other OSes.

## Path to `reusable`

Run the four compound experiments rendered on the dashboard
(`dashboard/repos/Jamailar--RedBox.html`). Each is a system prompt + a
"watch for" list. Log the result in
`repos/Jamailar--RedBox/runs/<date>/run-<scenario>/business-notes.md`
and update the matching claim's `status` in `claims/claim-map.yaml`.
After three pass with full evidence, re-run `verdict_calculator.py`
and the bucket can move to `reusable`.

## Recommended bucket

```yaml
current_bucket: usable
status: evaluated
```
