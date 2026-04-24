# repo-evals Roadmap — v0.2 → v0.3

Derived from:

- Anthropic skill-authoring best practices (platform.claude.com/docs + 30-page PDF guide + skill-creator source)
- Wendy's review on 2026-04-24 (trigger testing, HTML output, skill simplification)
- Dogfooding eval of `iamzhihuix/skills-manage` that exposed manual-filling friction

## Goals

1. Move from "structured human filling" → "executable evaluation harness"
2. Separate two distinct kinds of correctness: *does Claude trigger the skill* vs *does the skill do the right thing when triggered*
3. Make verdict output glance-readable (HTML single file) instead of YAML/MD-only

## Non-goals

- Cross-model testing (Haiku/Sonnet/Opus) — adds friction, minimal signal for our use case
- Cloud service, multi-tenant deployment — stays local-first
- Replacing `claim-map.yaml` / `run-summary.yaml` as the source of truth — those stay canonical

## Phase order

| Phase | Scope | Status | API-dependent |
|---|---|---|---|
| **1** | Eval-as-harness (A) | planned | no |
| **4** | Skill self-simplification (D) | planned | no |
| **5** | Small optimizations (E + F + H) | planned | no |
| **2** | Trigger discovery testing (B) | planned | yes (CLIProxyAPI) |
| **3** | HTML verdict renderer (C + G) | planned | no |

Phases 1 / 4 / 5 first — no external dependency, easy to commit.
Phases 2 / 3 after — need iteration and cost a bit of API / design time.

---

## Phase 1 — Eval-as-harness

Move from "human writes claim status in run-summary" to "eval script writes status automatically".

**Deliverables**

- `scripts/new-eval-harness.sh <repo-slug>` — scaffolds `repos/<slug>/evals/evals.json`
- `scripts/run_evals.py <repo-slug>` — loads `evals.json`, runs each eval, writes `results_by_claim` into the matching `run-summary.yaml`
- `scripts/run_evals.py --baseline` — runs the same prompts against Claude *without* the target repo, producing with/without diff
- New canonical fields on `run-summary.yaml`:
  - `metrics.pass_rate: float`
  - `metrics.elapsed_time_sec: float`
  - `metrics.token_usage: {input: int, output: int, cache_read: int}`
- Update `docs/FRAMEWORK.md` with the "eval drives claim status, not vice versa" principle

**Anchor**: skill-creator's `evals/evals.json` schema ships with:

```json
{"skill_name": "...", "evals": [{"id": 1, "prompt": "...", "expected_output": "...", "files": []}]}
```

We extend with `claim_id` so passing/failing an eval directly updates a claim's status.

---

## Phase 4 — Skill self-simplification

`~/.claude/skills/eval-repo/SKILL.md` as it stands is ~140 lines. Most of that is "how the framework works" — which belongs in the framework repo, not the skill.

**Deliverables**

- Trim skill body to < 50 lines
- Core 3 triggers:
  - "帮我 eval 一下这个 repo / 项目 / skill"
  - "evaluate this repo"
  - "试用一下这个项目"
- "Pushy" description per Anthropic skill-creator guidance (combat under-triggering)
- Delete cross-model testing language
- Point all detail to framework repo, not inline

---

## Phase 5 — Small optimizations

**5.1 `archetypes/mcp-enhancement/`** — new archetype for skills that wrap an MCP server with workflow guidance (e.g. `sentry-code-review`). PDF page 8 identifies this as one of three canonical skill categories; we currently have no home for it.

**5.2 Outcome-focused templates** — rewrite `templates/eval-readme.md` lead with outcomes, not feature lists. PDF page 20 gives the good/bad pattern.

**5.3 Skip_reason strictness** — `coverage_gap_detector.py` treats `status: untested` without `skip_reason` as a critical gap, and recognizes a populated `skip_reason` as a legitimate skip (still caps verdict per archetype rules).

---

## Phase 2 — Trigger discovery testing

Two-part correctness:

- **Precision**: does the skill NOT trigger on unrelated queries?
- **Recall**: does the skill trigger when it should?

**Deliverables**

- `scripts/trigger_test.py <skill-path>` — reads `SKILL.md` description, generates 10 should-trigger + 10 should-not-trigger user phrases (template + small LLM assist via CLIProxyAPI), then for each phrase calls Claude with the skill loaded and checks whether the skill was invoked
- Output: confusion matrix (TP/FP/FN/TN), precision, recall
- `verdict_calculator.py` adds ceiling: precision < 0.7 OR recall < 0.7 → cap at `usable`
- New fixture type: `fixtures/trigger-phrases/<domain>.yaml` — shareable should/should-not phrase banks
- Uses CLIProxyAPI at `http://localhost:8317/v1/messages` with `claude-haiku-4-5-20251001` for cost efficiency

---

## Phase 3 — HTML verdict renderer

Replace "open YAML + MD in editor" with "open one HTML file in browser".

**Deliverables**

- `scripts/render_verdict_html.py <repo-slug>` — generates `repos/<slug>/verdicts/<date>-verdict.html`
- Style anchor: `nicobailon/visual-explainer` (single file, no build step, CDN deps only)
- Content:
  - Hero banner: emoji bucket + repo URL + date
  - Mermaid flowchart: archetype → ceilings → final bucket derivation
  - Claim table: id / priority / status / evidence link
  - Confusion matrix for trigger test (if Phase 2 data present)
  - 3-metric bar chart (Chart.js CDN): pass_rate / elapsed_time / tokens
  - Evidence grid: links to logs + artifacts per run
  - Dark/light theme toggle
- Optionally call automatically at end of `scripts/verdict_calculator.py --md`

---

## Out of scope for now

- Dashboard integration of HTML renderer (Phase 4 of original platform tools) — keep separate
- Uploading artifacts to a public URL — out of scope (local-first)
- Automatic re-eval on schedule — can be bolted on later via `schedule` skill
