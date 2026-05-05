#!/usr/bin/env python3
"""One-shot migration applying three coordinated updates to evaluated repos:

  1. Convert flat-string ``workflow_diagram.why_layer`` into a bilingual
     ``{en, zh}`` dict so the dossier ZH toggle works.
  2. Add ``business_category`` (content / finance / development) field.
  3. Add ``product_view.how`` — one-paragraph synthesis of "how do you
     actually use this" — required for the new 4-card benefits layout.

Author-time only; not part of the eval runtime. After running this once,
the per-repo YAMLs hold all three additions and the renderer picks them
up automatically.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


# Per-repo content. Each entry holds:
#   business_category : "content" | "finance" | "development"
#   how               : { en, zh }                — one-paragraph "how to use it"
#   why_layer_zh      : str (only when current why_layer is a flat EN string)
#                       — the existing string becomes the .en, this is the .zh

UPDATES: dict[str, dict] = {
    "obra--superpowers": {
        "business_category": "development",
        "how": {
            "en": "Install the plugin into your agent platform (one command for Claude Code; per-platform configs for Codex / Cursor / Gemini / OpenCode / Factory Droid / GH Copilot). Then just give your agent a non-trivial coding task — superpowers' 14 skills auto-trigger at the right moment. You don't invoke skills by name; you describe what you want done and the agent picks the methodology.",
            "zh": "把插件装到 agent 平台(Claude Code 一行命令;Codex / Cursor / Gemini / OpenCode / Factory Droid / GH Copilot 用各自配置)。然后只管给 agent 一个不平凡的编程任务 —— superpowers 的 14 个 skill 会在合适时机自动触发。你不用按名字调 skill;你描述要做的事,agent 自己挑方法论。",
        },
    },
    "zarazhangrui--frontend-slides": {
        "business_category": "content",
        "how": {
            "en": "Install via Claude Code plugin marketplace. Tell your agent the topic and any constraints (e.g., \"Make me a 15-slide deck about X, Stripe-style\"). Phase 1 outlines the deck, Phase 2 generates the HTML, optional Phase 3 deploys to Vercel. You get back an HTML directory you can host, hand-edit, or re-prompt the agent to revise.",
            "zh": "Claude Code 插件市场安装。告诉 agent 主题和约束(比如 \"做一份 15 页的 X 主题 deck,Stripe 调性\")。Phase 1 列大纲,Phase 2 生成 HTML,可选 Phase 3 部署到 Vercel。出来一个 HTML 目录,可以托管 / 手改 / 再让 agent 改。",
        },
    },
    "NanmiCoder--MediaCrawler": {
        "business_category": "content",
        "how": {
            "en": "git clone, uv pip install. Run `python main.py --platform <name> --type <mode> --keyword/--note_id/--creator_id ...`. First run pops a QR code or asks for cookie to log in to the platform. Playwright opens a real browser, scrapes per your flags, writes results to `data/<platform>/<file>` in your chosen format (CSV / JSON / SQLite / Postgres / Mongo / etc.).",
            "zh": "git clone + uv pip install。`python main.py --platform <平台> --type <类型> --keyword/--note_id/--creator_id ...` 跑起来。第一次会弹二维码或问你 cookie 登录平台。Playwright 开真实浏览器按你的参数抓,把结果写到 `data/<平台>/<文件>`,格式按你挑(CSV / JSON / SQLite / Postgres / Mongo 等)。",
        },
    },
    "op7418--Humanizer-zh": {
        "business_category": "content",
        "how": {
            "en": "Install via `npx skills add op7418/Humanizer-zh` (or git clone into ~/.claude/skills/humanizer-zh). Then in Claude Code, paste your Chinese AI-suspect text and ask: \"帮我把这段去掉 AI 味\". The skill auto-fires, identifies which of 24 tells appear, rewrites them in-place, and returns a 50-point rubric score. One pass takes ~30 seconds.",
            "zh": "用 `npx skills add op7418/Humanizer-zh` 安装(或 git clone 到 ~/.claude/skills/humanizer-zh)。然后在 Claude Code 里贴上中文 AI 嫌疑文本,说:\"帮我把这段去掉 AI 味\"。skill 自动起,识别中了 24 痕迹里哪些,原地改写,给一份 50 分量化打分。一遍大约 30 秒。",
        },
        "why_layer_zh": "原子 —— 一个用户可调用的能力(改写中文 AI 嫌疑文本)。内部有 3 个隐式阶段(识别痕迹 → 改写 → 打分),但用户不编排 —— 一句话进,一份成品出。",
    },
    "geekjourneyx--md2wechat-skill": {
        "business_category": "content",
        "how": {
            "en": "Install via Homebrew / npm / install script (or `go build` from source). Run `md2wechat inspect article.md` first to see metadata + readiness issues. Fix any flagged problems in your markdown. Then `md2wechat convert article.md --theme dark --output draft.html` produces editor-ready HTML. Optional: `--upload-images --create-draft` pushes images to WeChat material library and creates a draft directly.",
            "zh": "Homebrew / npm / 安装脚本(或源码 `go build`)。先跑 `md2wechat inspect article.md` 看元数据 + 可修问题,在 markdown 里修。然后 `md2wechat convert article.md --theme dark --output draft.html` 出公众号编辑器可贴的 HTML。可选 `--upload-images --create-draft` 把图片传到素材库 + 直接创建草稿。",
        },
        "why_layer_zh": "原子 —— 一个用户可调用的能力(markdown → 微信 HTML)。内部阶段(parse → inspect → convert → 可选上传 → 可选草稿)用户不编排;你说\"convert\",工具跑完整流水线,你拿到 HTML。可选 LLM 模式(humanize / 从想法直接写)依然是原子形态 —— 一个输入,一份成品。",
    },
    "remotion-dev--skills": {
        "business_category": "content",
        "how": {
            "en": "Install means: clone the Remotion monorepo, copy `skills/remotion/SKILL.md` + `rules/` into your AI agent's skills directory (`~/.claude/skills/`, `~/.cursor/skills/`, etc.). The skill is `private: true` on npm — you cannot `npm install`. Once installed, your agent recognises Remotion tasks and auto-loads the relevant rule(s) from rules/ — captions, audio, ffmpeg, lottie, fonts, etc.",
            "zh": "安装方式: clone Remotion monorepo,把 `skills/remotion/SKILL.md` + `rules/` 复制到 AI agent 的 skills 目录(`~/.claude/skills/`、`~/.cursor/skills/` 等)。包是 `private: true`,不能 `npm install`。装好后 agent 识别到 Remotion 任务,自动加载 rules/ 里相关的子规则(captions / audio / ffmpeg / lottie / fonts 等)。",
        },
        "why_layer_zh": "原子 —— 一个用户可调用的能力,agent 在涉及 Remotion 任务时触发。内部 skill 从 rules/ 里加载对应子规则,但用户不编排 —— 你写一个 Remotion 任务,skill 挑相关规则。",
    },
    "anthropics--skill-creator": {
        "business_category": "development",
        "how": {
            "en": "Clone anthropics/skills repo, copy the `skills/skill-creator/` subdirectory into your `~/.claude/skills/`. Then in Claude Code: \"Use skill-creator to design a new skill for X\" or \"Run blind-compare on my skill v1 vs v2 against this benchmark\". The harness drafts SKILL.md, runs analyzer / grader / comparator sub-agents, generates an HTML eval-viewer report. Iterative loop: each round multiplies LLM calls — set a token budget.",
            "zh": "Clone anthropics/skills 仓库,把 `skills/skill-creator/` 子目录拷到 `~/.claude/skills/`。然后在 Claude Code 里说:\"用 skill-creator 设计一个 X skill\" 或者 \"在这个 benchmark 上对比我 skill 的 v1 vs v2\"。流水线起草 SKILL.md,跑 analyzer / grader / comparator 子 agent,出 HTML eval-viewer 报告。迭代循环每轮翻倍 LLM 调用 —— 设 token 预算。",
        },
        "why_layer_zh": "分子 —— skill 写作原子的固定流水线(分析 → 起草 → 跑评测 → 比版本 → 迭代)。用户选入口模式(新 skill / 优化 / benchmark),但模式内部流水线是确定性的。子 agent(analyzer / comparator / grader) 是被流水线编排的原子;LLM 不决定下一步触发哪个子 agent —— 脚本决定。",
    },
    "router-for-me--CLIProxyAPI": {
        "business_category": "development",
        "how": {
            "en": "Download the binary for your OS/arch (8 builds available), or `go install` from source. Configure your CLI sessions (Claude Code / Codex / Gemini CLI / Antigravity OAuth) and accounts in the YAML config. Run the binary; it listens on `localhost:8317` (or your chosen port). Point your other tools' `OPENAI_BASE_URL` at that address — they think they're talking to OpenAI; cliproxy translates protocols and forwards via your CLI auth.",
            "zh": "下载对应 OS/arch 的二进制(8 个版本可选),或源码 `go install`。在 YAML 配置里配置 CLI session(Claude Code / Codex / Gemini CLI / Antigravity OAuth) 和账号。跑起来,默认监听 `localhost:8317`。把其他工具的 `OPENAI_BASE_URL` 指过去 —— 它们以为自己在跟 OpenAI 说话,cliproxy 翻译协议然后用你的 CLI 鉴权转发。",
        },
        "why_layer_zh": "分子 —— 固定流水线(收 HTTP 请求 → 协议翻译 → CLI session 转发 → 响应翻译 → HTTP 返回)。用户配置 provider + 账号;流水线内部不让 LLM 决定路由 —— 代理严格按配置走。Round-robin / 故障切换是确定性规则,不是 LLM 决定。",
    },
    "iamzhihuix--skills-manage": {
        "business_category": "development",
        "how": {
            "en": "Download the Tauri DMG / installer (one-time `xattr` workaround on macOS for unsigned v0.9.1 build). Open the GUI, register a skill (or import a bundle). Pick which of the 28 supported tools (Claude Code / Cursor / Codex / Gemini CLI / Trae / ...) should see this skill — the app symlinks `~/.agents/skills/<name>/` into each tool's expected directory. Edit the source once, every selected tool sees the change immediately.",
            "zh": "下 Tauri DMG / 安装包(macOS 上 v0.9.1 未签名,首次启动跑一次 `xattr`)。开 GUI,注册 skill(或导入合集)。选 28 家支持的工具里哪些应该看到这个 skill(Claude Code / Cursor / Codex / Gemini CLI / Trae / ...) —— app 把 `~/.agents/skills/<name>/` 软链到每家工具的期待目录。改一次源,所有选中的工具立刻看到。",
        },
        "why_layer_zh": "分子 —— 固定流水线(skill 注册 → 中心存储 → 软链到每家启用的工具 → 工具读取)。用户选启用哪些工具,但注册之后步骤固定且确定性。运行时无 LLM 决策。",
    },
    "HughYau--qiushi-skill": {
        "business_category": "development",
        "how": {
            "en": "Install with `npx qiushi-skill install <platform>` for one of 7 supported agent platforms (Claude Code / Codex / Cursor / Hermes / NanoBot / OpenClaw / OpenCode). Pick 2-3 skills matching your real workflow (don't install all 10). Then invoke explicitly: \"用调查研究 skill 分析这个问题\" or \"用矛盾分析法找主要矛盾\". Each invocation forces the agent to follow that methodology's framework.",
            "zh": "用 `npx qiushi-skill install <平台>` 装到 7 家支持的 agent 平台之一(Claude Code / Codex / Cursor / Hermes / NanoBot / OpenClaw / OpenCode)。挑 2-3 条匹配你工作流的(不要 10 条都装)。然后明确调用:\"用调查研究 skill 分析这个问题\" 或 \"用矛盾分析法找主要矛盾\"。每次调用让 agent 按那条方法论的框架走。",
        },
        "why_layer_zh": "分子 —— 用户在某个时刻挑要触发哪条方法论 skill,但每次调用内部按固定结构走(定问题 → 调研 → 分析 → 结论)。方法论本身由调用了哪条 skill 决定,不是 LLM 运行时决定。多个用户可调用的原子,无复合物决策。",
    },
    "Usagi-org--ai-goofish-monitor": {
        "business_category": "content",
        "how": {
            "en": "Run `docker compose up -d`. Open the Vue dashboard at `localhost:8000` (change `WEB_PASSWORD` from default `admin123`). Use the companion Chrome extension to export your XianYu cookie, paste it into the dashboard. Add tasks in natural language (\"Sony A7R III, less than 5000 shutter actuations, under ¥8000\"). The scheduler runs Playwright + multi-modal LLM filtering; matches push to ntfy / Bark / WeChat Work / Telegram / Gotify / Webhook.",
            "zh": "`docker compose up -d`。打开 `localhost:8000` 的 Vue dashboard(改默认密码 `admin123`)。用配套 Chrome 扩展导出你的闲鱼 cookie 贴到 dashboard。自然语言加任务(\"Sony A7R III,快门 5000 以下,8000 以内\")。调度器跑 Playwright + 多模态 LLM 过滤,命中推到 ntfy / Bark / 企微 / Telegram / Gotify / Webhook。",
        },
        "why_layer_zh": "分子 —— 固定流水线(条件 → 调度 → Playwright → LLM 过滤 → 推送)。LLM 在条件生成 + 商品分析阶段被调用,但运行时不路由 —— 每条挂牌走的流水线一样。用户加任务 + 写条件;引擎确定性地跑。",
    },
    "brokermr810--QuantDinger": {
        "business_category": "finance",
        "how": {
            "en": "`docker compose up -d --build` (or AWS Marketplace AMI for paid one-click). Configure broker keys (IBKR for US stocks, MT5 for forex on a Windows host, crypto exchange) + at least one LLM provider (OpenAI / DeepSeek / Grok). Open the React dashboard, connect your AI agent via MCP. Workflow: \"design indicator\" → AI writes Python code → \"run backtest on this strategy\" → AI evaluates → optional \"go live\" with manual-approval gate forced ON.",
            "zh": "`docker compose up -d --build`(或买 AWS Marketplace AMI 一键)。配 broker key(IBKR 美股 / MT5 外汇要 Windows / 加密所) + 至少一家 LLM(OpenAI / DeepSeek / Grok)。开 React dashboard,通过 MCP 接 AI agent。工作流:\"设计 indicator\" → AI 写 Python → \"跑这个策略回测\" → AI 评估 → 可选\"上实盘\"必须开人工审批闸门。",
        },
        "why_layer_zh": "复合物 —— 在 3 个菱形决策节点上,LLM(或通过 MCP 的 AI agent)运行时根据请求和数据决定走哪条路。(1)\"需要新 indicator?\" 分到 AI 代码生成 vs 现成库;(2)\"回测够好了 or 继续迭代?\" 分到上实盘准备 vs 调整;(3)\"实盘审批 —— 谁决定?\" 分到 AI 预审 vs 人工否决。分子是固定流水线;复合物是运行时 LLM 决定的分支。",
    },
    "THU-MAIC--OpenMAIC": {
        "business_category": "content",
        "how": {
            "en": "Either use the hosted demo at `open.maic.chat` (zero setup, you bring an LLM key) or one-click Vercel deploy your own / `docker compose up` self-host. Drop a topic or upload a paper / chapter. LangGraph multi-agent stack generates a 20-30 minute classroom: AI teacher walks the whiteboard, AI peer asks questions, slides + quizzes + interactive simulations get auto-generated, TTS streams real voice.",
            "zh": "用 `open.maic.chat` 托管 demo(零安装,自带 LLM key)或一键 Vercel 部署自己的版本 / `docker compose up` 自托管。贴主题或上传论文 / 章节。LangGraph 多 agent stack 生成 20-30 分钟课堂: AI 老师讲白板,AI 同学提问,幻灯片 + quiz + 互动模拟自动生成,TTS 流式真人声音。",
        },
        "why_layer_zh": "复合物 —— 在 3 个菱形决策节点上,LangGraph 编排器(运行时跑 LLM)根据主题 + 课堂当前状态决定下一个子 agent 触发哪个。(1)\"大纲策略?\" 分深度优先 vs 广度;(2)\"白板 or 模拟?\" 分到 whiteboard-agent vs simulation-agent(数学 vs 过程内容);(3)\"quiz or 继续讲?\" 按学生参与度信号分。分子是固定流水线;OpenMAIC 每堂课不一样。这是复合物。",
    },
    "zinan92--repo-evals": {
        "business_category": "development",
        "how": {
            "en": "Clone + `pip install pyyaml`. Run `scripts/new-repo-eval.sh owner/repo` to scaffold a directory under `repos/`. Hand-author 6-10 claims in `claims/claim-map.yaml`, fill `repo.yaml` (product_view + workflow_diagram + similar_repos). Run `scripts/render_verdict_html.py owner--repo` for the bilingual dossier. Run `scripts/build_master_dashboard.py` to refresh the corpus index.",
            "zh": "Clone + `pip install pyyaml`。`scripts/new-repo-eval.sh owner/repo` 在 `repos/` 下生成目录。手写 6-10 条 claim 到 `claims/claim-map.yaml`,填 `repo.yaml`(product_view + workflow_diagram + similar_repos)。`scripts/render_verdict_html.py owner--repo` 出双语 dossier。`scripts/build_master_dashboard.py` 刷新总目录。",
        },
    },
}


def apply_updates() -> None:
    """Walk every (slug, updates) pair, mutate repo.yaml in place."""

    for slug, upd in UPDATES.items():
        repo_path = ROOT / "repos" / slug / "repo.yaml"
        if not repo_path.exists():
            print(f"  SKIP {slug} — no repo.yaml", file=sys.stderr)
            continue
        data = yaml.safe_load(repo_path.read_text()) or {}

        if "business_category" in upd:
            data["business_category"] = upd["business_category"]

        pv = data.get("product_view") or {}
        if "how" in upd and pv:
            pv["how"] = upd["how"]
            data["product_view"] = pv

        wd = data.get("workflow_diagram") or {}
        if "why_layer_zh" in upd and wd:
            current = wd.get("why_layer")
            if isinstance(current, str):
                wd["why_layer"] = {
                    "en": current.strip(),
                    "zh": upd["why_layer_zh"].strip(),
                }
                data["workflow_diagram"] = wd

        repo_path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=2000)
        )
        print(f"  UPDATED {slug}")


if __name__ == "__main__":
    apply_updates()
