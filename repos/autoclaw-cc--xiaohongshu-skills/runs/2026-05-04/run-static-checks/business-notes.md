# xiaohongshu-skills — static-checks run, 2026-05-04

Eval scope: 5 sub-skills, root SKILL.md routing, Chrome extension
permissions, Python deps, OpenClaw / Claude Code contract.

## Findings

### claim-001: 5 sub-skills present — **passed**

All 5 SKILL.md files return HTTP 200 from raw.githubusercontent.com:

```
skills/xhs-auth/SKILL.md          → 200
skills/xhs-publish/SKILL.md       → 200
skills/xhs-explore/SKILL.md       → 200
skills/xhs-interact/SKILL.md      → 200
skills/xhs-content-ops/SKILL.md   → 200
```

README's "功能概览" table is structurally complete — every row has
its file.

### claim-002: root SKILL.md routing — **passed**

Root SKILL.md mentions the 5 sub-skill names 11 times across its
body. It explicitly takes on the "intent → sub-skill" router role
("根据用户意图路由到对应的子技能完成任务"). The routing layer is
real, not a placeholder.

### claim-003: extension permissions — **passed_with_concerns**

```json
"permissions": ["tabs", "cookies", "scripting", "alarms", "debugger"]
"host_permissions": [
  "https://www.xiaohongshu.com/*",
  "https://xiaohongshu.com/*",
  "https://creator.xiaohongshu.com/*",
  "ws://localhost/*"
]
```

Two flags worth disclosing:

- **`debugger` permission** lets the extension attach to any tab and
  inspect/manipulate via the Chrome DevTools protocol. Powerful enough
  to bypass automation detection by some sites; also powerful enough
  to read the user's data on those sites.
- **`cookies` permission** scoped through host_permissions to XHS
  domains, which is appropriate, but combined with `debugger` the
  effective surface is large.

README does say "use real user account" — the privileged Chrome
surface is by design. This is `passed_with_concerns` because the
README doesn't explicitly enumerate the extension permissions; a
reader has to open `extension/manifest.json` to see them.

### claim-004: minimal Python deps — **passed**

```toml
dependencies = [
    "python-socks>=2.8.1",
    "requests>=2.28.0",
    "websockets>=12.0",
]
[project.optional-dependencies]
dev = ["ruff>=0.9.0", "pytest>=8.0"]
requires-python = ">=3.11"
```

Minimal browser-bridge dep stack (websocket + http + proxy support).
No surprise heavy frameworks. README's "uv sync" path is honest.

### claim-005: OpenClaw + Claude Code contract — **passed_with_concerns**

Root SKILL.md frontmatter includes:

```yaml
metadata:
  openclaw:
    requires:
      bins: [python3, uv]
    emoji: "📕"
    homepage: https://github.com/xpzouying/xiaohongshu-skills
    os: [darwin, linux]
```

OpenClaw contract is real (requires.bins, os scoping). Two things
worth noting:

- **Homepage points to a different repo** (`xpzouying/xiaohongshu-skills`).
  This repo (`autoclaw-cc/xiaohongshu-skills`) is either a fork or a
  rename, and the metadata wasn't updated. Mostly cosmetic, but
  potentially confusing.
- **Windows not supported** in `os` field — useful disclosure but not
  surfaced in the README install steps.

## What is still untested (claim-006)

Composite workflow: "搜索 X → 收藏 → 总结" in a real Claude Code +
real XHS account scenario:

1. Install skill bundle, install extension on a Chrome with logged-in
   XHS account.
2. Run a composite request through Claude Code.
3. Verify the agent (a) calls xhs-auth check first, (b) routes
   through xhs-explore for search, (c) executes xhs-interact for
   collect, (d) returns a summary using xhs-content-ops.
4. Capture: tool calls trace, final summary, browser state changes
   on the actual account.
5. Run an "expired login" scenario — verify xhs-auth re-triggers
   instead of failing silently.

## Verdict implication

Static layer is structurally sound. The two `passed_with_concerns`
items (extension `debugger` permission disclosure, repo-vs-homepage
mismatch) are docs gaps, not bugs. The compound molecule rule caps
`usable` until a logged composite-workflow run proves the routing
+ side-effect chain actually works on a real XHS account.

Recommended bucket: **usable**.
