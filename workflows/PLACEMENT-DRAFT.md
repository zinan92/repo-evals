# Workflow placement draft — for Wendy's review

This is the **review-first draft**. No repo.yaml has been touched yet.
Goal: agree on which repo lands at which stage, then code the schema +
renderer.

For each evaluated repo I picked one (occasionally two) workflow placements.
Three columns: workflow / stage / role. `role` follows Codex's vocabulary:

- **primary** — the thing you'd actually reach for at this stage
- **support** — handles a sub-task within this stage
- **alternative** — a viable substitute if the primary doesn't fit
- **reference** — useful to look at, not actually used

Empty stages = roadmap signals (what's the next thing you should
find / build).

---

## park-content-v1 (8-step content pipeline)

| Stage | Repo | Score | Role | Note |
|---|---|---|---|---|
| 01 信号发现 | *(none yet)* | — | — | **GAP — no content-signal-scanner in corpus.** Adjacent: ai-goofish-monitor (marketplace not content) |
| 02 内容获取 | NanmiCoder/MediaCrawler | 75 | primary | 7 CN platforms, mature |
| 02 内容获取 | zinan92/content-downloader | 29 | alternative | broken on Douyin signing |
| 02 内容获取 | Usagi-org/ai-goofish-monitor | 69 | reference | XianYu monitor — content-adjacent only |
| 03 内容理解 | zinan92/content-extractor | — | primary | per memory, in-build |
| 03 内容理解 | zarazhangrui/youtube-to-ebook | — | support | video → text understanding |
| 04 选题决策 | *(none yet)* | — | — | **GAP — no content-curator in corpus.** This is the human-judgment stage |
| 05 内容生产 | op7418/Humanizer-zh | 75 | primary | rewrite to remove AI 味 |
| 05 内容生产 | zinan92/content-toolkit | — | support | content-rewriter logic |
| 05 内容生产 | oaker-io/wewrite | — | alternative | broader WeChat content workflow |
| 06 成品组装 | zarazhangrui/frontend-slides | 62 | primary | HTML deck assembly |
| 06 成品组装 | remotion-dev/skills | 72 | primary | programmatic video assembly (different medium) |
| 06 成品组装 | zarazhangrui/personalized-podcast | — | primary | podcast-medium |
| 06 成品组装 | zarazhangrui/codebase-to-course | — | primary | course-medium |
| 06 成品组装 | THU-MAIC/OpenMAIC | 75 | primary | interactive classroom medium |
| 07 分发 | dreammis/social-auto-upload | 42 | primary | 7-platform multi-publish (despite ⚠️ Risky) |
| 07 分发 | geekjourneyx/md2wechat-skill | 91 | primary | WeChat-specific channel adapter |
| 07 分发 | autoclaw-cc/xiaohongshu-skills | — | support | single-platform helper |
| 08 反馈学习 | *(none yet)* | — | — | **GAP — no performance-tracker in corpus.** This is the loop-closer |

**Content pipeline coverage:** 4/8 stages have a primary. Stages 01 / 04 / 08 are gaps.

---

## park-trading-v1 (8-step trading pipeline)

Note: most of Wendy's trading repos (kline / signal / copilot / backtest /
risk / executor / journal) are scaffolds-in-progress per memory and not
all have full evals yet. Only currently-evaluated repos shown.

| Stage | Repo | Score | Role | Note |
|---|---|---|---|---|
| 01 行情数据 | *(none in current corpus)* | — | — | zinan92/kline exists per memory; not yet evaluated |
| 02 情报采集 | zinan92/intel | — | primary | per memory, was qualitative-data-pipeline |
| 02 情报采集 | RKiding/Awesome-finance-skills | — | support | finance methodology skills |
| 03 信号合成 | *(none yet)* | — | — | scaffold in zinan92/signal |
| 04 方法论路由 | tukuaiai/tradecat | — | primary | trading platform |
| 04 方法论路由 | RKiding/Awesome-finance-skills | — | support | strategy methodology |
| 05 回测验证 | brokermr810/QuantDinger | 76 | primary | full quant stack with backtest engine |
| 06 风控决策 | brokermr810/QuantDinger | 76 | primary | also covers risk gating |
| 07 执行引擎 | brokermr810/QuantDinger | 76 | primary | IBKR / MT5 / crypto execution |
| 07 执行引擎 | tukuaiai/tradecat | — | alternative | smaller-scope alternative |
| 08 复盘学习 | *(none yet)* | — | — | scaffold in zinan92/journal |

**Trading coverage:** QuantDinger occupies 3 stages alone (5/6/7 — that's the breadth-vs-depth question — is this an acceptable single-vendor span or a sign that we should evaluate more options).

---

## park-development-v1 (5-phase dev workflow)

| Stage | Repo | Score | Role | Note |
|---|---|---|---|---|
| 01 research | karpathy/autoresearch | — | reference | LLM training research, not general code research |
| 01 research | zinan92/repo-evals | 78 | primary | "decide what to install" research tool |
| 02 plan/design | zarazhangrui/frontend-slides | 62 | support | UI / pitch-deck design |
| 02 plan/design | HughYau/qiushi-skill | 73 | primary | reasoning-discipline skills (investigation-first / contradiction-analysis) |
| 02 plan/design | zinan92/doc-driven-dev-workflow | 59 | primary | the workflow itself, especially design phase |
| 03 code/review | obra/superpowers | 77 | primary | TDD / brainstorming / subagent-driven-dev / verification |
| 03 code/review | zinan92/doc-driven-dev-workflow | 59 | support | dev-phase enforcement |
| 03 code/review | gooseworks-ai/goose-skills | — | alternative | Goose-runtime equivalent |
| 04 package | anthropics/skill-creator | 81 | primary | skill-authoring meta-tool — what you reach for when packaging a skill |
| 04 package | iamzhihuix/skills-manage | 77 | primary | distribute the packaged skill across 28 tools |
| 04 package | router-for-me/CLIProxyAPI | 78 | support | deployment plumbing for AI tools |
| 05 maintain | router-for-me/CLIProxyAPI | 78 | support | runtime layer for AI tools post-deploy |
| 05 maintain | *(none beyond)* | — | — | observability / monitoring gap |

**Dev coverage:** 03 (code/review) and 04 (package) are well-covered. Research and maintain stages have gaps.

---

## Repos that don't fit any of the 3 workflows

These earn `workflow_placements: []`:

| Repo | Why no placement |
|---|---|
| Jamailar/RedBox | TBD — not yet read for this draft |
| nicobailon/visual-explainer | educational / explanation tool, not in any of the 3 |
| zarazhangrui/follow-builders | builder-network tool |
| zarazhangrui/tab-out | productivity skill |

---

## Open questions before we code this

1. **OpenMAIC + frontend-slides + codebase-to-course + youtube-to-ebook + personalized-podcast all end up at "06 成品组装"**. That's 5 repos at one stage. Either (a) the stage should split into 06a deck / 06b video / 06c podcast / 06d course, or (b) we keep it unified and surface 5 medium-cards under one stage. Your call.

2. **QuantDinger covers 05 + 06 + 07 of trading alone**. Multi-stage placement should be allowed (one repo, multiple `placements:`) — confirmed in schema. But should we explicitly mark "primary at 05, primary at 06, primary at 07" or use a "spans-stages" annotation?

3. **Empty stages** — once the schema lands, should the dossier auto-show "0 evaluated repos at this stage" so the gap is visible? Yes, I think so.

4. **GAP repos vs scaffolding repos**: zinan92/kline / signal / copilot / backtest / risk / executor / journal exist locally but aren't evaluated yet (per memory: scaffolding state). Should we list them as "pending evaluation" placeholders in the workflow YAML so the visualization shows them anyway? Or only show evaluated repos?

5. **Visual decision deferred**: still need to pick (a) linear SVG, (b) vertical timeline, or (c) grid view for the rendering. My recommendation stands: (a) for dossier (small, focused), (c) for dashboard (overview).

6. **`reason` field per placement**: every placement should have one short en/zh reason. Not in this draft (didn't want to write 33 of them prematurely). We'll write them as we encode the placement into each repo.yaml.
