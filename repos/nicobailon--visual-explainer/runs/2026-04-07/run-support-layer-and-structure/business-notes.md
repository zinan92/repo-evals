# Business Notes — support-layer-and-structure

## Scenario

把 visual-explainer 看成一个 hybrid skill：核心价值在 8 个 LLM-driven 命令产出的 styled HTML，但本次只覆盖 support layer —— packaging、SKILL.md 引用、4 个参考模板、install-pi、share.sh 失败模式。LLM 端按 hybrid-repo cap rule 锁住整体 verdict 上限。

## What Happened

| 检查点 | 输入 | 结果 | 证据 |
|--------|------|------|------|
| **marketplace.json + plugin.json** | JSON parse + 版本对比 | ⚠️ 结构合法，但**版本号不一致**：marketplace.json 0.5.1 vs plugin.json 0.6.3 vs SKILL.md 0.6.3 | render-results.json |
| **SKILL.md → 9 个文件引用** | grep + ls | ✅ 全部存在 | — |
| **8 个 commands ↔ SKILL.md 表格** | 一一对齐 | ✅ 8/8 | — |
| **architecture.html** | headless Chromium | ✅ 标题正确，1134 chars，0 errors | screenshots/architecture.png (215KB) |
| **data-table.html** | headless Chromium | ✅ 标题正确，1560 chars，0 errors | screenshots/data-table.png (241KB) |
| **mermaid-flowchart.html** | headless Chromium，CDN 被沙箱挡 | ✅ 页面结构正常，Mermaid SVG 因 CDN 没渲染 | screenshots/mermaid-flowchart.png (62KB) |
| **slide-deck.html** | headless Chromium | ✅ 11 个 slides == 11 个 sections，0 errors | screenshots/slide-deck.png |
| **install-pi.sh 干净环境** | `HOME=/tmp/ve-install-test bash install-pi.sh`（沙箱 HOME） | ❌ `cp: ... No such file or directory` + exit 1 | — |
| **install-pi.sh 已建 parent dir** | `mkdir -p $HOME/.pi/agent/skills && bash install-pi.sh` | ✅ 全部文件复制，{{skill_dir}} 占位符替换为绝对路径 | — |
| **share.sh × 3 失败场景** | 无参数 / 文件不存在 / 缺 vercel-deploy skill | ✅ 三种都 exit 1 + 清晰错误（缺 vercel-deploy 还告诉你 `pi install npm:vercel-deploy`） | — |
| **8 个 LLM-driven 命令端到端** | — | ⚪ 未测（hybrid cap） | — |

## Was The Result Usable?

**Support layer → 几乎可用，但有两个用户看得见的坑：**

**1. install-pi.sh 干净环境必坏。** 这是一个 1 行修复的 bug，但严重程度高 —— 任何 README 路径来的新 Pi 用户跑第一行 `curl -fsSL ... | bash` 都会立即吃个 `cp: No such file or directory`。原因是 line 23 `cp -r plugins/visual-explainer "$SKILL_DIR"` 之前没 `mkdir -p "$(dirname "$SKILL_DIR")"`。脚本对 `$PROMPTS_DIR` 倒是 mkdir 了（line 35），但那在 cp 之后，`set -e` 已经把脚本杀掉。修复就是 1 行。

**2. share.sh 的 vercel-deploy 依赖没文档化。** README 写 `/share | Deploy an HTML page to Vercel and get a live URL`，听起来是开箱即用的。但 share.sh 实际上不调用 vercel CLI，而是去找 `~/.pi/agent/skills/vercel-deploy/scripts/deploy.sh`。这个外部 skill 在 README 任何地方都没提。新用户跑 `/share` 会被告知"vercel-deploy skill not found"然后自己去 google。错误信息至少告诉你怎么装（`pi install npm:vercel-deploy`），所以不算 silent fail，但是把"开箱即用"误导成了"先装个隐形依赖"。

**4 个 HTML 模板 → 完全可用。** Headless Chromium 全部成功渲染，0 个 JS 错误，标题/正文都是真内容。Mermaid 模板的 SVG 因为我的沙箱挡了 jsdelivr CDN 没生成出来，但页面结构本身没问题，对在线用户没影响。slide-deck.html 的 11 个 slides 跟 11 个 sections 数量精确一致 —— 显然是真的把 slide 做成了独立 sections，不是嘴炮。

**LLM 端 → 没测，按 hybrid cap 锁住。** 整个 repo 的真正用户价值在 8 个 slash command 调出来的 styled HTML 是不是真的好看、是不是真的避开 anti-AI-slop 列表里那些禁忌、是不是真的会读 references/ —— 这些都得在真实 Claude Code 会话里验证。本次 eval 完全没碰，按更新后的 framework rule 整体 verdict 上限就是 `usable`。

## Anything Surprising?

1. **Version drift 是个小但典型的 packaging bug。** `marketplace.json` 写 0.5.1，`plugin.json` 写 0.6.3，SKILL.md frontmatter 也写 0.6.3。明显是发版时只 bump 了一边。Claude Code marketplace 拉取时会显示 0.5.1（用户以为装的是旧版），但安装后实际是 0.6.3。这个问题可以加 CI assertion 防止再发生。

2. **install-pi.sh 的 bug 是"有 ~/.pi 目录就不会被发现"的典型 cleanup-blind spot。** Maintainer 自己测试时 `~/.pi/agent/skills/` 早就因为别的 skill 存在了，所以 `cp` 永远成功。只有 fresh install 用户会踩。这种 bug 必须在 ephemeral container / fresh HOME 里测试才能抓到。

3. **Mermaid + ELK + jsdelivr ESM imports 是个值得留意的依赖选择。** mermaid-flowchart.html 用 `import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/...'` 直接 ESM 加载。优点：零 build step，HTML 文件真的 self-contained。缺点：用户网络挡 jsdelivr 就坏了（公司内网、防火墙、本次评测环境），且依赖 CDN 长期可用。frontend-slides 用 inline base CSS 完全规避了这个 trade-off，visual-explainer 选的是另一个 trade-off。

4. **share.sh 把 vercel 部署外包给另一个 skill 是合理的解耦，但文档没跟上。** 让 visual-explainer 不直接依赖 vercel CLI 是好设计（其它 skill 也能复用 vercel-deploy），但 README 完全没提"你需要先装 vercel-deploy"，导致用户体验是"看起来开箱即用但其实不是"。

5. **跟 frontend-slides 横向对比有意思：** 两个都是 hybrid skill repo，都有 12 个左右的 prompt-driven 入口，都受 hybrid-cap 限制。但：
   - frontend-slides 的 support layer 完全没 bug；visual-explainer 有 install-pi 的 1 行 bug + version drift + 隐形 vercel-deploy 依赖
   - frontend-slides 的 README 100% 跟代码对齐；visual-explainer 的 README 在 share 命令上误导
   - 两个都是 `usable`，但 visual-explainer 离 `reusable` 的距离更远 —— 不光要补 LLM 端测试，还要先修这 3 个 support layer 问题

6. **failure transparency 这一项没失分。** share.sh 的 3 个失败场景全部 exit 1 + 清晰错误，错误信息甚至教你下一步。这个跟 content-downloader 的 wechat/x silent fail 是天壤之别。
