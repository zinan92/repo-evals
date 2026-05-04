# xiaohongshu-skills — final verdict (2026-05-04)

## Repo

- **Name:** autoclaw-cc/xiaohongshu-skills
- **Branch evaluated:** main@HEAD (skill v1.0.0)
- **Archetype:** hybrid-skill (LLM + Python bridge + Chrome extension)
- **Layer:** **molecule** — 5 atomic sub-skills wired by root routing layer
- **Eval framework:** repo-evals layer model v1 (4acbd5d)

## Bucket

**`usable`** — strong static layer; molecule rule caps `usable`
until a composite workflow is logged on a real XHS account. Two
disclosure gaps need surfacing (privileged extension permissions and
homepage repo mismatch).

## What was evaluated

### Atom + molecule level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 5 sub-skills | passed | All 5 SKILL.md files present (HTTP 200) |
| 002 root routing | passed | 11 sub-skill mentions in root SKILL.md; explicit "intent → sub-skill" router role |
| 003 extension permissions | passed_with_concerns | `debugger` + `cookies` + `scripting` privileged perms; README doesn't enumerate them |
| 004 minimal Python deps | passed | python-socks + requests + websockets; nothing surprising |
| 005 OpenClaw / Claude Code contract | passed_with_concerns | `metadata.openclaw` block real; but `homepage` field points to a different repo (xpzouying/xiaohongshu-skills) |

### Molecule level (deferred — live)

| Claim | Status | Required |
|---|---|---|
| 006 composite workflow | untested | Real XHS account + Chrome + Claude Code session running "搜索 → 收藏 → 总结" composite |

## Real findings worth surfacing

1. **`debugger` permission is a real privilege escalation.** Combined
   with `cookies` and `scripting`, the extension has full access to
   the user's xiaohongshu.com session including DevTools-level page
   manipulation. Design intent (drive a real account) is honest, but
   the README doesn't list this — anyone evaluating for production
   should open `extension/manifest.json` first.

2. **Homepage field points to a different repo.** Root SKILL.md says
   `metadata.openclaw.homepage: https://github.com/xpzouying/xiaohongshu-skills`
   — not `autoclaw-cc/xiaohongshu-skills`. Likely a fork or rename
   without metadata update. Mostly cosmetic but confusing for skill
   discovery.

3. **Windows not supported by design.** `metadata.openclaw.os` is
   `[darwin, linux]`. README install steps don't mention this; a
   Windows user following the install path would only discover this
   after it failed.

4. **Rate-limit risk acknowledged.** README explicitly warns about
   triggering XHS anti-automation; "use real account" is more humane
   than headless scraping but the platform ToS is the same.

## Why not higher

`usable` because:

- No live composite-workflow run logged on this evaluator's machine.
- Privilege escalation in the extension is real and undisclosed in
  the README — promotion past `usable` should require either the
  README disclosing it or the perms being narrowed.

## Path to `reusable`

1. Disclose extension permissions in README (one-line link to
   `extension/manifest.json` rationale).
2. Update `metadata.openclaw.homepage` to point to this repo, not
   the upstream fork.
3. Run a composite workflow on a real XHS account in Claude Code,
   log under `runs/<date>/run-composite/`.
4. Run an "expired login" scenario; verify `xhs-auth` re-triggers.
5. Update claim-006 to `passed`; re-run verdict_calculator.

## Recommended

```yaml
current_bucket: usable
status: evaluated
```
