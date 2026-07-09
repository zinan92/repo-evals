# repo-evals summary — XBuilderLAB/cheat-on-content

> Mark ｜ 正式 repo-evals ｜ 评估日 2026-07-05 ｜ 版本 main@HEAD (tag v0.1.0)
> 方法：clean clone 静态源码审查 + GitHub API。**未跑 live end-to-end**（compound skill，需真实账号 + 平台登录态 + T+3d 复盘窗口）。

## 一句话判断

一套**认真、工程化的内容「校准循环」skill**（打分 → 盲预测 → 复盘 → 进化 rubric），机制是真的、护栏是真的；但 README 的「一个月百万粉」是**不可证伪的营销**。采用它的**方法**，忽略它的**增长承诺**。

## 核心分数

| 项目 | 值 |
|---|---|
| **Score** | **70 / 100** |
| **Category** | 🛠 **可使用 / Available** |
| **Tier** | 🛠 自用 OK（self-use） |
| **Confidence** | medium |
| **Layer** | **compound**（15 子 skill 运行时路由 + 模式检测 + spawn 盲打分子 agent） |
| **Archetype** | orchestrator |
| Final bucket | usable（→ 类别天花板 = Available，**永远到不了 Production**，除非补一次 live run） |

**分数构成**：base 40 + 静态claim +15 + 维护信号 +12 + 生态(5.3k stars) +6 + compound层 −3 = **70**。

**为什么是 70 而不是更高**（top deltas）：
1. **+15 静态 claim**：6 条机制 claim 全部读代码验证通过（不可改预测 hook、盲打分隔离、bump 全量重打+跨模型审、schema 迁移链、营销隔离）。
2. **−天花板**：compound skill + 没有 live run → final bucket 锁死在 `usable`，类别最高只能 Available，**「百万粉」这类效果承诺无法把分数抬进生产级**。
3. **2/4 关键 claim 未覆盖**：两条 critical 效果承诺（1M 粉 / 判断力 ×10）记为 untested —— 不是造假，是**结构上不可证伪 / 需要数月纵向数据**。

## 它到底是什么

- **不是**一个涨粉工具、不替你写、不替你分发。
- **是**一面镜子 + 一套纪律：把「我觉得这条会火」变成「发布前写死的盲预测」，发布 3 天后用真实数据结账，连续偏差后**逼你升级打分公式**，且升级要过「全量重打 + 排序一致 + 跨模型审核」才放行。
- 卖点是 **judge sharper（判断更准）**，不是 **ship more（发得更多）**。

## 营销 vs 实现（本次评估的核心发现）

| README 门面（不可证伪） | 实际实现（读代码验证为真） |
|---|---|
| 「一个月 0→100 万粉」 | `hooks/prediction-immutability.sh` 真的用 PreToolUse hook 拦截对预测段的编辑 |
| 「它预测了你会读到这一行」 | `cheat-score-blind` 盲打分子 agent 硬拒读实绩数据 + grep 自检污染 |
| 量子 / 宿命话术 | bump 升级要 Spearman 排序一致 + pairwise 不回退 + 跨模型 audit |

**难得的诚实**：仓库自己把营销话术**隔离在 README**，SKILL.md 明确「Cluely 风格 hook 不要写进 rubric_notes.md / 预测日志」，并用 ✅/⬜ 诚实标注哪些没做完。这是加分项。

## 角色归属建议

| 问题 | 结论 |
|---|---|
| 适合什么职位的人用 | **内容判断 / 内容运营负责人**（个人创作者、获客型内容主线的 owner） |
| 公司现有角色匹配 | ✅ **Joanna**（内容判断、内容生产、获客型内容主线）—— 正中她的 remit |
| 是否需要新角色 | 否。不需要建新角色，不需要 Park 确认角色名 |
| 建议 owner | **Joanna** |
| 建议放置位置 | 若采用 → skill card 放 `001_agent-os/skills/cheat-on-content/SKILL.md`，Joanna 的 JD 链接引用；当前先作为**评估 dossier** 存档于本目录 |

## 如何唤醒

- **归属 Joanna 后**：先 `@Joanna`，再说「用 cheat-on-content 帮我把这条内容跑一次盲预测 / 复盘 / 升级 rubric」。
- **当前（未正式采用）**：先 `@Mark`，引用本 dossier `001_agent-os/skills/_evaluations/260705_XBuilderLAB_cheat-on-content/`。

**适合使用**
- 你有一个**长期、可量化**的内容主线（观点视频 / 长文 / thread），愿意连续跑几周至几个月。
- 你想把「凭感觉判断爆款」变成可复盘、会进化的个人打分系统。
- 你已经在产内容，缺的是「发布前后的判断纪律」，不是「把内容做出来」。

**不适合使用 / 不要唤醒**
- 想「快速涨粉」或把它当增长引擎 —— 它不是。
- 一次性 / 短平快内容，不打算连续复盘。
- 做非观点视频形态且不愿自己写 rubric（内置 rubric 只基于**一个**中文观点视频博主拟合）。
- 不愿意给复盘 adapter 配平台登录态（抖音/小红书/领英/B站都要 Playwright + 扫码）。

## 风险 & gotchas

1. **效果未验证**：「百万粉 / 判断力 ×10」无 live 证据，结构上不可证伪。买方法，别买承诺。
2. **install.sh 动 live skill 目录**：会 symlink 15 个 skill 进 `~/.claude/skills`。谨慎的话先在沙箱跑（本次评估**未执行** install.sh）。
3. **重、慢热**：真正见效要数周至数月纪律性使用。
4. **adapter 脆弱**：平台反爬，抓数 adapter 可能随时间失效；且需真实登录凭证。
5. **rubric 迁移成本**：升级要全量重打校准池，样本越多越贵（这是设计上的「升级阻尼」，不是 bug）。

## 下一步最小动作

- **若 Park 想采用**：在**沙箱化 / 独立的 agent skill 目录**里，用一个**测试账号**跑一次完整闭环（`初始化` → `启动预测` → `已发布` → `复盘`），记录触发命中 + 盲隔离行为。这一次 live run 就能把 `core_layer_tested` 抬起来、突破 compound 天花板，分数有望进入 65–80 的「自用 OK / 团队就绪」区间。
- **若暂不采用**：保留本 dossier 作为证据库，等 Joanna 有真实内容主线需要「校准判断」时再启动。

## 产物路径

- **HTML dossier（本目录）**：`001_agent-os/skills/_evaluations/260705_XBuilderLAB_cheat-on-content/dossier.html`
- **本摘要**：`001_agent-os/skills/_evaluations/260705_XBuilderLAB_cheat-on-content/summary.md`
- **repo-evals 框架产物**：`~/repo-evals/repos/XBuilderLAB--cheat-on-content/`（repo.yaml / claims/claim-map.yaml / plans / verdicts/2026-07-05-verdict.html）
