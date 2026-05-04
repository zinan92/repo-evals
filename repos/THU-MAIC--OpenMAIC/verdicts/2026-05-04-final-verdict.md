# OpenMAIC — final verdict (2026-05-04)

## Repo

- **Name:** THU-MAIC/OpenMAIC
- **Branch evaluated:** main@HEAD (v0.2.1, JCST'26 paper)
- **Archetype:** orchestrator
- **Layer:** **compound** — LangGraph multi-agent classroom
  generation
- **Eval framework:** repo-evals layer model v1 (f9ed1e9)

## Bucket

**`usable`** — strong static layer with rare positive signals
(in-repo eval harness, well-disclosed multi-provider env, clean
OpenClaw integration). Compound rule caps `usable` until at least one
logged live classroom generation.

## What was evaluated

### Atom + molecule level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 tech stack | passed | next 16.1.2 / react 19.2.3 / langgraph ^1.1.1 / tailwind ^4 — matches README badges |
| 002 5 LLM providers | passed | OpenAI/Anthropic/Google/DeepSeek/Grok all with KEY+BASE_URL+MODELS |
| 003 5 TTS providers | passed | OpenAI/Azure/GLM/Qwen/MiniMax all with KEY+BASE_URL; MiniMax has default endpoint |
| 004 eval harness | passed | 2 named eval scripts (eval:whiteboard + eval:outline-language) reference real tsx runners |
| 005 OpenClaw skill | passed | skills/openmaic/SKILL.md (102 lines) with user-invocable, confirmation-heavy SOP |

### Compound level (deferred)

| Claim | Status | Required |
|---|---|---|
| 006 live classroom generation | untested | open.maic.chat or self-hosted; verify slides + quiz + sim + whiteboard + TTS |
| 007 cost transparency | untested | README to add per-classroom token + TTS cost estimate |

## Real findings worth surfacing

1. **In-repo eval harness is rare and disciplined.** Most "AI demo"
   repos don't ship `eval/`. OpenMAIC has two named evals
   (whiteboard-layout, outline-language) with their own runners and
   a `shared/` for common code. That's a strong testing-intent
   signal.

2. **OpenClaw SOP is safety-conscious.** The skill explicitly says
   "Run one phase at a time and ask for confirmation before each
   state-changing step". This is the right posture for a multi-step
   AI orchestrator that might write files / clone repos / start
   services on the user's machine.

3. **TTS surface is unusually broad.** 5 commercial providers + a
   self-hosted VoxCPM2 (added in v0.2.1) means the classroom doesn't
   degrade silently if one provider has issues — the operator can
   fail over.

4. **Active development cadence.** 4 minor releases in the 6 weeks
   leading up to eval (v0.1.0 through v0.2.1). Healthy for an
   academic-affiliated open-source project.

## Why not higher

`usable` because:

- No live classroom generation logged on this evaluator's machine.
  Compound layer's user value is the multi-agent dance — static
  evidence cannot validate that the agents actually teach
  meaningfully.
- Cost transparency is genuinely missing; non-technical users would
  benefit from a "a 30-min classroom on a typical topic costs roughly
  $X with default config" line.

## Path to `reusable`

1. Run a live classroom on open.maic.chat with a real LLM key.
2. Self-host a fork; verify Vercel one-click deploy works.
3. Try one PDF-upload classroom; verify the OpenClaw skill SOP
   end-to-end.
4. Trigger an LLM-provider failure (revoked key) and verify the
   classroom degrades gracefully.
5. Update claim-006 → `passed`. If the README later adds a cost
   estimate, claim-007 → `passed`. Re-run verdict_calculator.

## Recommended

```yaml
current_bucket: usable
status: evaluated
```
