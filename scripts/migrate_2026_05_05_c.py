#!/usr/bin/env python3
"""Backfill ``product_view.next_step`` for all 14 repos that have
the new benefits-driven schema. The text was distilled from each
repo's verdict.md "Path to higher score" section; we just promote
it into the dossier as a first-screen callout.

Each entry is one concrete action the maintainer or evaluator
could take this week to push the repo's score up to the next tier.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


# Per-repo concrete next-action sentence (en + zh).
NEXT_STEP: dict[str, dict] = {
    "obra--superpowers": {
        "en": "Run one logged Claude Code session: ask the agent for a real feature, watch the methodology fire (brainstorming → writing-plans → TDD → subagent-driven-development → verification-before-completion). Save the transcript. Updates claim-007 from untested to passed; moves the score toward 80+.",
        "zh": "跑一次有日志记录的 Claude Code session: 让 agent 做一个真实功能,观察方法论是否触发(brainstorming → 写计划 → TDD → 子 agent 拆活 → 完成前自检)。保存 transcript。把 claim-007 从未验证转为通过;分数向 80+ 推进。",
    },
    "zarazhangrui--frontend-slides": {
        "en": "Run a logged Claude Code session generating one real deck end-to-end: pick a topic, watch Phase 1 (outline) → Phase 2 (HTML) → Phase 3 (Vercel deploy). Save the resulting HTML directory + the deploy URL. Validates Phase 1-3 quality + the optional deploy path.",
        "zh": "跑一次有日志的 Claude Code session,完整生成一份真实 deck: 选主题,看 Phase 1(大纲) → Phase 2(HTML) → Phase 3(Vercel 部署)。保存 HTML 目录 + 部署链接。验证 Phase 1-3 质量 + 可选的部署路径。",
    },
    "NanmiCoder--MediaCrawler": {
        "en": "Pick one of the 7 platforms (Xiaohongshu is easiest), log in with a real account, run a logged 100-listing scrape, save the resulting CSV. Then a second platform a week later. Validates the per-platform crawler works against today's anti-bot. Without this, score stays around 75.",
        "zh": "挑 7 个平台中的一个(小红书最容易),用真实账号登,跑一次 100 条挂牌的有日志抓取,存下 CSV。一周后换第二个平台再跑一次。验证当前反爬环境下各平台爬虫能跑通。没这个分数停在 75 左右。",
    },
    "op7418--Humanizer-zh": {
        "en": "Run on a real 1500-char AI-suspect Chinese article in a logged Claude Code session. Save before/after rubric scores + the rewritten output. Validates the 24-tell rewrite + 50-point rubric work end-to-end. Updates claim-005 to passed.",
        "zh": "在一篇真实的 1500 字中文 AI 嫌疑文本上跑一次 Claude Code session 留日志。保存改前/改后的量表分 + 改后版本。验证 24 痕迹改写 + 50 分量表能端到端工作。把 claim-005 转为通过。",
    },
    "geekjourneyx--md2wechat-skill": {
        "en": "Already at 91 / Production-ready. Two paths to 95+: (1) Get a second evaluator to run the install + convert flow on their own machine, log the session — confirms reproducibility. (2) Run the LLM modes (humanize / write-from-idea) on a real article + log the output quality.",
        "zh": "已在 91 / 可用于生产。两条路升到 95+: (1) 找第二位评测者在自己机器上跑一遍 install + convert 流程留日志 —— 验证可复现。(2) 在真实文章上跑 LLM 模式(humanize / 从想法直接写) + 记录输出质量。",
    },
    "remotion-dev--skills": {
        "en": "Clone the Remotion monorepo, copy SKILL.md + rules/ into your Claude Code skills dir, ask the agent for a Remotion captions task. Verify it loads rules/captions.md and renders working code first try. Validates claim-005 (end-to-end). Then publish a thinner public-friendly install path.",
        "zh": "Clone Remotion monorepo,把 SKILL.md + rules/ 拷到 Claude Code skills 目录,让 agent 做一个 Remotion 字幕任务。验证它是否加载 rules/captions.md 并第一次 render 出可用代码。验证 claim-005(端到端)。然后发一个更对外友好的安装路径。",
    },
    "anthropics--skill-creator": {
        "en": "Run the full skill-authoring loop in Claude Code: design a new skill from scratch, run analyzer / grader / comparator on it against a 20-prompt benchmark, save the eval-viewer HTML report. Validates the live A/B + the iterative-improvement loop end-to-end. Pushes 81 → 85+.",
        "zh": "在 Claude Code 里跑一次完整的 skill 写作循环: 从零设计一个新 skill,跑 analyzer / grader / comparator 在 20 条 prompt 的 benchmark 上对比,保存 eval-viewer HTML 报告。验证活的 A/B + 迭代改进循环能端到端跑。把 81 推到 85+。",
    },
    "router-for-me--CLIProxyAPI": {
        "en": "Run with 2+ provider OAuth sessions configured. Send 100 OpenAI-compatible requests, verify round-robin works + the token-refresh fires when one session expires. Save the proxy logs. Validates the multi-account behavior + token lifecycle.",
        "zh": "配置 2 家以上 provider OAuth session 后跑起来。发 100 个 OpenAI 兼容请求,验证 round-robin 工作 + 一家 session 过期时 token 刷新触发。保存代理日志。验证多账号行为 + token 生命周期。",
    },
    "iamzhihuix--skills-manage": {
        "en": "On a clean macOS install (or VM), download the v0.9.1 DMG, run the xattr workaround, register a skill, sync to Claude Code + Cursor + Codex. Verify symlinks point correctly + the same source SKILL.md edit appears in all three. Validates the central-storage + symlink design end-to-end.",
        "zh": "在一台干净 macOS(或虚拟机)上,下 v0.9.1 DMG,跑 xattr 解锁,注册一个 skill,同步到 Claude Code + Cursor + Codex。验证软链指对位置 + 改一份源 SKILL.md 三家工具都看到。验证中心存储 + 软链架构端到端。",
    },
    "HughYau--qiushi-skill": {
        "en": "Install the contradiction-analysis skill in Claude Code. Give the agent a complex business decision (\"should we expand to a new market\"), explicitly invoke the skill. Save transcript. Verify the agent uses the methodology framework (identify principal contradiction → compare against secondary) instead of giving a flat answer.",
        "zh": "在 Claude Code 里装 contradiction-analysis skill。给 agent 一个复杂商业决策(\"该不该拓展新市场\"),明确调用 skill。保存 transcript。验证 agent 是否用方法论框架(找主要矛盾 → 对比次要)而不是给平铺答案。",
    },
    "Usagi-org--ai-goofish-monitor": {
        "en": "Run docker compose up on your own host, configure with a real XianYu cookie + one realistic criterion (e.g., Sony A7R III < ¥8000). Watch a 24h cycle. Verify true matches push correctly to your phone + false positives < 5% after a day of LLM-rule tuning. Validates the multi-modal LLM filter quality.",
        "zh": "在自己机器上 docker compose up,配真实闲鱼 cookie + 一个真实条件(比如 Sony A7R III < 8000)。看一个 24 小时周期。验证真命中正确推到手机 + 一天 LLM 规则调优后误报 < 5%。验证多模态 LLM 过滤质量。",
    },
    "brokermr810--QuantDinger": {
        "en": "Run a backtest on a known-good strategy (RSI dip + MA20 cross on SPY 2020-2025). Verify Sharpe / drawdown match a hand-calculated baseline within ±5%. Then a paper-account live test on IBKR for 2 weeks with manual-approval gate ON. Validates backtest + execution layer + the safety gate.",
        "zh": "在一个已知策略上跑回测(SPY 2020-2025 上的 RSI 回调 + MA20 上穿)。验证 Sharpe / 回撤跟手算基线差距 ±5% 以内。然后在 IBKR 的 paper 账号上跑 2 周实盘,人工审批闸门必须开。验证回测 + 执行层 + 安全闸门。",
    },
    "THU-MAIC--OpenMAIC": {
        "en": "Use open.maic.chat hosted demo on a real paper (one you actually need to understand). Verify LangGraph multi-agent dispatch reaches a useful 20-min classroom — outline-agent picks a sensible structure, whiteboard / simulation choice matches the topic, quizzes are at right checkpoints, TTS streams without breaking. Then a self-host run.",
        "zh": "用 open.maic.chat 托管 demo 跑一篇真实论文(你真心要搞懂的那种)。验证 LangGraph 多 agent 调度能给到一节有用的 20 分钟课堂 —— outline-agent 排合理结构,白板 / 模拟选择跟主题对得上,quiz 在合适检查点,TTS 流式不断流。然后再跑一次自托管。",
    },
    "zinan92--repo-evals": {
        "en": "Log a fresh-clone-to-rendered-dossier session for a never-seen repo. Stopwatch the steps; save the resulting dossier. Updates claim-010 (live e2e) from untested to passed. With LICENSE + README already fixed, this single live run pushes 78 → 80+.",
        "zh": "给一个从没见过的 repo 跑一次从 clone 到 dossier 出炉的有日志 session。计时每步;保存最终 dossier。把 claim-010(端到端)从未验证转为通过。LICENSE + README 已经修了,加上这一次实际运行,把 78 推过 80。",
    },
}


def apply_updates() -> None:
    for slug, ns in NEXT_STEP.items():
        repo_path = ROOT / "repos" / slug / "repo.yaml"
        if not repo_path.exists():
            print(f"  SKIP {slug} — no repo.yaml", file=sys.stderr)
            continue
        data = yaml.safe_load(repo_path.read_text()) or {}
        pv = data.get("product_view") or {}
        if not pv:
            print(f"  SKIP {slug} — no product_view", file=sys.stderr)
            continue
        pv["next_step"] = ns
        data["product_view"] = pv
        repo_path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=2000)
        )
        print(f"  UPDATED {slug}")


if __name__ == "__main__":
    apply_updates()
