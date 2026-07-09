# Final Verdict

## Repo

- **Name**: helloianneo/ian-xiaohei-illustrations
- **Version tested**: main@HEAD (2026-06-03 push), commit 91b5608
- **Date**: 2026-07-09
- **Archetype**: prompt-skill
- **Layer**: molecule
- **Score**: 66 /100  (from `verdict_calculator.py`)
- **Category**: 🛠 Available / 可使用
- **Tier**: self (≥65) — Self-use OK / 自用 OK

## 一句话结论

- 若采用: Vera 得到一套有识别度、反 PPT、带固定「小黑」IP 的中文正文配图提示词系统 —— 风格 DNA + 8 种结构类型 + 参数化单张生图模板 + QA 清单，把「配一张图」升级成「把一个认知动作画出来」。
- 何时会后悔: 指望它「装好即出图」（真正出图要外部图像模型，Claude Code 无内置 image_gen）；或指望图的质量稳定 on-brand（本次评估无法运行图像模型，图好不好、中文会不会出错字，全未验证）；或在这个单一作者、6 周新、无 CI 的仓库上建长期强依赖。

## Why This Score

核心价值——「用一套可复用的风格语言，把中文文章里的一个判断/流程/隐喻画成有品牌感的正文配图」——在**提示词脚手架层面**是真实且完整的：SKILL.md frontmatter 合法且带明确触发词，5 份 references（风格 DNA / 小黑 IP / 构图 / 生图模板 / QA）全部解析得到且规则自洽，README 承诺的 4 类能力（shot list / 生成 / 单概念 / 改图）都能在工作流里找到路径，MIT 许可证真实。但**真正的产物是一张图**，由外部图像模型（默认 Codex 内置 image_gen）渲染 —— 本次评估无图像模型凭证、无法运行，所以「图是否 on-brand / 中文是否可读 / 是否避开 PPT 感」这一整层是黑的。作者示例图只证明「这套 prompt 出过东西」，不证明「你这篇每张都好」。

### Top 3 score drivers

- **+15 静态 claim**：提示词脚手架干净完整 —— 2/2 critical support 全过（frontmatter 合法 + 引用零悬挂）、4 条 high 过（能力覆盖 / 风格三件套自洽 / 模板参数化 / 触发规格），8/12 通过、0 失败。触发精度记 passed_with_concerns（未做在线 trigger_test）扣掉 1 分（+2→+1）。
- **+6 生态 / +5 维护**：7354★ 落在 ≥5000 档给 +6；但维护只 +5（仅 recently_active）—— 无 CI（release_pipeline=1）、无自动化 eval harness（eval_discipline=1，只有提示词侧 QA 清单）、单一 committer、无多语 README，三项 +5 门槛都没够到。
- **0 layer / −2 critical-untested / 天花板封顶**：molecule 无 layer 加成（不像 atom +5）；核心「图 on-brand」critical 因无法运行图像模型记 untested（−2）；且 core_layer_tested=false 把类别**硬封在 🛠 available**（无法进 🏭 production）。这正是防注水规则按预期生效 —— 不能因为脚手架漂亮就把一个核心产物无法验证的图像 skill 算成生产级。

### Core outcome
可观测有效（静态）：一套自洽、可移植（模型无关的英文 prompt 模板）的风格系统 + shot list 规划口径 + QA 迭代规则；随包 22 张作者校准样例证明这套风格能出图。
未观测（核心层全黑）：任意真实文章的实际出图质量、是否 on-brand、小黑是否真承担核心动作、中文标注是否可读、是否避开 PPT/可爱/左上角标题 —— 全部依赖一个本次评估无法运行的外部图像模型。

### Scenario breadth
静态覆盖：4 类 README 能力 × 提示词/工作流路径核对全过；5 份 references 逐份读过、规则一致。实测生成：0 张（无图像模型凭证）。跨模型 / 跨文章一致性：未测 → evidence_completeness = partial。

### Repeatability
文件级可复现：frontmatter 解析、引用存在性、许可证、能力映射都是确定性静态检查，同输入同结论。图像产物层不可复现 —— 出图依赖外部模型那次发挥，且 skill 自己承认会有错字 / 风格漂移。

### Failure transparency
中：skill 主动列了失败信号（左上角标题 / 太像 PPT / 小黑装饰 / 中文错字）和对应迭代对策（局部改图 / 减少标注重生成），失败时 agent 有可操作的下一步。但没有任何自动化校验能在出图后确定性地判「合格 / 不合格」，全靠 agent/人肉照 QA 清单看。

## What Would Move The Score Up

1. (~+? 抬升 core_layer_tested + evidence→portable) 让 Vera 在真实 Codex（或外接 nano-banana/Gemini/Flux）里跑完 1 篇真文章、生成 4-8 张，按 qa-checklist.md 逐项打分并留存产物 —— 这是把核心层从「黑」变「亮」、把类别从 available 往上抬的唯一动作。
2. (~+5 维护) 固定一个图像模型 + 参数写成可复现脚本 / eval-cases，让「合规判定」从人肉看变成半自动 → eval_discipline 到 2。
3. (~+2 维护) 补一份 README.en.md → multilingual_readme=true（+2），顺带扩大可采用面。

## Remaining Risks

| Risk | Severity | Impact | Mitigation |
|---|---|---|---|
| 图像模型依赖：Claude Code 无内置 image_gen | 高 | Park 若跑在 Claude Code，生成步骤开箱不工作 | Vera 在 Codex 里跑，或把 prompt-template 接到外部图像模型（模板本身模型无关，可移植） |
| 核心产物质量未验证 | 高 | 图可能不 on-brand / 中文出错字 / 风格漂移 | 每张过 qa-checklist + 人工核字；错字多则减少标注重生成 |
| bus-factor 1（单作者 / 9 commits / 6 周新 / 无 CI） | 中 | 长期维护 / 修 bug 不确定 | skill 是自包含提示词，可 fork 冻结自用；观察维护度几周 |
| 许可 / IP | 低 | MIT 允许内部自用与改编 | NOTICE 请求保留「小黑」IP 署名；对外分发注意署名，别把「小黑」当自有品牌 |
| 平台锁定（Codex 生态 + $ 触发语法） | 低 | 非 Codex host 上触发 / 调用方式需适配 | 提示词与风格 DNA 可抽出复用，触发层按 host 适配 |

## Verdict

采用 —— 但**归属 Vera 作为「正文配图」这一条窄车道的 primary skill**（park-content-v1 的 05_production，产出后交接 06_assembly 的 gzh-design），不作为封面/KV/信息图/通用配图的通用工具。唤醒靠 description 触发词或 `$ian-xiaohei-illustrations`。**采用有硬前提**：出图要一个能生图的 runtime（Codex 内置 image_gen，或给 prompt-template 外接图像模型）；Claude Code 开箱没有。下一步最小动作：Vera 用一篇真实文章跑一次完整闭环、按 qa-checklist 打分，把核心层从 untested 抬升到实测，evidence 从 partial 升到 portable。

## Related Artifacts

- Claim map: `../claims/claim-map.yaml`
- Plan: `../plans/2026-07-09-eval-plan.md`
- Verdict calculator input: `2026-07-09-verdict-input.yaml`
- Rendered HTML dossier: `2026-07-09-verdict.html`
