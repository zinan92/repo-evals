from __future__ import annotations

import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import publish_eval as pe  # noqa: E402


def test_normalise_slug_accepts_owner_repo_and_slug():
    assert pe.normalise_slug("owner/repo") == "owner--repo"
    assert pe.normalise_slug("owner--repo") == "owner--repo"
    assert pe.normalise_slug("/owner/repo/") == "owner--repo"


def test_build_commands_render_each_slug_then_dashboard_once():
    commands = pe.build_commands(
        ["owner--one", "owner--two"],
        date="2026-07-09",
        lang="zh",
    )

    assert len(commands) == 3
    assert commands[0][1].endswith("scripts/render_verdict_html.py")
    assert commands[0][2:] == [
        "owner--one",
        "--lang",
        "zh",
        "--no-dashboard",
        "--date",
        "2026-07-09",
    ]
    assert commands[1][1].endswith("scripts/render_verdict_html.py")
    assert commands[1][2] == "owner--two"
    assert commands[2][1].endswith("scripts/build_master_dashboard.py")
