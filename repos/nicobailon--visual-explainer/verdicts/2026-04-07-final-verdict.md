# Final Verdict — visual-explainer

## Repo

- **Name:** nicobailon/visual-explainer
- **Date:** 2026-04-07
- **Final bucket:** `usable`
- **Framework:** repo-evals @ `21f90eb` (provenance + hybrid-repo cap)
- **Target commit:** `9a97a58`

## Why This Bucket

### Hybrid-repo cap rule applies

`visual-explainer` 的真正用户价值在 8 个 LLM-driven 命令产出的 styled HTML（generate-web-diagram / diff-review / plan-review / project-recap / fact-check / generate-visual-plan / generate-slides / share）。本次 eval **完全没碰** LLM 端 —— 跟 frontend-slides 一样，按 framework 的 hybrid-repo cap rule，**整体 verdict 上限 = `usable`**。

### Support layer — 强但有 3 处 bug

| 检查 | 结果 |
|------|------|
| Plugin marketplace + plugin.json 结构 | ⚠️ 合法但版本号不一致（0.5.1 vs 0.6.3） |
| SKILL.md 9 个文件引用 | ✅ 全部存在 |
| 8 个 commands ↔ SKILL.md 表格 | ✅ 全部对齐 |
| 4 个 HTML 模板 headless 渲染 | ✅ 0 page errors |
| install-pi.sh 干净环境 | ❌ `cp: No such file or directory`（缺 mkdir -p） |
| install-pi.sh 已建 parent dir | ✅ 占位符替换正确 |
| share.sh 失败模式 × 3 | ✅ 全部 exit 1 + 清晰错误 |
| share.sh 的 vercel-deploy 依赖文档化 | ❌ README 没提 |

### Failure transparency — 强

share.sh 的 3 个失败场景全部清晰报错 + 退出码 1，连"缺 vercel-deploy 怎么装"都告诉你。这一项跟 content-downloader 的 silent fail 是天壤之别。

## What I Would Say In Plain English

> "Support layer 大体上 ready：4 个 HTML 模板渲染干净、SKILL.md 引用都对、错误处理也好。但有 3 个用户看得见的坑：
>
> 1. **install-pi.sh 在干净环境必坏** — 1 行 mkdir 修复就行，但任何 fresh Pi 用户都会踩。
> 2. **marketplace.json 写 0.5.1，plugin.json 写 0.6.3** — Claude Code marketplace 会显示旧版号。
> 3. **share.sh 静悄悄要一个 vercel-deploy skill** — README 完全没提这个隐形依赖，新用户跑 /share 才会发现。
>
> 而真正的核心价值（8 个 slash command 产出的 styled HTML）这次完全没测 —— hybrid 框架规则把整体 verdict 锁在 `usable`。修这 3 个 support layer bug + 跑一次端到端 LLM 会话评测，可以晋级 `reusable`。"

## 三+1 repo 横向对比

| Repo | Bucket | Support layer | Core LLM 层 | README ↔ 代码 | Failure transparency |
|------|--------|--------------|------------|--------------|---------------------|
| content-downloader | `usable` | n/a (无) | n/a | ❌ 2 silent fails | ❌ wechat/x 假装成功 |
| frontend-slides | `usable` | ✅ 完美 | ⚪ 未测 | ✅ 100% 对齐 | ✅ 优秀 |
| content-extractor | `usable` | ⚠️ 视频强 audio 假 | ⚪ 部分（视频路径） | ❌ 3 处不对齐 | ✅ 优秀 |
| **visual-explainer** | **`usable`** | **⚠️ 3 处 bug** | **⚪ 未测** | **❌ install + share + version 三处** | **✅ 优秀** |

四个 repo 都落在 `usable`，但内部健康度不一样：
- **frontend-slides** 离 `reusable` 最近（只缺 LLM 端验证）
- **visual-explainer** 离 `reusable` 第二近（缺 LLM 端验证 + 3 处 1-行 bug）
- **content-extractor** 离 `reusable` 第三远（要修 audio adapter + 测试套件 + Mac 性能）
- **content-downloader** 离 `reusable` 最远（要修 silent fails 的根本设计）

## Remaining Risks

1. **B 层完全空白。** LLM 是否真的会读 references/ + templates/，是否真的避开 SKILL.md 列出的 anti-AI-slop 模式（neon dashboard / gradient mesh / Inter+violet），proactive table rendering 触发是否可靠 —— 全部未知。
2. **install-pi.sh 干净环境的 mkdir bug** 是 cleanup-blind spot：maintainer 自己测试时 ~/.pi 早就存在所以从来不会踩。必须在 fresh container 才能抓到。
3. **Marketplace version drift** 可能让 Claude Code marketplace 显示旧版号 —— 用户以为装的是 0.5.1，实际上拉到的是 0.6.3。
4. **share.sh 的隐形依赖** 让"开箱即用"的承诺打折扣，且依赖另一个 skill 长期可用 + maintained。
5. **Mermaid + ELK + jsdelivr ESM imports** 是 CDN 依赖：用户网络挡 jsdelivr 就坏了（公司内网、防火墙、离线环境）。这是个 trade-off 选择，不算 bug，但需要文档化。
6. **未测 OpenAI Codex 安装路径**（README 列了 Codex 手工 cp 的方法，本次没碰）。

## Recommended Next Actions

按优先级：

1. **修 install-pi.sh 的 mkdir bug**（最高，5 秒）：
   ```bash
   # 在 line 22 的 rm -rf "$SKILL_DIR" 之前加：
   mkdir -p "$(dirname "$SKILL_DIR")"
   ```
2. **同步 marketplace.json 的版本号到 0.6.3** + 加一个 CI assertion：`grep -q '"version": "0.6.3"' .claude-plugin/marketplace.json`
3. **在 README Install 部分加一行 vercel-deploy 依赖说明**：
   > Note: `/share` requires the `vercel-deploy` skill. Install it with `pi install npm:vercel-deploy`.
4. **跑一次 B 层端到端会话评测**：
   - 在 Claude Code 里跑 `/visual-explainer:generate-web-diagram`、`/diff-review`、`/plan-review`、`/generate-slides --slides`
   - 用 Playwright 截图产物 HTML
   - 对照 SKILL.md 的 anti-AI-slop list 打分
   - 用一个会触发 Proactive Table Rendering 的提示验证 auto-trigger
5. **Mermaid CDN 依赖文档化**：在 README "Limitations" 段加一句"Templates that use Mermaid require internet access to load mermaid@11 + elk from jsdelivr; offline use requires inlining the bundles"
6. **测一遍 Codex 安装路径**：README 列了步骤但没人验证过。
7. 修完 1-3 + 完成 4 后重跑 eval，目标晋级 `reusable`。

## Provenance

| Field | Value |
|-------|-------|
| runner | cc |
| agent | Claude Code |
| model | claude-opus-4-6 |
| repo_evals_commit | `21f90eb` |
| target_repo_path | `/tmp/visual-explainer` |
| target_repo_ref | `main` |
| target_repo_commit | `9a97a58` |
| evaluated_at | 2026-04-07T04:25:54Z |
