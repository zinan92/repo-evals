#!/usr/bin/env python3
"""Apply ``workflow_placements`` to the 16 repos that fit the Park content
workflow (park-content-v1). Each placement carries a stage_id, role, and
a short bilingual reason.

Schema (added to repo.yaml at the top level):

    workflow_placements:
      - workflow_id: park-content-v1
        stage_id: "06_assembly"
        role: primary       # primary | support | alternative | reference
        medium: video       # optional — for stages that span media types
        reason:
          en: "..."
          zh: "..."

A repo can have multiple placements (multi-stage span like QuantDinger,
or multi-workflow like a tool useful in both content and dev).
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


# Per-repo placements. Drawn from workflows/PLACEMENT-DRAFT.md.
PLACEMENTS: dict[str, list[dict]] = {

    # === 02 acquisition ===
    "NanmiCoder--MediaCrawler": [{
        "workflow_id": "park-content-v1",
        "stage_id": "02_acquisition",
        "role": "primary",
        "reason": {
            "en": "Multi-platform CN crawler — 7 platforms × 4 crawl modes × 8 storage backends. When you need raw content from any of those platforms, this is the reference implementation.",
            "zh": "多平台中国爬虫 —— 7 个平台 × 4 种抓取模式 × 8 种存储后端。任何一个平台想要原始内容,这是参考实现。",
        },
    }],
    "zinan92--content-downloader": [{
        "workflow_id": "park-content-v1",
        "stage_id": "02_acquisition",
        "role": "alternative",
        "reason": {
            "en": "Lighter single-purpose downloader. Currently broken on Douyin signing — use only when MediaCrawler is overkill for your one platform AND that platform isn't Douyin.",
            "zh": "更轻量的单目的下载器。抖音签名当前坏了 —— 只在 MediaCrawler 对你那一个平台太重 + 那个平台不是抖音时用。",
        },
    }],
    # Removed (2026-05-06): ai-goofish-monitor not actually content workflow
    # (it's marketplace listings monitoring). Per Wendy's review.

    # === 03 understanding ===
    "zarazhangrui--youtube-to-ebook": [{
        "workflow_id": "park-content-v1",
        "stage_id": "03_understanding",
        "role": "primary",
        "medium": "video-to-text",
        "reason": {
            "en": "Video → text comprehension specifically. Use when source material is a YouTube video and you need it in queryable text form.",
            "zh": "专做视频 → 文字理解。源素材是 YouTube 视频、要变成可查询文本时用。",
        },
    }],
    "zinan92--content-extractor": [{
        "workflow_id": "park-content-v1",
        "stage_id": "03_understanding",
        "role": "primary",
        "reason": {
            "en": "Author's own content-extraction tool — pulls structure, transcript, quotes, fact-claims from acquired raw assets.",
            "zh": "作者自己的内容提取工具 —— 从抓回来的原始素材里拎出结构 / 转录 / 金句 / 事实 claim。",
        },
    }],

    # === 05 production ===
    "op7418--Humanizer-zh": [{
        "workflow_id": "park-content-v1",
        "stage_id": "05_production",
        "role": "primary",
        "reason": {
            "en": "Chinese AI 味 cleanup + 50-point rubric. The de-AI step every CN draft needs before publish.",
            "zh": "中文去 AI 味 + 50 分量化打分。每份中文草稿发布前的去 AI 步骤。",
        },
    }],
    "zinan92--content-toolkit": [{
        "workflow_id": "park-content-v1",
        "stage_id": "05_production",
        "role": "support",
        "reason": {
            "en": "Author's content-rewriter logic. Supplements Humanizer-zh on the production layer.",
            "zh": "作者自己的内容改写工具。在生产层补 Humanizer-zh。",
        },
    }],
    "oaker-io--wewrite": [{
        "workflow_id": "park-content-v1",
        "stage_id": "05_production",
        "role": "alternative",
        "reason": {
            "en": "Broader WeChat-content workflow tool. Use when production and publish are tightly coupled to one channel.",
            "zh": "更宽的公众号内容工作流工具。生产 + 发布紧密绑定一个渠道时用。",
        },
    }],

    # === 06 assembly ===
    "zarazhangrui--frontend-slides": [{
        "workflow_id": "park-content-v1",
        "stage_id": "06_assembly",
        "role": "primary",
        "medium": "presentation",
        "reason": {
            "en": "HTML deck assembly. Medium: presentation slides — browser-native, hostable, hand-editable HTML.",
            "zh": "HTML 演示稿组装。媒介: 幻灯片 —— 浏览器原生、可托管、可手改的 HTML。",
        },
    }],
    "remotion-dev--skills": [{
        "workflow_id": "park-content-v1",
        "stage_id": "06_assembly",
        "role": "primary",
        "medium": "video",
        "reason": {
            "en": "Programmatic video assembly via the Remotion best-practices skill. Medium: video — captions, audio sync, lottie, ffmpeg.",
            "zh": "通过 Remotion best-practices skill 做程序化视频组装。媒介: 视频 —— 字幕 / 音频同步 / lottie / ffmpeg。",
        },
    }],
    # Removed (2026-05-06): personalized-podcast / codebase-to-course / OpenMAIC
    # are educational/long-form output, not Wendy's social-media content
    # workflow (X / 抖音 / 小红书 / WeChat). Per Wendy's review.

    # === 07 distribution ===
    "dreammis--social-auto-upload": [{
        "workflow_id": "park-content-v1",
        "stage_id": "07_distribution",
        "role": "primary",
        "reason": {
            "en": "Multi-platform auto-upload to 7 CN + international platforms (douyin / bilibili / xhs / kuaishou / 视频号 / 百家号 / TikTok) from one CLI. Despite ⚠️ Risky tier, it's the broadest distribution layer in the corpus.",
            "zh": "一个 CLI 自动上传到 7 个中外平台(抖音 / B 站 / 小红书 / 快手 / 视频号 / 百家号 / TikTok)。虽然在 ⚠️ Risky 档,但它是 corpus 里覆盖最广的分发层。",
        },
    }],
    "geekjourneyx--md2wechat-skill": [{
        "workflow_id": "park-content-v1",
        "stage_id": "07_distribution",
        "role": "primary",
        "medium": "wechat",
        "reason": {
            "en": "WeChat-specific channel adapter — markdown → WeChat editor-ready HTML, optionally pushes draft to WeChat material library. Best-in-class for WeChat publish.",
            "zh": "公众号专用渠道适配器 —— markdown → 公众号可贴 HTML,可选推送到素材库。WeChat 发布层的最优解。",
        },
    }],
    "autoclaw-cc--xiaohongshu-skills": [{
        "workflow_id": "park-content-v1",
        "stage_id": "07_distribution",
        "role": "support",
        "medium": "xiaohongshu",
        "reason": {
            "en": "Xiaohongshu single-platform helper. Use when the workflow targets only Xiaohongshu and you don't need the multi-platform overhead of social-auto-upload.",
            "zh": "小红书单平台助手。当工作流只发小红书 + 不想要 social-auto-upload 多平台开销时用。",
        },
    }],
}


def apply_updates() -> None:
    for slug, placements in PLACEMENTS.items():
        repo_path = ROOT / "repos" / slug / "repo.yaml"
        if not repo_path.exists():
            print(f"  SKIP {slug} — no repo.yaml", file=sys.stderr)
            continue
        data = yaml.safe_load(repo_path.read_text()) or {}
        existing = data.get("workflow_placements") or []
        # Merge: keep any non-Park placements + replace Park ones
        non_park = [p for p in existing if not str(p.get("workflow_id", "")).startswith("park-")]
        data["workflow_placements"] = non_park + placements
        repo_path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=2000)
        )
        print(f"  UPDATED {slug}  → {len(placements)} placement(s)")


if __name__ == "__main__":
    apply_updates()
