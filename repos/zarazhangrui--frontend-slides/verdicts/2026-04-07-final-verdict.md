# Final Verdict — frontend-slides

## Repo

- **Name:** zarazhangrui/frontend-slides
- **Date:** 2026-04-07
- **Final bucket:** `usable`

## Why This Bucket

### Core outcome — 强（A 层全过）

| 检查 | 结果 |
|------|------|
| Plugin marketplace + plugin.json 结构 | ✅ |
| SKILL.md 引用的 7 个文件全部存在 | ✅ |
| `extract-pptx.py` 在 2 个真实 PPT 上跑通 | ✅（带 title 提取小 bug） |
| `export-pdf.sh` 3-slide HTML → 3 页有效 PDF | ✅ |
| 12 个 style preset 在 STYLE_PRESETS.md 里真的有 | ✅ |
| viewport-base.css 包含 `.slide overflow:hidden + clamp() + 100dvh` | ✅ |

### Scenario breadth — 中等

A 层覆盖了 packaging / SKILL integrity / extract / export / failure modes / 设计契约。
B 层（端到端 LLM 生成）完全没碰，是评测的天花板限制。

### Repeatability — 不适用

脚本是无状态的；LLM 端的 repeatability 没测。

### Failure transparency — 强

`export-pdf.sh` 的两种失败场景（无 .slide / 文件不存在）都给清晰错误 + 退出码 1。
`no-slides` 的错误甚至会告诉你应该用哪个 CSS class —— 这是评测里最体贴的失败信息之一。
跟 content-downloader 那种 silent failure 是天壤之别。

## What I Would Say In Plain English

> "如果你想用它当 Claude Code skill，安装路径、底层脚本、文件引用都已经 ready —— 不会装一半坏掉。两个支持脚本（PPT 提取 + PDF 导出）都跑得通，错误处理也很好。
>
> 但 skill 真正的价值在 SKILL.md 那 322 行 prompt 里，能不能让 LLM 真的产出 viewport-fit、风格独特、不像 AI slop 的 deck —— **这次没验证**。要给 `recommendable`，必须再跑一次完整的 `/frontend-slides` 端到端会话，拿到产物用 export-pdf 截图后对照 12 个 preset 的视觉契约打分。"

定位 = `usable`：A 层执行/结构/打包全过，说明 supporting layer 很强；但最关键的核心用户价值层，也就是 LLM 真的能不能按这个 skill 产出好 deck，还没被验证。按更新后的框架规则，**untested core layer 会把整体 verdict 封顶在 `usable`**。

跟 content-downloader 对比：
- content-downloader = `usable`：4 个平台 2 个 silent fail，违反自己的 fail 契约
- frontend-slides = `usable`：support layer 很强，但核心 LLM 层未测

## Remaining Risks

1. **B 层完全空白。** 只有真的让 Claude 跑一次 `/frontend-slides` 才知道：viewport non-negotiable 是不是真的能阻止 LLM 写 px 字号、12 个 preset 里 LLM 是不是真的会均匀分布而不是永远跳到某 1-2 个、"show don't tell" 在 Phase 2 是否真的产出 3 个 distinct preview。
2. **extract-pptx.py 的 title 提取 bug。** 两个测试 PPT 全部 title 为空，是 `shape == slide.shapes.title` 在 None 时永远 False 的经典坑。下游 Phase 4 confirm 显示会是一堆 "(no title)"。修复成本很低（5 行）。
3. **extract-pptx.py 没过滤空 text frame。** JSON content 数组里有大量空字符串占位，污染 LLM 上下文。
4. **deploy.sh 未验证。** 跟 Vercel 的实际握手没测过，登录态边界 / 文件夹 vs 单文件 / 路径含空格的实际行为都没数据。
5. **plugin 文件双份手工同步。** root 和 `plugins/.../skills/.../` 各一份，目前 `diff -q` 一致，但没看到自动同步机制 —— 长期会漂移。
6. **复杂 PPT 未测。** SmartArt / 嵌入视频 / 表格 / 自定义 shape 的提取行为未知。

## Recommended Next Actions

按优先级：

1. **跑一次端到端 LLM session**（最高优先）：在 Claude Code 里 `/frontend-slides` 给一个真实 topic，对每个 mood × 多个 preset 各跑一次，用 export-pdf.sh 截图后人工打分 viewport-fit / 风格独特性 / 内容质量。修完这一步可以晋级 `recommendable`。
2. **修 extract-pptx 的 title 提取**：用 placeholder type 或 `slide.shapes.title is not None` 做 None-check。
3. **过滤空 text frame**：`if shape.text.strip()` 再加进 content 数组。
4. **加一个 sample-deck.html fixture**：放在 `tests/fixtures/` 里，CI 跑 export-pdf.sh smoke。
5. **加 plugin 双份同步检查**：CI 里 `diff -r SKILL.md plugins/.../SKILL.md` 防止漂移。
6. **测一次 deploy.sh**：用一个一次性 Vercel 项目跑通后删掉，记录错误处理和 happy path。
