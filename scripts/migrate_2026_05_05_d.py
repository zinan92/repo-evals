#!/usr/bin/env python3
"""Backfill ``use_case_tags`` for the 14 repos with the new schema.

Tags drawn from the controlled vocabulary in
scripts/render_verdict_html.py::USE_CASE_TAGS. 1-3 tags per repo.

Each tag answers "I want to <task>" — task-driven discovery on top of
the existing layer (atom/molecule/compound) and business_category
(content/finance/development) dimensions.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


TAGS: dict[str, list[str]] = {
    "obra--superpowers":            ["agent-methodology", "coding-workflow"],
    "zarazhangrui--frontend-slides":["presentation-content"],
    "NanmiCoder--MediaCrawler":     ["content-scraping"],
    "op7418--Humanizer-zh":         ["content-rewriting"],
    "geekjourneyx--md2wechat-skill":["content-publishing"],
    "remotion-dev--skills":         ["video-generation"],
    "anthropics--skill-creator":    ["skill-authoring"],
    "router-for-me--CLIProxyAPI":   ["llm-routing"],
    "iamzhihuix--skills-manage":    ["skill-distribution"],
    "HughYau--qiushi-skill":        ["agent-methodology", "reasoning-discipline"],
    "Usagi-org--ai-goofish-monitor":["marketplace-monitoring", "content-scraping"],
    "brokermr810--QuantDinger":     ["quant-trading"],
    "THU-MAIC--OpenMAIC":           ["educational-content"],
    "zinan92--repo-evals":          ["repo-evaluation"],
}


def apply_updates() -> None:
    for slug, tags in TAGS.items():
        repo_path = ROOT / "repos" / slug / "repo.yaml"
        if not repo_path.exists():
            print(f"  SKIP {slug} — no repo.yaml", file=sys.stderr)
            continue
        data = yaml.safe_load(repo_path.read_text()) or {}
        data["use_case_tags"] = tags
        repo_path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=2000)
        )
        print(f"  UPDATED {slug}  tags={tags}")


if __name__ == "__main__":
    apply_updates()
