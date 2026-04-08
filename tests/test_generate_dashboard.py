"""
Tests for scripts/generate_dashboard.py
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_dashboard as gd  # noqa: E402


def test_parse_gap_report_counts_and_items():
    text = """
# Coverage Gap Report — demo

**Gaps:** 4  (critical: 2, warning: 1, info: 1)

## Critical (2)

- **[CRITICAL_CLAIM_FAILED]** `claim-001` — boom
- **[CRITICAL_CLAIM_UNTESTED]** `claim-002` — not covered

## Warnings (1)

- **[HIGH_CLAIM_UNTESTED]** `claim-003` — later

## Info (1)

- **[ORPHAN_PLAN_REFERENCE]** `-` — nice to know
"""
    parsed = gd.parse_gap_report(text)
    assert parsed["counts"] == {"total": 4, "critical": 2, "warning": 1, "info": 1}
    assert parsed["critical_items"][0]["code"] == "CRITICAL_CLAIM_FAILED"
    assert parsed["warning_items"][0]["claim_id"] == "claim-003"
    assert parsed["info_items"][0]["code"] == "ORPHAN_PLAN_REFERENCE"


def test_parse_diff_summary_markdown_extracts_headline_and_confidence():
    text = """
# Re-Eval Diff — demo

**from:** `HEAD~2` (`7127d8c`) → **to:** `working`

**Comparison confidence:** medium
  - baseline provenance quality is 'missing'

## Headline

Verdict did not change bucket (`usable` → `usable`).

## Verdict
"""
    parsed = gd.parse_diff_summary_markdown(text)
    assert parsed["headline"] == "Verdict did not change bucket (`usable` → `usable`)."
    assert parsed["comparison_confidence"] == "medium"
    assert parsed["from_ref"] == "HEAD~2"
    assert parsed["from_sha"] == "7127d8c"
    assert parsed["to_ref"] == "working"


def test_collect_repo_record_on_real_repo():
    repo = gd.collect_repo_record(ROOT / "repos" / "zinan92--content-downloader")
    assert repo["slug"] == "zinan92--content-downloader"
    assert repo["current_bucket"] == "usable"
    assert repo["archetype"] == "adapter"
    assert repo["claims_summary"]["total"] >= 1
    assert repo["runs_summary"]["count"] >= 1
    assert repo["latest_gap_report"]["counts"]["critical"] >= 1
    assert repo["latest_diff"]["comparison_confidence"]["level"] in {"high", "medium", "low", "unknown"}


def test_collect_dashboard_data_contains_all_real_repos():
    site = gd.collect_dashboard_data(ROOT)
    slugs = [repo["slug"] for repo in site["repos"]]
    assert "zinan92--content-downloader" in slugs
    assert "zinan92--content-toolkit" in slugs
    assert site["stats"]["repo_count"] >= 5
    assert "bucket_counts" in site["stats"]


def test_collect_dashboard_data_skips_incomplete_repo_dirs():
    with tempfile.TemporaryDirectory() as tmp:
        temp_root = pathlib.Path(tmp)
        repos_dir = temp_root / "repos"
        repos_dir.mkdir()

        good = repos_dir / "owner--good"
        (good / "claims").mkdir(parents=True)
        (good / "repo.yaml").write_text(
            "owner: owner\nrepo: good\ndisplay_name: good\nrepo_type: skill\narchetype: adapter\nstatus: evaluated\ncurrent_bucket: usable\n"
        )
        (good / "claims" / "claim-map.yaml").write_text("claims: []\n")

        bad = repos_dir / "owner--bad"
        bad.mkdir()

        old_root = gd.ROOT
        old_repos_dir = gd.REPOS_DIR
        try:
            gd.ROOT = temp_root
            gd.REPOS_DIR = repos_dir
            site = gd.collect_dashboard_data(temp_root)
        finally:
            gd.ROOT = old_root
            gd.REPOS_DIR = old_repos_dir

        assert [repo["slug"] for repo in site["repos"]] == ["owner--good"]
        assert site["stats"]["repo_count"] == 1


def test_write_dashboard_creates_index_repo_pages_and_json():
    site = gd.collect_dashboard_data(ROOT)
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "dashboard"
        gd.write_dashboard(site, out)
        assert (out / "index.html").exists()
        assert (out / "assets" / "style.css").exists()
        assert (out / "assets" / "app.js").exists()
        assert (out / "data" / "index.json").exists()
        assert (out / "repos" / "zinan92--content-downloader.html").exists()
        payload = json.loads((out / "data" / "index.json").read_text())
        assert payload["stats"]["repo_count"] >= 5
        html_text = (out / "index.html").read_text()
        assert "repo-evals operator dashboard" in html_text
        assert "zinan92--content-downloader" in html_text
        assert "../repos/zinan92--content-downloader/repo.yaml" in html_text


if __name__ == "__main__":
    import traceback

    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception:
                failed += 1
                print(f"  FAIL  {name}")
                traceback.print_exc()
    print(f"\n{'-'*40}\n{'FAILED' if failed else 'OK'}: {failed} failures")
    sys.exit(1 if failed else 0)
