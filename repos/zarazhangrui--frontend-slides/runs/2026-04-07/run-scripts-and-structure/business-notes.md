# Business Notes — scripts-and-structure

## Scenario

把 frontend-slides 看成两个东西：一个 LLM-driven 的 Claude Code skill（不可执行，纯 prompt 工程）+ 三个支持脚本（extract-pptx / export-pdf / deploy）。本次评测覆盖：所有可执行/可静态验证的部分。LLM 端到端生成不在本次范围。

## What Happened

| 检查点 | 输入 | 结果 | 证据 |
|--------|------|------|------|
| **Plugin marketplace 结构** | `.claude-plugin/marketplace.json` + `plugins/.../plugin.json` | ✅ 合法 JSON，source path 正确，所有镜像文件存在 | `diff -q SKILL.md plugins/.../SKILL.md` 一致 |
| **SKILL.md 引用完整性** | grep markdown 链接 → 7 个文件 | ✅ 全部 OK | 见 grep 输出 |
| **PPT 提取（Sam Altman 15-slide）** | 真实 .pptx | ✅ 15 slides JSON + 15 PNG 落盘 | `extract-test/extracted-slides.json` |
| **PPT 提取（binary-choices 8-slide）** | 真实 .pptx | ✅ 8 slides JSON | `extract-test2/extracted-slides.json` |
| **PDF 导出（3-slide HTML）** | 自建 sample-deck.html | ✅ 3 页 PDF 1.4，42KB，`file` 确认 | `sample-deck.pdf` |
| **PDF 失败 — 无 .slide** | no-slides.html | ✅ 清晰 ERROR + 退出码 1 + 提示用 `<div class="slide">` | stderr |
| **PDF 失败 — 不存在文件** | nonexistent.html | ✅ "File not found" + 退出码 1 | stderr |
| **12 个 style preset** | grep `^### [0-9]` STYLE_PRESETS.md | ✅ 12 个 numbered presets，每个含 colors + typography + signature elements | `wc` |
| **viewport-base.css 内容** | 静态阅读 | ✅ `.slide { overflow:hidden; height:100dvh }` + clamp() vars | 文件内容 |

## Was The Result Usable?

**A 层 → 是。** 三个脚本都跑通了；plugin 结构是合法的；SKILL.md 引用没漂移；STYLE_PRESETS 的 12 个 preset 是真存在的。这意味着如果你 `/plugin install frontend-slides@frontend-slides`，它会真的装上一个完整的 skill 而不是装到一半发现引用断裂。

**B 层 → 未知。** Phase 1-3 的产物质量（"非设计师能不能拿到不像 AI slop 的 deck"）这次没有验证，因为那需要在 Claude Code 里跑一次完整 `/frontend-slides` 会话。**这是评测的天花板**：A 层全过 + B 层未测 = 最多 `reusable`，不能 `recommendable`。

## Anything Surprising?

1. **比 content-downloader 健康得多。** 没有任何 silent failure，三个脚本的退出码 / 错误信息都正确。export-pdf.sh 的 "0 slides found" 错误信息甚至会告诉你应该用哪个 class —— 非常体贴。

2. **extract-pptx.py 的 title 检测有 bug。** 两个完全不同的 PPT，所有 slide 的 title 都是空字符串。代码用 `if shape == slide.shapes.title:` 来识别 title，但当 title placeholder 为 None 时这个比较永远 False —— 文字会落到 `content` 数组里而不是 `title` 字段。下游 LLM 在 Phase 4 confirm 时看到的会是 "Slide 1: (no title)"。信息没丢但语义错位。

3. **content 数组里全是空 text frame。** 没有过滤空字符串的 text shape，所以 JSON 里有大量 `{"type":"text","content":""}` 噪音。Phase 4 的 LLM 会被噪音淹没。

4. **plugin 镜像结构两份文件。** `SKILL.md` 在 root 和 `plugins/frontend-slides/skills/frontend-slides/` 下各一份，`diff -q` 完全一致。这避免了"装上去和源码不同"的歧义，但也意味着每次更新要同步两边 —— 没看到自动化，是手工同步的脆弱点。

5. **README claims 跟代码 100% 对齐**。这是评测里很少见的情况 —— 12 个 preset 真的有 12 个，所有 SKILL.md 引用真的存在，所有脚本真的能跑。文档没有提前承诺还没做的东西。

6. **整个 "skill 价值" 锁在 SKILL.md 里。** 真正决定产物好坏的是那 322 行 prompt（viewport rules、density limits、phase flow、anti-AI-slop guidance）—— 这些只能用 LLM 实跑去验证，静态分析只能确认 prompt 的结构合理性。
