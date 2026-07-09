# Final Verdict

## Repo

- **Name**: op7418/guizang-social-card-skill
- **Version tested**: main@cf4b810 (2026-07-01 push, package v1.0.0)
- **Date**: 2026-07-09 (initial eval) + same-day follow-up run (live render)
- **Archetype**: hybrid-skill
- **Layer**: molecule
- **Score**: 85 /100  (from `verdict_calculator.py`, not judgement — updated same day after live render)
- **Category**: 🏭 Production-ready / 可用于生产
- **Tier**: 🏭 Team-ready / 团队就绪 (≥80)

## Plain English

- 采用即得 (if adopted): 从一篇文章一句话渲出成品级社交图组——小红书 3:4 组图与公众号 21:9+1:1 封面对，28 版式 × 10 主题，产物是确定性的 HTML→PNG（固定像素 CSS，不是图像模型），版式底线由一个 9 规则 DOM 校验器 + 一个零依赖文档校验器兜住。**本次同日追加实测：真的渲出了 21:9+1:1 封面对 PNG 并肉眼验收，无明显缺陷；版式校验器真跑通，且第一轮就真的抓到一个样本里的实际缺陷（标题超行）。**
- 何时后悔 (regret when): 指望它把封面渲得「有品味」（脚本只保证不溢出/可读/够密；本次肉眼验收的是「工整、无缺陷」，不是审美主观判断的替代，且只验了 1 个主题 × 1 篇文章）；或没预料到它硬依赖 Node + Playwright + 可下载的 Chromium（~260MB，隔离环境第一次尝试超时，第二次补装成功）；或在这个 AGPL-3.0 copyleft 仓库上改代码再分发 / 做对外 SaaS（会触发开源义务或需付费商业授权）；或指望这次验收覆盖了真机发布到公众号编辑器的效果（未测，只验证到"产出正确的静态 PNG"）。

## Why This Score

核心承诺是「文章 → 符合调性、可直接发布的封面对 / 组图 PNG」。初次评估把**确定性支撑层**打穿了（文档校验器 27/27、28×10 设计系统核实、双模板自包含），但核心渲染层因隔离环境缺 Chromium 精确版本未能验证，77 分被 core_layer_tested=false 压在 usable（🛠 可使用）。

**同日追加实测翻转了这一点**：`npx playwright install chromium` 补装 `chromium_headless_shell-1223` 成功后，对同一份样本封面对**真的**跑了 `validate-social-deck.mjs`——第一轮报 1 clean/0 fail/1 WARN（R6：21:9 标题渲成 2 行，超单行上限），这不是空跑，是校验器真的抓到了我样本里的一个真实缺陷；改窄标题后第二轮 2 clean/0 fail/0 warn。随后用 Playwright 独立截图两块 poster，产出真实 PNG，肉眼逐张验收：Swiss 排版工整、IKB 蓝仅出现在 2 处（分类标签+分隔线，未越界）、中文渲染清晰无乱码、"越大越轻"字重规则视觉成立、留白节奏舒适——**没有发现明显缺陷**。claim-009（核心 on-brand 承诺）与 claim-010（版式关卡对真实渲染放行）双双由 untested 转 passed，`core_layer_tested` 由 false 改 true，`evidence_completeness` 由 partial 升级 portable。分数 77 → **85**（🏭 production / team）。

### Top 3 score drivers（更新）

- +30（封顶）: 静态 claim —— 4 个 critical 全部通过（含追加实测的 claim-009 核心承诺 + claim-010 版式关卡），12/14 claim 通过、0 失败，仅 2 个非核心分支（Live Photo、网络取图）仍未测。
- +12 : 维护证据 —— eval 纪律 +5（两个真实校验器，均已实测跑通）、近 90 天活跃 +5、双语 README +2。（release_pipeline +0：无 git tag / release / CI。）
- +3 : 生态 —— 4808★ 落 [1000,5000) 档给 +3（离 5000→+6 就差一点）；molecule 无 layer 加成；真实 AGPL-3.0 → 0 罚分。

### Core outcome（更新）
可观测有效（支撑层 + 核心层）：`check-skill-docs.mjs` 27/27 exit 0；28 版式 + 10 主题真实且 wire 进自包含模板；`validate-social-deck.mjs` 真实运行、真的抓到并验证修复了一个缺陷；AGPL-3.0 为真；**真实渲出的 21:9+1:1 封面对 PNG 经肉眼验收无明显缺陷**。
仍未观测：Live Photo→.pvt、网络取图封面、多主题/多文章批量一致性、真机发布到公众号编辑器的落地效果。

### Scenario breadth（更新）
支撑层：doc 校验器 1 次全通过；28 版式 / 10 主题 / 2 模板全量静态核实。核心层：**1 个主题（IKB）× 1 篇样本文章 × 2 块板（21:9+1:1）已渲染 + 版式校验 + 肉眼验收**——核心层广度从 0 提升到「单样本已验证」，但仍未做多主题/多文章的批量覆盖。evidence_completeness = portable（不是 full）。

### Repeatability
支撑层可复现：doc 校验器确定性（同输入同结论、退出码稳定）；grep 计数可重放。核心层「by construction」的确定性**本次得到部分经验验证**：两轮跑校验器（改标题前后）行为符合预期、退出码稳定；仍未做同输入的双渲染逐位比对；字体走 CDN 是唯一潜在像素变量。

### Failure transparency
高。版式校验器对每条 R1-R9 FAIL 给出像素级 message + 分级修正建议，任一 FAIL 退出 1；本次亲历：R6 WARN 消息清楚指出"哪个元素、超了几行、上限是多少、怎么修"，据此直接改对了标题。doc 校验器逐项 PASS/FAIL 打印并在失败时退 1。

## What Would Move The Score Up

1. （抬到 full / recommendable）多主题（Editorial × 4 剩余 + Swiss 其余强调色）+ 多篇不同题材文章批量渲染 + 校验，验证一致性而非单样本。
2. 补测 Live Photo→.pvt（claim-013）与网络取图封面（claim-014）两条未测分支。
3. 真机发布到公众号编辑器一次，验证粘贴/上传路径与本地 PNG 是否一致（本次只验证到本地渲染正确）。
4. 向上游提 PR 修正 package.json 的 ISC→AGPL 误标。

## Remaining Risks

Ranked.

| Risk | Severity | Impact | Mitigation |
|---|---|---|---|
| AGPL-3.0 copyleft + 双授权 | High | 改代码再分发 / 做对外 SaaS 触发开源义务，否则需付费商业授权（10-30 万 / 3 万） | Park 仅内部做封面自用（不触发）；若要产品化，先谈商业授权 |
| 硬依赖 Node + Playwright + Chromium（~260MB） | Medium | 无浏览器时整条渲染管线不可用；首次安装可能因网络限流失败（本次即遇到过一次） | 部署前预置 chromium；离线环境不可用需提前告知 Vera |
| 审美覆盖面窄（本次只验 1 主题×1 文章） | Medium | 其余 9 套主题、不同题材文章的效果未知 | 正式采用前多主题/多文章批量抽验 |
| 未验证真机发布路径 | Medium | 本地 PNG 正确 ≠ 公众号编辑器粘贴/上传后效果一致 | Vera 首次使用时做一次真机发布验证 |
| 仓库年轻、单作者、无 CI/tag | Low-Med | 长期维护 / 回归风险 | 观察 issue 响应；锁定 commit cf4b810 自用 |
| package.json license 误标 ISC | Low | 授权歧义 | 以 LICENSE（AGPL-3.0）为准；上游提 PR 修正 |

## Verdict

采用，归 **Vera（视觉/配图 Manager）** 作 **封面/社交卡片主线（primary）**：公众号 21:9+1:1 封面对 + 小红书组图，渲出的 PNG/URL 交给 gzh-design 的封面槽（park-content-v1 05_production 主 / 06_assembly 支撑）。与 ponyo（小红书钩子标题公式）是**互补不同子赛道、非备胎**——ponyo 打磨钩子那行字，guizang 渲整张封面。**限定内部使用**以让 AGPL copyleft 保持休眠。**已完成从 🛠 可使用到 🏭 生产线的关键验证**（版式校验器真跑通 + 真实 PNG 肉眼验收无缺陷）；下一步最小动作是多主题/多文章批量抽验 + 一次真机发布验证，把证据从 portable 推向 full。

## Related Artifacts

- Claim map: `claims/claim-map.yaml`
- Plan: `plans/2026-07-09-eval-plan.md`
- Runs:
  - `runs/2026-07-09/run-static-and-render-attempt/run-summary.yaml`（初次评估，浏览器受阻）
  - `runs/2026-07-09/run-static-and-live-render/run-summary.yaml`（同日追加：Chromium 补装成功、真跑校验器、真实渲染 + 肉眼验收）+ artifacts/（sample deck HTML + 两张真实 PNG）
- Verdict calculator input: `verdicts/2026-07-09-verdict-input.yaml`（同日更新：core_layer_tested→true, evidence_completeness→portable）
- Rendered HTML dossier: `verdicts/2026-07-09-verdict.html` (calculator) + vault `dossier.html` (render_verdict_html.py)
