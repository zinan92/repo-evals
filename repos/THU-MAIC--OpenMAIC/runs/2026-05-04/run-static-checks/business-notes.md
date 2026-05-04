# OpenMAIC — static-checks run, 2026-05-04

Eval scope: tech stack, multi-LLM + multi-TTS env surface, eval
harness, OpenClaw skill. No live classroom run.

## Findings

### claim-001: tech stack — **passed**

| Lib | Version |
|---|---|
| next | 16.1.2 |
| react | 19.2.3 |
| @langchain/langgraph | ^1.1.1 |
| tailwindcss | ^4 |

Matches README's "Next.js 16 / React 19 / TypeScript 5 / LangGraph 1.1
/ Tailwind 4" badges exactly.

### claim-002: 5 LLM providers — **passed**

Each of OPENAI / ANTHROPIC / GOOGLE / DEEPSEEK / GROK has 3 env vars:
`*_API_KEY`, `*_BASE_URL`, `*_MODELS`. README headlines "All providers
are optional" — that's enforced by the env layout.

### claim-003: 5 TTS providers — **passed**

Each of TTS_OPENAI / TTS_AZURE / TTS_GLM / TTS_QWEN / TTS_MINIMAX has
2 env vars (`*_API_KEY`, `*_BASE_URL`). MiniMax has a default
`BASE_URL=https://api.minimaxi.com`. Combined with the recently-added
self-hosted VoxCPM2 (per the v0.2.1 changelog), the TTS surface is
unusually well-covered for an OSS classroom platform.

### claim-004: in-repo eval harness — **passed**

`package.json` declares two named eval scripts:

```
"eval:whiteboard":        tsx eval/whiteboard-layout/runner.ts
"eval:outline-language":  tsx eval/outline-language/runner.ts
```

`eval/` directory contains `outline-language/`, `whiteboard-layout/`,
and a `shared/` for common code. This is unusually disciplined — most
"interactive AI" repos don't ship eval harnesses at all.

### claim-005: OpenClaw skill — **passed**

`skills/openmaic/SKILL.md` exists (102 lines, HTTP 200) with:

```yaml
---
name: openmaic
description: Guided SOP for setting up and using OpenMAIC from OpenClaw…
user-invocable: true
metadata: { "openclaw": { "emoji": "🏫" } }
---
```

The body is a step-by-step SOP that explicitly says "Run one phase at
a time and ask for confirmation before each state-changing step" —
that's the right safety posture for a multi-platform AI orchestrator.

## What is still untested

- **claim-006 (live classroom)** — open.maic.chat with a real LLM key,
  ask for "quantum physics", verify the multi-agent classroom
  actually generates slides + quiz + simulation + whiteboard + TTS.
- **claim-007 (cost transparency)** — README does not currently
  estimate per-classroom token / TTS cost; for a non-technical user
  this is a real gap.

## Verdict implication

Static layer is unusually clean for a Next.js platform of this
complexity (81 deps + multi-agent orchestration). The eval/ harness
is a major positive signal — disciplined testing intent. Per the
compound rule, ceiling is `usable` until at least one logged classroom
generation scenario.

Recommended bucket: **usable**.
