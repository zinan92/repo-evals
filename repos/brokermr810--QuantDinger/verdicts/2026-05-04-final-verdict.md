# QuantDinger — final verdict (2026-05-04)

## Repo

- **Name:** brokermr810/QuantDinger
- **Branch evaluated:** main@HEAD (3.0.3)
- **Archetype:** orchestrator
- **Layer:** **compound** — multi-agent AI research, LLM-driven
  strategy and indicator generation, ensemble + reflection
- **Eval framework:** repo-evals layer model v1 (4acbd5d)

## Bucket

**`usable`** — strong static layer. Compound rule caps `usable`
until at least one logged agent-driven scenario, and a platform that
lets an LLM trade real money needs a verified manual-approval gate
before any higher bucket can be claimed.

## What was evaluated

### Atom + molecule level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 4-service compose | passed | postgres + redis + backend + frontend, all healthchecked |
| 002 base-image consistency | passed | python:3.12-slim-bookworm in both Dockerfile and compose |
| 003 multi-LLM | passed | OpenAI / DeepSeek / Grok all with `*_BASE_URL` overrides |
| 004 multi-broker | passed | ccxt + ib_insync + finnhub + yfinance + akshare in requirements; MetaTrader5 conditional + Windows-only note |
| 005 MCP server | passed | quantdinger-mcp 0.1.0 with `mcp>=1.2.0`; supports 5 named agent runtimes |
| 006 default port binding | passed | postgres/redis/backend bind 127.0.0.1; frontend public-by-design |
| 008 live-trading off by default | passed | `AGENT_LIVE_TRADING_ENABLED=false`; env.example references paper-only force-pin |

### Compound level (deferred)

| Claim | Status | Required |
|---|---|---|
| 007 MCP-agent e2e | untested | install + LLM key + Cursor/Claude Code session running a real backtest end-to-end via MCP |
| 008 live-order gating in practice | untested | flip flag in paper-broker test, verify manual approval is enforced (not just UI) |

## Real findings worth surfacing

1. **The default safety posture is real.** `AGENT_LIVE_TRADING_ENABLED=false`
   + `paper_only` force-pinned + localhost-only bindings on
   sensitive services together mean the default deploy doesn't
   auto-fire live orders or auto-leak postgres/redis. That's the
   right baseline for a platform where an LLM writes trading code.

2. **MetaTrader5 is structurally Linux-incompatible.** The Python
   package only ships Windows wheels. README mentions "MT5 forex"
   alongside crypto and stocks as a peer; the requirements file is
   honest (Windows-only comment), but a casual reader of the README
   could miss that and pick a Linux server expecting forex to work.
   This belongs in `watch_out`.

3. **OSS / SaaS / Marketplace overlap.** README links to
   ai.quantdinger.com (SaaS), AWS Marketplace AMI, and a billing
   primitive in the OSS repo. A user evaluating "is this open
   source?" should read which features are gated and which are
   genuinely free to self-host.

4. **MCP integration is a separately-versioned package.** Not a
   stub or marketing phrase — `mcp_server/` has its own pyproject,
   its own version (0.1.0), its own console_scripts entry. Easier
   to audit than a "we mention MCP somewhere" claim.

## Why not higher

`usable` is the right ceiling because:

- No live agent-driven scenario logged. Compound layer is exactly
  the case where static evidence cannot translate to user-facing
  trust without a real session.
- The most consequential claim — that an LLM cannot auto-fire live
  orders — is verifiable only with a live test, and is too
  important to assume from one default-off env var.

## Path to `reusable`

1. Bring up the stack on a fresh host with `docker-compose up -d`.
2. Wire MCP into Claude Code (or Cursor) per README Step 2.
3. Ask the agent to run one backtest and capture: tool calls
   actually used, structured artefact returned, token usage.
4. With paper account: enable live trading, attempt to submit an
   order through the agent, confirm a manual-approval step
   intercedes.
5. Log under `runs/<date>/run-{compound-happy,compound-safety}/`.
6. Update claim-007 + claim-008 to `passed` if both work as
   advertised; re-run verdict_calculator.

## Recommended

```yaml
current_bucket: usable
status: evaluated
```
