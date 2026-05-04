# Awesome-finance-skills — static-checks run, 2026-05-04

Eval scope: catalog coverage, per-skill hybrid shape, install paths,
frontmatter contract. No live multi-skill agent session.

## Findings

### claim-001: 8 alphaear-* skills present — **passed**

All 8 README-headlined skills return HTTP 200 on raw SKILL.md fetch:

```
alphaear-news / -stock / -sentiment / -predictor /
-signal-tracker / -logic-visualizer / -reporter / -search
```

### claim-002: hybrid shape — **passed**

Sampled `alphaear-news`:

```
SKILL.md          → 33 lines, frontmatter + body
scripts/          → __init__.py + content_extractor.py +
                    database_manager.py + news_tools.py
references/       → sources.md
tests/            → present
```

Each skill is a real hybrid bundle (LLM prompt + Python helpers +
reference docs + tests), not a markdown-only stub.

### claim-003: catalog ≥ docs — **passed**

`skills/` has 10 directories:

```
8 README-listed alphaear-* skills
+ alphaear-deepear-lite     (free lite version, mentioned in README badge)
+ skill-creator             (utility skill for authoring more skills, 371 lines)
```

Code is richer than docs (extra skills not in the table) — under-promise,
over-deliver pattern. Worth a docs PR upstream.

### claim-004: multi-agent install paths — **passed**

README's "Integration Guide" table covers 3 frameworks with explicit
paths:

| Framework | Workspace path | Global path |
|---|---|---|
| Antigravity | `<workspace>/.agent/skills/<skill>/` | `~/.gemini/antigravity/global_skills/<skill>/` |
| OpenCode | `.opencode/skills/<skill>/` or `.claude/skills/<skill>/` | `~/.config/opencode/skills/<skill>/` |
| OpenClaw | `<workspace>/skills` (highest priority) | `~/.openclaw/skills` |

Concrete enough to cargo-cult; users in each framework can act
without reading source.

### claim-005: SKILL.md frontmatter — **passed**

Sampled alphaear-news:

```yaml
---
name: alphaear-news
description: Fetch hot finance news, unified trends, and prediction
  financial market data. Use when the user needs real-time financial
  news, trend reports from multiple finance sources (Weibo, Zhihu,
  WallstreetCN, etc.), or Polymarket finance market prediction data.
---
```

Standard `name + description` with explicit "Use when..." trigger
phrase. Compatible with auto-discovery in OpenCode / OpenClaw /
Claude Code skill loaders.

## What is still untested (claim-006)

Multi-skill agent session:

1. Install full skill set into a real OpenCode / OpenClaw / Claude
   Code workspace.
2. Ask a multi-skill question ("Analyze how the gold crash affects
   A-shares").
3. Verify the agent correctly chains alphaear-news → alphaear-stock →
   alphaear-logic-visualizer → alphaear-reporter (or a sensible
   subset).
4. Capture: tool call trace, token usage, final artefact (text
   summary + draw.io XML transmission diagram).
5. Run a "data source down" scenario (e.g., Polymarket unreachable)
   and verify the failure surfaces clearly.

## Verdict implication

Strong static layer — every README-listed skill is real and
non-trivial. The catalog is properly structured for multi-agent
distribution. Per the molecule rule, the catalog can't be promoted
past `usable` without at least one logged multi-skill agent session.

Recommended bucket: **usable**.
