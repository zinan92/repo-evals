# Mark 评估摘要 — pbakaus/impeccable

> 正式 repo-evals 已跑完。HTML dossier：`dossier.html`（同目录）。
> 评估日期：2026-06-30 ｜ 版本：main@HEAD（package v3.1.0 / skill-v3.8.0）
> 分数 / 归类由 `verdict_calculator.py` + `render_verdict_html.py` 计算，非人工判断。

## 1. 核心结论

| 项 | 值 |
|---|---|
| **Score** | **68 / 100** |
| **Category** | 🛠 **Available / 可使用** |
| **Tier** | 🛠 **Self-use OK / 自用 OK**（self） |
| **Confidence** | medium |
| **层级** | **Compound**（内嵌一个已验证的确定性 atom：44 规则 detector） |
| **License** | Apache-2.0 ✅ |
| **维护** | 极强：42,293 stars、27 个 tagged releases、CI、62 个测试文件、昨日仍在推送 |

**score breakdown**：base 40 + 静态 claims +7 + 维护 +15 + 生态 +9 + 层级 −3 = **68**。

**为什么封顶在"可使用"而非"可用于生产"**：hybrid-skill 规则要求对"面向用户的核心层"
做端到端验证。Impeccable 的核心承诺是"让你的 AI 更会设计"——这是 LLM 质量类 claim，
本次**没有做 live design-generation run**（2 个 critical claim 只覆盖了 1 个）。
确定性层全部验证通过；主观质量提升未验证 → 天花板锁在 usable / 可使用。

## 2. 它是什么

一句话：**给 AI 编程 agent 用的一套"设计语言"** —— 1 个 skill、23 条命令，外加一个
44 条规则的**确定性检查器**，专门洗掉 AI 生成前端那股一眼假的味道（Inter 字体、紫蓝渐变、
卡片套卡片、bounce 动效、彩底灰字）。确定性检查**不需要任何 API key**。

起点是 Anthropic 的 `frontend-design` skill，在其之上加了命令词汇、确定性 linter、
跨 harness 安装和编辑器 hook。

## 3. Top 3 分数驱动

- **+15 维护信号**：42k stars 之外，27 个 tagged releases + CI + 62 个测试文件 + 昨日推送。
- **+9 生态 / +7 静态**：确定性层 5 条 claim 全部实证通过（detector 实跑、规则数、命令数、引用完整、跨 harness）。
- **−3 层级 + 封顶**：compound 核心 LLM 层未 live 验证（1/2 critical 覆盖），卡在 68 / usable。

## 4. 已验证 vs 未验证

**已验证（确定性层，硬证据，status=passed）**
- ✅ detector 无 API key 运行成功，报出 overused-font / bounce-easing / 配色漂移（带行号+理由）
- ✅ 规则数 ≥ 44（实测 48 个 rule id）
- ✅ 23 命令存在且有 reference 文档
- ✅ SKILL.md 引用全部解析得到
- ✅ 14 种 harness payload（.claude/.codex/.cursor/.gemini/… 已存在）

**未验证（核心 LLM 层 → 封顶原因，status=untested）**
- ⛔ "真的让 AI 产出更会设计"——需要真实 agent 会话生成 UI 并对照质量契约打分
- ⛔ anti-slop 规则在真实产出中被遵守——同上，依赖 live run

## 5. 这个 repo 适合什么职位的人用

**前端 / 设计方向的角色** —— 用 AI agent 产出界面、需要稳定设计质量与共同设计语言的人。

## 6. 公司现有角色匹配

| 角色 | 是否匹配 |
|---|---|
| Joanna（内容） | ❌ 不匹配，这是设计/前端工具 |
| Mark（技能治理） | ⭕ 仅作为 owner 暂管，不是使用者 |

**公司目前没有"设计 / 前端"角色。** 这个 skill 暗示需要一个新角色方向：
**Designer / Frontend Lead**。按规则，Mark **不直接创建角色**，需 Park 确认（见第 9 节）。

## 7. 建议归属与放置位置

- 现状：该 skill 已在 harness 层全局可用（`~/.claude/skills/impeccable`），任何角色都能调用。
- 归属建议：**暂作为未归属工具**，由 Mark 管理；evals 证据存于本目录。
- 若 Park 同意建立设计角色 → 把唤醒指引写进 `010_<角色>/` 角色目录（不搬 HTML dossier）。

## 8. 如何唤醒 / 何时不要用

**如何唤醒**
- 确定性检查（无需 LLM/key）：`npx impeccable detect <文件|目录|URL>`
- 在 AI 工具里：`/impeccable init` 一次性写设计上下文，再用 `polish` / `critique` / `audit` / `craft` / `bolder` 等命令
- 未来若有设计角色：先 `@设计角色`，再让其调用 `/impeccable <command>`

**适合使用**
- AI 生成的前端要做设计质量把关 / 去 AI 味
- 团队想和 agent 之间建立共同设计语言
- 在 CI / 编辑时做确定性设计 linting

**不适合使用**
- 纯内容 / 非前端任务（那是 Joanna）
- 期待"装上就自动变好看"而不投入 live 迭代——主观提升本次未被证明
- 不想让安装器写入多个 harness 目录时（全局安装前先确认范围）

## 9. 需要 Park 确认的事

> 目前没有合适 owner。这个 skill 暗示需要一个新角色：**Designer / Frontend Lead（设计/前端）**。
>
> 1. 要不要建立这个角色 profile？
> 2. 如果要建，这个角色叫什么名字？
> 3. 如果暂不建：我就把 impeccable 标记为"未具象化角色的未归属工具"，由 Mark 暂管。

## 10. 下一步最小动作（提升评分）

1. 在 Claude Code 里跑一次真实会话：`/impeccable craft` → `/impeccable critique`，
   把产出对照 SKILL.md 质量契约逐项打分，并用 `npx impeccable detect` 复检
   （覆盖第 2 个 critical claim、解锁 compound 天花板，有望从 68 → 80+ 进入 team 区间）。
2. Park 决定是否设立"设计/前端"角色。
3. 确认后把唤醒指引写进对应角色目录或保留为未归属工具。

## 风险 / Gotchas

- 头部承诺是 LLM 质量类 claim，效果依赖你的模型 + prompt，本次未 live 验证。
- 安装器会自动写入多个 harness 目录（~/.claude、~/.codex、.cursor…），全局安装前确认范围。
- 无 CHANGELOG 文件，但 27 个 GitHub releases 充当变更记录。
