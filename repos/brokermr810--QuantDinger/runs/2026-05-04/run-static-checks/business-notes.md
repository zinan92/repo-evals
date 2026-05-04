# QuantDinger — static-checks run, 2026-05-04

Eval scope: docker-compose stack, base image, LLM providers, broker
integrations, MCP server, port-bind defaults, live-trading safety
pin. No live install, no AI-agent session.

## Findings

### claim-001: 4-service compose stack — **passed**

| Service | Image | Ports |
|---|---|---|
| postgres | postgres:16-alpine | 127.0.0.1:5432 (default) |
| redis | redis:7-alpine | 127.0.0.1:6379 (default) |
| backend | local build (./backend_api_python) | 127.0.0.1:5000 (default) |
| frontend | local build | :8888 → 80 (public, by design) |

All 4 containers prefixed `quantdinger-*`, all have healthchecks.
README's "Try in 2 minutes" command correctly references this stack.

### claim-002: image / Python version consistency — **passed**

`backend_api_python/Dockerfile` declares
`ARG BASE_IMAGE=python:3.12-slim-bookworm`. `docker-compose.yml`
backend service declares the same default. README badge says "Python
3.10+ | Docker image 3.12" — runtime image is 3.12, source minimum
is 3.10+ (broader compat for non-Docker installs).

### claim-003: multi-LLM — **passed**

`backend_api_python/env.example` declares 3 LLM providers, each with
its own `*_API_KEY`, `*_MODEL`, and `*_BASE_URL`:

```
OPENAI_API_KEY=…    OPENAI_MODEL=gpt-4o      OPENAI_BASE_URL=https://api.openai.com/v1
DEEPSEEK_API_KEY=…  DEEPSEEK_MODEL=deepseek-chat   DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
GROK_API_KEY=…      GROK_MODEL=grok-beta     GROK_BASE_URL=https://api.x.ai/v1
```

`*_BASE_URL` overrides mean users can route through their own gateway
or a CN-friendly proxy. README's claim of "your own keys" is enforced
by the env layout.

### claim-004: multi-broker integration — **passed**

`backend_api_python/requirements.txt` declares:

- `ccxt>=4.0.0` (crypto exchanges)
- `ib_insync>=0.9.86` (Interactive Brokers, optional comment in file)
- `finnhub-python>=2.4.18` + `yfinance>=0.2.18` + `akshare>=1.12.0`
  (data sources)
- `MetaTrader5` is referenced in a comment but not in requirements
  proper — the comment explicitly notes Windows-only ("Note:
  MetaTrader5 is Windows-only and not available on Linux/macOS").
  This means a Linux Docker host genuinely cannot do forex; the
  README mentioning forex without that footnote on every promo page
  is a small DX trap (covered in `watch_out`).

### claim-005: MCP server — **passed**

`mcp_server/pyproject.toml` declares:

```
name = "quantdinger-mcp"
version = "0.1.0"
description = "Model Context Protocol (MCP) server for the QuantDinger
  Agent Gateway — exposes market data, strategies, backtests and paper
  trading to AI agents (Cursor, Claude Code, Codex, OpenClaw, NanoBot, ...)."
requires-python = ">=3.10"
mcp>=1.2.0
console_scripts: quantdinger-mcp = quantdinger_mcp.server:main
```

This is a real, separately-versioned MCP server, not a stub. The
description explicitly enumerates 5 supported agent runtimes.

### claim-006: default port binding — **passed**

3 of 4 services bind to 127.0.0.1 by default — postgres/redis/backend
are not externally exposed unless the user changes the env var. Only
frontend exposes :8888 to the host (intentional, you need to load the
UI in a browser). A user running `docker-compose up -d` on a public
VPS still gets exposed (the frontend is public, and from the
frontend you can talk to the backend), but they're not auto-leaking
postgres or redis credentials.

### claim-008: live-trading is opt-in — **passed**

`env.example` defaults `AGENT_LIVE_TRADING_ENABLED=false`. The same
file documents that `paper_only` is "force-pinned to true and any
attempt to" override it is rejected (text continues out of the
captured slice — worth a deeper look in a live eval). The default
posture is paper-trading-first; users have to flip a flag to fire
real orders.

This is the right safety story for a platform that lets an LLM write
strategies. Worth confirming in the live eval that the flag actually
gates the order submission path, not just the UI.

## What is still untested

- **claim-007 (MCP-agent e2e)** — install, configure an LLM key,
  connect Cursor or Claude Code via MCP, ask the agent to run a
  backtest, capture: token usage, returned structured artefact,
  whether the agent actually used the MCP tool list rather than
  hallucinating. Run a happy-path + a failure case (bad ticker,
  revoked key).

- **claim-008 (live-order safety in practice)** — flip
  `AGENT_LIVE_TRADING_ENABLED=true` in a paper-broker environment
  (e.g., IBKR paper account) and verify there's still a manual
  approval step before order submission. If a user can flip one env
  var and have the LLM auto-submit live orders, the safety story
  collapses.

## Verdict implication

Static layer is clean. Compound rule caps `usable` until a logged
agent-driven scenario shows the platform delivers value end-to-end.
The most important deferred check is claim-008 — a platform that lets
an LLM trade real money needs more than a default-off flag, it needs
audit trails + manual confirmation.

Recommended bucket: **usable** — strong foundation, real safety
pin in defaults, but the compound experience is unverified.
