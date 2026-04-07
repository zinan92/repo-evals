"""
Tests for scripts/reeval_diff.py — Re-Eval Diff Mode.

Covers:
  - Transition classification (improvement / regression / newly_failing / unchanged)
  - Bucket change classification (improvement / regression / unclassifiable)
  - Claim diff (added / removed / status / priority / title / area changes)
  - Run set diff
  - Gap report diff (structured + committed-markdown fallback)
  - Provenance quality detection (full / partial / missing)
  - Comparison confidence downgrades
  - Snapshot loading from a real temporary git repo
  - Missing baseline handled as low-confidence first-time eval
  - Self-compare produces zero movement
  - Real fixture test against the repo-evals HEAD itself
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reeval_diff as rd  # noqa: E402


# --- Pure classification --------------------------------------------------


def test_transition_improvements():
    assert rd.classify_transition("untested", "passed") == "improvement"
    assert rd.classify_transition("failed", "passed") == "improvement"
    assert rd.classify_transition("failed_partial", "passed_with_concerns") == "improvement"


def test_transition_regressions():
    assert rd.classify_transition("passed", "failed") == "regression"
    assert rd.classify_transition("passed", "untested") == "regression"
    assert rd.classify_transition("passed_with_concerns", "failed") == "regression"


def test_transition_newly_failing():
    # untested → failed is "we learned something bad" — not regression,
    # because there's nothing to regress from, but it's not an improvement
    # either. The differ must classify this as newly_failing.
    assert rd.classify_transition("untested", "failed") == "newly_failing"


def test_transition_unchanged():
    assert rd.classify_transition("passed", "passed") == "unchanged"
    assert rd.classify_transition("untested", "untested") == "unchanged"
    assert rd.classify_transition("failed", "failed") == "unchanged"


def test_transition_passed_with_concerns_treated_as_passed():
    # Normalization should collapse passed_with_concerns into "passed"
    assert rd.classify_transition("passed", "passed_with_concerns") == "unchanged"


# --- Bucket classification ------------------------------------------------


def test_bucket_improvement_and_regression():
    assert rd.classify_bucket_change("usable", "reusable") == "improvement"
    assert rd.classify_bucket_change("reusable", "recommendable") == "improvement"
    assert rd.classify_bucket_change("reusable", "usable") == "regression"
    assert rd.classify_bucket_change("recommendable", "unusable") == "regression"


def test_bucket_unchanged():
    assert rd.classify_bucket_change("usable", "usable") == "unchanged"
    assert rd.classify_bucket_change(None, None) == "unchanged"


def test_bucket_unknown_is_unclassifiable():
    assert rd.classify_bucket_change("unknown", "usable") == "unclassifiable"
    assert rd.classify_bucket_change("usable", "unknown") == "unclassifiable"
    assert rd.classify_bucket_change(None, "usable") == "unclassifiable"


def test_bucket_canonical_order():
    ranks = rd.BUCKET_RANK
    assert ranks["unusable"] < ranks["usable"] < ranks["reusable"] < ranks["recommendable"]


# --- Claim diff -----------------------------------------------------------


def _cl(id_, status="untested", priority="medium", title="", area="core"):
    return {
        "id": id_, "title": title or id_, "status": status,
        "priority": priority, "area": area,
    }


def test_claim_diff_added_and_removed():
    f = [_cl("claim-001"), _cl("claim-002")]
    t = [_cl("claim-002"), _cl("claim-003")]
    d = rd.diff_claims(f, t)
    assert [c["id"] for c in d["added"]] == ["claim-003"]
    assert [c["id"] for c in d["removed"]] == ["claim-001"]


def test_claim_diff_status_change_recorded_with_transition():
    f = [_cl("claim-001", status="untested", priority="critical")]
    t = [_cl("claim-001", status="passed", priority="critical")]
    d = rd.diff_claims(f, t)
    changes = d["status_changes"]
    assert len(changes) == 1
    c = changes[0]
    assert c["from"] == "untested"
    assert c["to"] == "passed"
    assert c["transition"] == "improvement"
    assert c["priority"] == "critical"


def test_claim_diff_priority_change_separate_from_status():
    f = [_cl("claim-001", status="passed", priority="medium")]
    t = [_cl("claim-001", status="passed", priority="critical")]
    d = rd.diff_claims(f, t)
    assert d["status_changes"] == []
    assert len(d["priority_changes"]) == 1


def test_claim_diff_title_and_area_changes():
    f = [_cl("claim-001", title="Old title", area="core")]
    t = [_cl("claim-001", title="New title", area="extra")]
    d = rd.diff_claims(f, t)
    assert len(d["title_changes"]) == 1
    assert len(d["area_changes"]) == 1


def test_claim_diff_unchanged_claim_produces_no_rows():
    f = [_cl("claim-001", status="passed")]
    t = [_cl("claim-001", status="passed")]
    d = rd.diff_claims(f, t)
    assert d["added"] == []
    assert d["removed"] == []
    assert d["status_changes"] == []
    assert d["priority_changes"] == []
    assert d["title_changes"] == []
    assert d["area_changes"] == []


# --- Runs diff ------------------------------------------------------------


def test_runs_diff_set_difference():
    f = [{"_path": "runs/2026-04-07/run-a/run-summary.yaml"},
         {"_path": "runs/2026-04-07/run-b/run-summary.yaml"}]
    t = [{"_path": "runs/2026-04-07/run-b/run-summary.yaml"},
         {"_path": "runs/2026-04-08/run-c/run-summary.yaml"}]
    d = rd.diff_runs(f, t)
    assert d["from_count"] == 2
    assert d["to_count"] == 2
    assert d["added"] == ["runs/2026-04-08/run-c/run-summary.yaml"]
    assert d["removed"] == ["runs/2026-04-07/run-a/run-summary.yaml"]


# --- Gap report diff ------------------------------------------------------


def _gap(code, cid="claim-001", severity="critical", message="x"):
    return {"code": code, "claim_id": cid, "severity": severity, "message": message}


def test_gap_diff_structured_closed_and_opened():
    f = {
        "summary": {"total": 3, "critical": 2, "warning": 1, "info": 0},
        "gaps": [
            _gap("CRITICAL_CLAIM_UNTESTED"),
            _gap("CRITICAL_CLAIM_FAILED", cid="claim-002"),
            _gap("HIGH_CLAIM_UNTESTED", cid="claim-003", severity="warning"),
        ],
    }
    t = {
        "summary": {"total": 2, "critical": 1, "warning": 1, "info": 0},
        "gaps": [
            _gap("CRITICAL_CLAIM_FAILED", cid="claim-002"),
            _gap("HIGH_CLAIM_UNTESTED", cid="claim-003", severity="warning"),
        ],
    }
    d = rd.diff_gap_reports(f, t)
    assert d["baseline_kind"] == "structured"
    assert d["head_kind"] == "structured"
    assert [g["code"] for g in d["closed"]] == ["CRITICAL_CLAIM_UNTESTED"]
    assert d["opened"] == []
    assert d["summary_delta"]["total"] == -1
    assert d["summary_delta"]["critical"] == -1


def test_gap_diff_committed_markdown_baseline_is_not_structured():
    # Working tree → structured, but the baseline came from a committed
    # markdown report under gap-reports/. The differ must honestly admit
    # it cannot compute a structured diff in that case.
    f = {"committed_report_path": "gap-reports/old.md", "gaps": []}
    t = {
        "summary": {"total": 1, "critical": 1, "warning": 0, "info": 0},
        "gaps": [_gap("CRITICAL_CLAIM_UNTESTED")],
    }
    d = rd.diff_gap_reports(f, t)
    assert d["baseline_kind"] == "committed-markdown"
    assert d["head_kind"] == "structured"
    assert d["closed"] == []
    assert d["opened"] == []
    assert d["summary_delta"] is None


def test_gap_diff_missing_both_sides():
    d = rd.diff_gap_reports(None, None)
    assert d["baseline_kind"] == "missing"
    assert d["head_kind"] == "missing"


# --- Provenance quality ---------------------------------------------------


def test_provenance_full_when_every_run_is_captured_and_not_partial():
    runs = [
        {"provenance": {"captured": True, "partial": False}},
        {"provenance": {"captured": True, "partial": False}},
    ]
    assert rd._provenance_quality(runs) == "full"


def test_provenance_partial_when_any_is_partial():
    runs = [
        {"provenance": {"captured": True, "partial": False}},
        {"provenance": {"captured": True, "partial": True}},
    ]
    assert rd._provenance_quality(runs) == "partial"


def test_provenance_missing_when_nothing_captured():
    # This is the honest classification for the 5 legacy evaluated repos.
    runs = [
        {"provenance": {"captured": False}},
        {"provenance": {"captured": False}},
    ]
    assert rd._provenance_quality(runs) == "missing"


def test_provenance_missing_when_no_runs():
    assert rd._provenance_quality([]) == "missing"


def test_provenance_partial_when_mix_of_captured_and_not():
    runs = [
        {"provenance": {"captured": True, "partial": False}},
        {"provenance": {"captured": False}},
    ]
    assert rd._provenance_quality(runs) == "partial"


# --- Confidence assessment ------------------------------------------------


def test_confidence_high_on_clean_full_snapshots():
    f = rd.Snapshot(
        ref="HEAD~1",
        repo_meta={"archetype": "adapter", "current_bucket": "usable"},
        claims=[_cl("claim-001", status="passed", priority="critical")],
        verdict_bucket="usable",
        runs=[{"provenance": {"captured": True, "partial": False}}],
        provenance_quality="full",
    )
    t = rd.Snapshot(
        ref="working",
        repo_meta={"archetype": "adapter", "current_bucket": "reusable"},
        claims=[_cl("claim-001", status="passed", priority="critical")],
        verdict_bucket="reusable",
        runs=[{"provenance": {"captured": True, "partial": False}}],
        provenance_quality="full",
    )
    conf = rd.assess_confidence(f, t)
    assert conf["level"] == "high"
    assert conf["reasons"] == []


def test_confidence_medium_when_baseline_provenance_partial():
    f = rd.Snapshot(
        ref="HEAD~1",
        repo_meta={"current_bucket": "usable"},
        claims=[_cl("claim-001")],
        verdict_bucket="usable",
        provenance_quality="partial",
    )
    t = rd.Snapshot(
        ref="working",
        repo_meta={"current_bucket": "usable"},
        claims=[_cl("claim-001")],
        verdict_bucket="usable",
        provenance_quality="full",
    )
    conf = rd.assess_confidence(f, t)
    assert conf["level"] == "medium"
    assert any("baseline provenance" in r for r in conf["reasons"])


def test_confidence_low_when_baseline_snapshot_empty():
    f = rd.Snapshot(ref="ea4bb73")
    t = rd.Snapshot(
        ref="working",
        repo_meta={"current_bucket": "usable"},
        claims=[_cl("claim-001")],
        verdict_bucket="usable",
        provenance_quality="full",
    )
    conf = rd.assess_confidence(f, t)
    assert conf["level"] == "low"
    assert any("has no usable data" in r for r in conf["reasons"])


# --- Summary --------------------------------------------------------------


def test_summarize_counts_movement_correctly():
    diff = {
        "claims": {
            "added": [{"id": "claim-003"}],
            "removed": [],
            "status_changes": [
                {"transition": "improvement"},
                {"transition": "improvement"},
                {"transition": "regression"},
                {"transition": "newly_failing"},
                {"transition": "unchanged"},
            ],
        },
        "verdict": {"bucket_change": "improvement"},
        "runs": {"added": ["x"], "removed": []},
        "gap_report": {"closed": [{}, {}], "opened": [{}]},
    }
    s = rd.summarize(diff)
    assert s["status_improvements"] == 2
    assert s["status_regressions"] == 1
    assert s["status_newly_failing"] == 1
    assert s["claims_added"] == 1
    assert s["claims_removed"] == 0
    assert s["runs_added"] == 1
    assert s["gaps_closed"] == 2
    assert s["gaps_opened"] == 1
    assert s["bucket_change"] == "improvement"


# --- Snapshot loader integration test (real git + temporary repo) --------


def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)


def _init_tmp_git_repo() -> pathlib.Path:
    tmp = pathlib.Path(tempfile.mkdtemp())
    _run(["git", "init", "-q"], tmp)
    _run(["git", "config", "user.email", "test@example.com"], tmp)
    _run(["git", "config", "user.name", "Test"], tmp)
    return tmp


def _make_baseline_repo(root: pathlib.Path) -> pathlib.Path:
    """Create a minimal repo-evals layout with one evaluated repo at
    'baseline' state (one critical claim, untested, usable bucket)."""
    slug = "test--sample"
    repo = root / "repos" / slug
    (repo / "claims").mkdir(parents=True)
    (repo / "runs").mkdir()
    (repo / "verdicts").mkdir()
    (repo / "plans").mkdir()
    (repo / "repo.yaml").write_text(yaml.safe_dump({
        "owner": "test", "repo": "sample",
        "archetype": "pure-cli",
        "current_bucket": "usable",
    }))
    (repo / "claims" / "claim-map.yaml").write_text(yaml.safe_dump({
        "claims": [
            _cl("claim-001", status="untested", priority="critical",
                title="Happy path works"),
        ],
    }))
    (repo / "plans" / "2026-04-07-eval-plan.md").write_text(
        "# plan\nclaim-001 Happy path works\n"
    )
    return repo


def test_snapshot_loader_reads_git_history_and_working_tree():
    tmp = _init_tmp_git_repo()
    try:
        repo_dir = _make_baseline_repo(tmp)
        _run(["git", "add", "-A"], tmp)
        _run(["git", "commit", "-q", "-m", "baseline"], tmp)

        # Now improve the state: claim goes from untested → passed
        cm_path = repo_dir / "claims" / "claim-map.yaml"
        cm = yaml.safe_load(cm_path.read_text())
        cm["claims"][0]["status"] = "passed"
        cm_path.write_text(yaml.safe_dump(cm))
        repo_yaml = repo_dir / "repo.yaml"
        meta = yaml.safe_load(repo_yaml.read_text())
        meta["current_bucket"] = "reusable"
        repo_yaml.write_text(yaml.safe_dump(meta))

        diff = rd.build_diff(repo_dir, "HEAD", "working", root=tmp)

        assert diff["baseline"]["exists"]
        assert diff["head"]["exists"]
        assert diff["baseline"]["verdict_bucket"] == "usable"
        assert diff["head"]["verdict_bucket"] == "reusable"
        assert diff["verdict"]["bucket_change"] == "improvement"

        s = diff["summary"]
        assert s["status_improvements"] == 1
        assert s["status_regressions"] == 0
        assert s["bucket_change"] == "improvement"

        # from_ref resolves to a SHA because we committed
        assert diff["from_sha"] is not None
        # working never resolves
        assert diff["to_sha"] is None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_snapshot_loader_missing_baseline_yields_low_confidence():
    tmp = _init_tmp_git_repo()
    try:
        repo_dir = _make_baseline_repo(tmp)
        # commit the initial state (so HEAD exists)
        _run(["git", "add", "-A"], tmp)
        _run(["git", "commit", "-q", "-m", "init"], tmp)

        # Now compare against an even earlier ref that doesn't exist —
        # use the repo root commit sha but remove the repo from working tree
        # by comparing HEAD~0 (self) is not interesting. Instead, use a
        # bogus sha.
        diff = rd.build_diff(repo_dir, "0000000", "working", root=tmp)
        assert not diff["baseline"]["exists"]
        assert diff["comparison_confidence"]["level"] == "low"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_self_compare_has_zero_movement():
    tmp = _init_tmp_git_repo()
    try:
        repo_dir = _make_baseline_repo(tmp)
        _run(["git", "add", "-A"], tmp)
        _run(["git", "commit", "-q", "-m", "baseline"], tmp)
        diff = rd.build_diff(repo_dir, "HEAD", "HEAD", root=tmp)
        s = diff["summary"]
        assert s["status_improvements"] == 0
        assert s["status_regressions"] == 0
        assert s["status_newly_failing"] == 0
        assert s["claims_added"] == 0
        assert s["claims_removed"] == 0
        assert s["bucket_change"] == "unchanged"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_added_and_removed_claims_flow_through_build_diff():
    tmp = _init_tmp_git_repo()
    try:
        repo_dir = _make_baseline_repo(tmp)
        _run(["git", "add", "-A"], tmp)
        _run(["git", "commit", "-q", "-m", "baseline"], tmp)

        cm_path = repo_dir / "claims" / "claim-map.yaml"
        cm = yaml.safe_load(cm_path.read_text())
        cm["claims"].append(_cl("claim-002", status="passed", priority="high",
                                title="Second claim"))
        cm["claims"] = [c for c in cm["claims"] if c["id"] != "claim-001"]
        cm_path.write_text(yaml.safe_dump(cm))

        diff = rd.build_diff(repo_dir, "HEAD", "working", root=tmp)
        assert [c["id"] for c in diff["claims"]["added"]] == ["claim-002"]
        assert [c["id"] for c in diff["claims"]["removed"]] == ["claim-001"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- Real repo-evals HEAD smoke test --------------------------------------


def test_real_repo_evals_self_compare_produces_no_movement():
    """Regression guard: comparing HEAD against HEAD on a real evaluated
    repo in this tree must yield a zero-movement diff."""
    repo_dir = ROOT / "repos" / "zinan92--content-downloader"
    if not repo_dir.exists():
        return  # skip gracefully if the repo was ever removed
    diff = rd.build_diff(repo_dir, "HEAD", "HEAD", root=ROOT)
    s = diff["summary"]
    assert s["status_improvements"] == 0
    assert s["status_regressions"] == 0
    assert s["claims_added"] == 0
    assert s["claims_removed"] == 0
    assert diff["verdict"]["bucket_change"] == "unchanged"


# --- Markdown renderer sanity --------------------------------------------


def test_markdown_renderer_contains_key_sections():
    diff = {
        "repo": "owner--repo",
        "from_ref": "HEAD~1",
        "from_sha": "abc1234",
        "to_ref": "working",
        "to_sha": None,
        "baseline": {"exists": True, "provenance_quality": "full",
                     "claim_count": 2, "verdict_bucket": "usable",
                     "archetype": "adapter", "errors": []},
        "head": {"exists": True, "provenance_quality": "full",
                 "claim_count": 2, "verdict_bucket": "reusable",
                 "archetype": "adapter", "errors": []},
        "archetype_change": {"from": "adapter", "to": "adapter", "changed": False},
        "verdict": {"from_bucket": "usable", "to_bucket": "reusable",
                    "bucket_change": "improvement"},
        "claims": {
            "added": [],
            "removed": [],
            "status_changes": [{
                "id": "claim-001", "title": "Main path", "priority": "critical",
                "from": "untested", "to": "passed", "transition": "improvement",
            }],
            "priority_changes": [],
            "title_changes": [],
            "area_changes": [],
        },
        "runs": {"from_count": 1, "to_count": 2, "added": ["runs/x"], "removed": []},
        "gap_report": {
            "baseline_kind": "structured", "head_kind": "structured",
            "closed": [], "opened": [],
            "summary_delta": {"total": -1, "critical": -1, "warning": 0, "info": 0},
        },
        "comparison_confidence": {"level": "high", "reasons": []},
    }
    diff["summary"] = rd.summarize(diff)
    out = rd.render_markdown(diff)
    assert "# Re-Eval Diff — owner--repo" in out
    assert "Comparison confidence:** high" in out
    assert "## Headline" in out
    assert "improved" in out
    assert "Improvements" in out
    assert "`claim-001`" in out
    assert "## Runs" in out
    assert "## Coverage gaps" in out
    assert "## Snapshot integrity" in out


# --- Ad-hoc runner --------------------------------------------------------

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
