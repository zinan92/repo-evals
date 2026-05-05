#!/usr/bin/env python3
"""Apply workflow_placements for park-trading-v1 + park-development-v1.

Mirrors migrate_2026_05_06_workflows.py (which did park-content-v1).
Same merge semantics: keep any non-Park placements + replace Park-*
placements wholesale.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


PLACEMENTS: dict[str, list[dict]] = {

    # ====== TRADING (park-trading-v1) ======
    "brokermr810--QuantDinger": [
        {
            "workflow_id": "park-trading-v1",
            "stage_id": "05_backtest",
            "role": "primary",
            "reason": {
                "en": "Backtest engine + variance analysis. Strong 05 anchor in the corpus.",
                "zh": "回测引擎 + 方差分析。corpus 里 05 阶段的强锚点。",
            },
        },
        {
            "workflow_id": "park-trading-v1",
            "stage_id": "06_risk",
            "role": "primary",
            "reason": {
                "en": "Manual-approval gate + position sizing + max-loss cap rules baked in.",
                "zh": "人工审批闸门 + 仓位规模 + 最大损失上限规则内置。",
            },
        },
        {
            "workflow_id": "park-trading-v1",
            "stage_id": "07_execution",
            "role": "primary",
            "reason": {
                "en": "IBKR + MT5 + crypto-exchange execution under one stack with the safety gate.",
                "zh": "IBKR + MT5 + 加密所执行,一套 stack,带安全闸门。",
            },
        },
    ],

    "tukuaiai--tradecat": [
        {
            "workflow_id": "park-trading-v1",
            "stage_id": "04_methodology_routing",
            "role": "primary",
            "reason": {
                "en": "Trading methodology + strategy library — match a signal to a strategy.",
                "zh": "交易方法论 + 策略库 —— 把信号匹配到策略。",
            },
        },
        {
            "workflow_id": "park-trading-v1",
            "stage_id": "07_execution",
            "role": "alternative",
            "reason": {
                "en": "Lighter-weight execution alternative to QuantDinger's full stack.",
                "zh": "比 QuantDinger 全栈更轻量的执行替代。",
            },
        },
    ],

    "RKiding--Awesome-finance-skills": [
        {
            "workflow_id": "park-trading-v1",
            "stage_id": "02_intel",
            "role": "support",
            "reason": {
                "en": "Curated finance methodology skills — useful for intel-collection guidance.",
                "zh": "精选金融方法论 skills —— 给情报采集做指引。",
            },
        },
        {
            "workflow_id": "park-trading-v1",
            "stage_id": "04_methodology_routing",
            "role": "support",
            "reason": {
                "en": "Strategy / methodology skills your AI agent can reach for at routing time.",
                "zh": "AI agent 在策略路由时可以触发的策略 / 方法论 skill。",
            },
        },
    ],

    # ====== DEVELOPMENT (park-development-v1) ======
    "karpathy--autoresearch": [{
        "workflow_id": "park-development-v1",
        "stage_id": "01_research",
        "role": "reference",
        "reason": {
            "en": "Research-loop reference — LLM-training research, not general code research, but the autonomous-research pattern is the canonical example.",
            "zh": "研究循环参考 —— LLM 训练研究,不是通用代码研究,但自主研究模式是规范例子。",
        },
    }],

    "zinan92--repo-evals": [{
        "workflow_id": "park-development-v1",
        "stage_id": "01_research",
        "role": "primary",
        "reason": {
            "en": "\"Decide what to install\" research — the dev-research bottleneck most often hits, and this addresses it directly.",
            "zh": "\"该装什么\"研究 —— 开发研究最常碰到的瓶颈,这个直接对症。",
        },
    }],

    "zarazhangrui--frontend-slides": [{
        "workflow_id": "park-development-v1",
        "stage_id": "02_plan_design",
        "role": "support",
        "reason": {
            "en": "UI / pitch-deck design — for the design-deliverable side of plan/design.",
            "zh": "UI / pitch deck 设计 —— 计划与设计阶段的设计交付侧。",
        },
    }],

    "HughYau--qiushi-skill": [{
        "workflow_id": "park-development-v1",
        "stage_id": "02_plan_design",
        "role": "primary",
        "reason": {
            "en": "Reasoning-discipline skills (investigation-first / contradiction-analysis / protracted-strategy) keep the agent from rushing to design before research closes.",
            "zh": "推理纪律 skills(调研优先 / 矛盾分析 / 持久战) 让 agent 别在研究还没收尾前就跳到设计。",
        },
    }],

    "zinan92--doc-driven-dev-workflow": [
        {
            "workflow_id": "park-development-v1",
            "stage_id": "02_plan_design",
            "role": "primary",
            "reason": {
                "en": "The whole 22-stage doc-driven workflow lives in this stage — PRD / plan / approval gates are the design phase.",
                "zh": "完整 22-stage 文档驱动工作流在这一阶段 —— PRD / 计划 / 审批门是设计阶段。",
            },
        },
        {
            "workflow_id": "park-development-v1",
            "stage_id": "03_code_review",
            "role": "support",
            "reason": {
                "en": "workflow_guard + state machine cover the development-phase enforcement (TDD-batch + review).",
                "zh": "workflow_guard + 状态机覆盖开发阶段执行(TDD-batch + review)。",
            },
        },
    ],

    "obra--superpowers": [{
        "workflow_id": "park-development-v1",
        "stage_id": "03_code_review",
        "role": "primary",
        "reason": {
            "en": "TDD / brainstorming / subagent-driven-development / verification-before-completion — the canonical methodology bundle for the code-and-review phase.",
            "zh": "TDD / brainstorming / 子 agent 拆活 / 完成前自检 —— 编码与评审阶段的规范方法论合集。",
        },
    }],

    "gooseworks-ai--goose-skills": [{
        "workflow_id": "park-development-v1",
        "stage_id": "03_code_review",
        "role": "alternative",
        "reason": {
            "en": "Goose-runtime methodology skills — alternative when the agent harness is Goose rather than Claude Code.",
            "zh": "Goose 运行时的方法论 skills —— 当 agent 平台是 Goose 而非 Claude Code 时的替代。",
        },
    }],

    "anthropics--skill-creator": [{
        "workflow_id": "park-development-v1",
        "stage_id": "04_package",
        "role": "primary",
        "reason": {
            "en": "Skill authoring + eval harness — the meta-tool for shipping a skill cleanly. Production-ready (81 / 🏭) in our corpus.",
            "zh": "Skill 写作 + 评测流水线 —— 把 skill 干净地发出来的元工具。corpus 里 production-ready (81 / 🏭)。",
        },
    }],

    "iamzhihuix--skills-manage": [{
        "workflow_id": "park-development-v1",
        "stage_id": "04_package",
        "role": "primary",
        "reason": {
            "en": "Distribute the packaged skill across 28 AI coding tools — symlink-driven. Solves the \"5 copies of one skill\" problem.",
            "zh": "把打包好的 skill 分发到 28 家 AI 编程工具 —— 软链驱动。解决\"一个 skill 在 5 个目录\"问题。",
        },
    }],

    "router-for-me--CLIProxyAPI": [
        {
            "workflow_id": "park-development-v1",
            "stage_id": "04_package",
            "role": "support",
            "reason": {
                "en": "Deployment plumbing for AI tools — wraps existing CLI subscriptions as OpenAI-compatible endpoints for self-hosted dev infra.",
                "zh": "AI 工具的部署管道 —— 把已有 CLI 订阅包装成 OpenAI 兼容端点,给自托管 dev 基础设施用。",
            },
        },
        {
            "workflow_id": "park-development-v1",
            "stage_id": "05_maintain",
            "role": "support",
            "reason": {
                "en": "Runtime AI-routing layer — keeps the agent dependencies running without per-tool API rewires.",
                "zh": "运行时 AI 路由层 —— 让 agent 依赖跑起来,不用各家工具 API 重接线。",
            },
        },
    ],

    "nicobailon--visual-explainer": [{
        "workflow_id": "park-development-v1",
        "stage_id": "02_plan_design",
        "role": "support",
        "reason": {
            "en": "HTML / slide-deck visualisation for diff reviews + plan audits — bridges design <-> review handoff.",
            "zh": "做 diff review + plan audit 的 HTML / 幻灯片可视化 —— 设计 <-> 评审交接桥。",
        },
    }],
}


def apply_updates() -> None:
    for slug, placements in PLACEMENTS.items():
        repo_path = ROOT / "repos" / slug / "repo.yaml"
        if not repo_path.exists():
            print(f"  SKIP {slug}", file=sys.stderr)
            continue
        data = yaml.safe_load(repo_path.read_text()) or {}
        existing = data.get("workflow_placements") or []
        # Keep park-content-v1 and any non-Park placements; replace Park-trading + Park-development
        keep = [
            p for p in existing
            if not str(p.get("workflow_id", "")).startswith(("park-trading", "park-development"))
        ]
        data["workflow_placements"] = keep + placements
        repo_path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=2000)
        )
        print(f"  UPDATED {slug} → {len(placements)} new placements (kept {len(keep)})")


if __name__ == "__main__":
    apply_updates()
