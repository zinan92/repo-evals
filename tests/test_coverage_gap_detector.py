"""
Tests for scripts/coverage_gap_detector.py

Runs each rule against a synthetic repo tree to keep fixtures tight
and deterministic.
"""

from __future__ import annotations

import pathlib
import shutil
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import coverage_gap_detector as cgd  # noqa: E402


# --- Synthetic repo helper -------------------------------------------------


def _mk_repo(
    tmp: pathlib.Path,
    *,
    archetype: str = "pure-cli",
    claims: list[dict] | None = None,
    plan: str | None = None,
    runs: list[dict] | None = None,
) -> pathlib.Path:
    repo = tmp / "test--repo"
    (repo / "claims").mkdir(parents=True)
    (repo / "plans").mkdir()
    (repo / "runs").mkdir()

    # repo.yaml
    (repo / "repo.yaml").write_text(yaml.safe_dump({
        "owner": "test", "repo": "repo",
        "archetype": archetype,
    }))

    # claim-map.yaml
    (repo / "claims" / "claim-map.yaml").write_text(yaml.safe_dump({
        "claims": claims or [],
    }, allow_unicode=True))

    if plan is not None:
        (repo / "plans" / "2026-04-07-eval-plan.md").write_text(plan)

    # runs
    for i, r in enumerate(runs or [], start=1):
        d = repo / "runs" / "2026-04-07" / f"run-{i}"
        d.mkdir(parents=True)
        (d / "run-summary.yaml").write_text(yaml.safe_dump(r, allow_unicode=True))

    return repo


def _good_claim(**kw):
    base = {
        "id": "claim-001",
        "title": "Main happy path",
        "priority": "critical",
        "area": "core",
        "statement": "Runs and returns 0.",
        "business_expectation": "It works.",
        "evidence_needed": "Run exits 0 on a sample input.",
        "status": "passed",
    }
    base.update(kw)
    return base


# --- Rule: blank evidence_needed -------------------------------------------


def test_blank_evidence_on_critical_is_critical():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[_good_claim(evidence_needed="")],
            plan="mentions claim-001 Main happy path",
        )
        report = cgd.build_report(repo)
        assert any(
            g["code"] == "EVIDENCE_NEEDED_BLANK" and g["severity"] == "critical"
            for g in report["gaps"]
        )


def test_blank_evidence_on_medium_is_warning():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[_good_claim(priority="medium", evidence_needed="")],
            plan="claim-001 Main happy path",
        )
        report = cgd.build_report(repo)
        g = next(g for g in report["gaps"] if g["code"] == "EVIDENCE_NEEDED_BLANK")
        assert g["severity"] == "warning"


# --- Rule: critical claim not mentioned in plan ----------------------------


def test_critical_claim_missing_from_plan_flagged():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[
                _good_claim(id="claim-001"),
                _good_claim(id="claim-002", title="Another thing"),
            ],
            plan="# Plan\nOnly mentions claim-001 Main happy path\n",
        )
        report = cgd.build_report(repo)
        assert any(
            g["code"] == "CRITICAL_CLAIM_MISSING_FROM_PLAN"
            and g["claim_id"] == "claim-002"
            for g in report["gaps"]
        )


def test_plan_referencing_claim_by_title_is_ok():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[_good_claim(id="claim-001", title="Unique Title XYZ")],
            plan="The plan will validate: Unique Title XYZ in scenario 1.",
        )
        report = cgd.build_report(repo)
        assert not any(
            g["code"] == "CRITICAL_CLAIM_MISSING_FROM_PLAN"
            for g in report["gaps"]
        )


# --- Rule: critical untested / failed --------------------------------------


def test_critical_untested_flagged():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[_good_claim(status="untested")],
            plan="claim-001 Main happy path",
        )
        report = cgd.build_report(repo)
        assert any(g["code"] == "CRITICAL_CLAIM_UNTESTED" for g in report["gaps"])


def test_critical_failed_flagged():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[_good_claim(status="failed")],
            plan="claim-001 Main happy path",
        )
        report = cgd.build_report(repo)
        assert any(g["code"] == "CRITICAL_CLAIM_FAILED" for g in report["gaps"])


def test_high_untested_is_warning_not_critical():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[_good_claim(priority="high", status="untested")],
            plan="claim-001 Main happy path",
        )
        report = cgd.build_report(repo)
        g = next(g for g in report["gaps"] if g["code"] == "HIGH_CLAIM_UNTESTED")
        assert g["severity"] == "warning"


# --- Rule: run evidence missing --------------------------------------------


def test_claim_with_status_but_no_run_evidence_flagged():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[_good_claim(status="passed")],
            plan="claim-001 Main happy path",
            runs=[{
                "run_name": "r1",
                # Deliberately has no results_by_claim
                "result": "pass",
            }],
        )
        report = cgd.build_report(repo)
        assert any(
            g["code"] == "CLAIM_STATUS_BUT_NO_RUN_EVIDENCE"
            for g in report["gaps"]
        )


def test_claim_covered_by_results_by_claim_is_ok():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[_good_claim(status="passed")],
            plan="claim-001 Main happy path",
            runs=[{
                "run_name": "r1",
                "result": "pass",
                "results_by_claim": {"claim-001-main": "pass"},
            }],
        )
        report = cgd.build_report(repo)
        assert not any(
            g["code"] == "CLAIM_STATUS_BUT_NO_RUN_EVIDENCE"
            for g in report["gaps"]
        )


# --- Rule: orphan plan reference -------------------------------------------


def test_orphan_plan_reference_is_info():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[_good_claim(id="claim-001")],
            plan="We will test claim-001 and claim-999 too.",
        )
        report = cgd.build_report(repo)
        orphans = [g for g in report["gaps"] if g["code"] == "ORPHAN_PLAN_REFERENCE"]
        assert len(orphans) == 1
        assert orphans[0]["claim_id"] == "claim-999"
        assert orphans[0]["severity"] == "info"


# --- Rule: hybrid archetype, no core claim ---------------------------------


def test_hybrid_archetype_without_core_claims_flagged():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            archetype="hybrid-skill",
            claims=[
                _good_claim(id="claim-001", area="support-install"),
                _good_claim(id="claim-002", area="support-templates"),
            ],
            plan="claim-001 Main happy path claim-002 Main happy path",
        )
        report = cgd.build_report(repo)
        assert any(
            g["code"] == "HYBRID_ARCHETYPE_NO_CORE_CLAIMS"
            for g in report["gaps"]
        )


def test_hybrid_archetype_with_core_area_is_ok():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            archetype="hybrid-skill",
            claims=[
                _good_claim(id="claim-001", area="support-install"),
                _good_claim(id="claim-101", area="core-llm", title="Core LLM output"),
            ],
            plan=(
                "claim-001 Main happy path\n"
                "claim-101 Core LLM output\n"
            ),
        )
        report = cgd.build_report(repo)
        assert not any(
            g["code"] == "HYBRID_ARCHETYPE_NO_CORE_CLAIMS"
            for g in report["gaps"]
        )


# --- fail-on behavior ------------------------------------------------------


def test_summary_counts_match_rules_fired():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[
                _good_claim(id="claim-001", status="untested"),
                _good_claim(id="claim-002", priority="high", status="untested"),
            ],
            plan="",  # blank plan → every critical claim will be flagged missing
        )
        report = cgd.build_report(repo)
        s = report["summary"]
        assert s["total"] == s["critical"] + s["warning"] + s["info"]
        assert s["critical"] >= 1
        assert s["warning"] >= 1


# --- Clean repo sanity -----------------------------------------------------


def test_clean_repo_has_no_gaps():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(
            pathlib.Path(t),
            claims=[
                _good_claim(id="claim-001", title="Happy path"),
            ],
            plan="The plan validates claim-001 Happy path with input A.",
            runs=[{
                "run_name": "r1",
                "result": "pass",
                "results_by_claim": {"claim-001": "pass"},
            }],
        )
        report = cgd.build_report(repo)
        assert report["summary"]["total"] == 0, report["gaps"]


# --- Ad-hoc runner ---------------------------------------------------------


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
