"""
Tests for scripts/verdict_calculator.py

Exercises the rule table directly via compute_verdict() — no YAML I/O in tests.
Run:
    python3 -m pytest tests/test_verdict_calculator.py -v
or (if pytest not available):
    python3 tests/test_verdict_calculator.py
"""

from __future__ import annotations

import pathlib
import sys

# Make scripts/ importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verdict_calculator import (  # noqa: E402
    BUCKETS,
    VerdictError,
    compute_verdict,
)


# --- Fixtures --------------------------------------------------------------


def _claims(*triples):
    return [
        {"id": f"claim-{i:03d}", "priority": p, "status": s}
        for i, (p, s) in enumerate(triples, start=1)
    ]


# --- Happy-path bucket tiers ----------------------------------------------


def test_all_critical_pass_plus_breadth_is_recommendable():
    rec = compute_verdict({
        "repo": "owner/pure-cli",
        "archetype": "pure-cli",
        "core_layer_tested": True,
        "evidence_completeness": "full",
        "claims": _claims(
            ("critical", "passed"),
            ("critical", "passed"),
            ("high", "passed"),
            ("high", "passed"),
            ("medium", "passed"),
        ),
    })
    assert rec["recommended_bucket"] == "recommendable"
    assert rec["final_bucket"] == "recommendable"
    assert rec["confidence"] == "high"
    assert rec["ceiling_reasons"] == []


def test_critical_failed_is_unusable():
    rec = compute_verdict({
        "archetype": "pure-cli",
        "core_layer_tested": True,
        "evidence_completeness": "full",
        "claims": _claims(
            ("critical", "failed"),
            ("critical", "passed"),
            ("high", "passed"),
        ),
    })
    assert rec["recommended_bucket"] == "unusable"
    assert any("critical claim" in b for b in rec["blocking_issues"])


def test_partial_critical_coverage_is_usable():
    rec = compute_verdict({
        "archetype": "pure-cli",
        "core_layer_tested": True,
        "evidence_completeness": "portable",
        "claims": _claims(
            ("critical", "passed"),
            ("critical", "untested"),
            ("high", "passed"),
        ),
    })
    assert rec["recommended_bucket"] == "usable"
    assert rec["confidence"] == "low"  # untested critical → low confidence


# --- Ceiling: untested core layer (hybrid rule) ---------------------------


def test_hybrid_untested_core_caps_at_usable():
    """The most important rule: hybrid repo with support layer pristine but
    the LLM / user-facing layer untested must still cap at 'usable'."""
    rec = compute_verdict({
        "repo": "nicobailon/visual-explainer",
        "archetype": "hybrid-skill",
        "core_layer_tested": False,
        "evidence_completeness": "full",
        "claims": _claims(
            ("critical", "passed"),         # support: plugin structure
            ("critical", "passed"),         # support: templates render
            ("high", "passed"),             # support: failure transparency
            ("critical", "untested"),       # core: LLM end-to-end
            ("high", "untested"),           # core: proactive rendering
        ),
    })
    assert rec["recommended_bucket"] == "usable"
    assert rec["final_bucket"] == "usable"
    assert any("core user-facing layer untested" in r for r in rec["ceiling_reasons"])
    assert any("hybrid-repo rule" in r for r in rec["ceiling_reasons"])


def test_pure_cli_untested_core_also_capped():
    """The hybrid-specific message doesn't fire for non-hybrid archetypes,
    but the generic 'untested core layer' ceiling still applies."""
    rec = compute_verdict({
        "archetype": "pure-cli",
        "core_layer_tested": False,
        "evidence_completeness": "full",
        "claims": _claims(
            ("critical", "passed"),
            ("high", "passed"),
        ),
    })
    assert rec["recommended_bucket"] == "usable"
    assert not any("hybrid-repo rule" in r for r in rec["ceiling_reasons"])


# --- Ceiling: evidence completeness ---------------------------------------


def test_weak_evidence_caps_below_reusable():
    rec = compute_verdict({
        "archetype": "pure-cli",
        "core_layer_tested": True,
        "evidence_completeness": "partial",
        "claims": _claims(
            ("critical", "passed"),
            ("critical", "passed"),
            ("high", "passed"),
        ),
    })
    assert rec["recommended_bucket"] == "usable"
    assert any("evidence_completeness" in r for r in rec["ceiling_reasons"])


def test_portable_evidence_caps_at_reusable_not_recommendable():
    rec = compute_verdict({
        "archetype": "pure-cli",
        "core_layer_tested": True,
        "evidence_completeness": "portable",
        "claims": _claims(
            ("critical", "passed"),
            ("critical", "passed"),
            ("high", "passed"),
            ("high", "passed"),
            ("medium", "passed"),
        ),
    })
    assert rec["recommended_bucket"] == "reusable"


# --- Override path ---------------------------------------------------------


def test_override_requires_reason():
    try:
        compute_verdict({
            "archetype": "pure-cli",
            "core_layer_tested": True,
            "evidence_completeness": "full",
            "claims": _claims(("critical", "passed")),
            "override": {"apply": True, "bucket": "reusable"},
        })
    except VerdictError as e:
        assert "reason" in str(e)
    else:
        raise AssertionError("expected VerdictError")


def test_override_applied_becomes_final_but_recommended_unchanged():
    rec = compute_verdict({
        "archetype": "hybrid-skill",
        "core_layer_tested": False,
        "evidence_completeness": "full",
        "claims": _claims(
            ("critical", "passed"),
            ("critical", "untested"),
        ),
        "override": {
            "apply": True,
            "bucket": "reusable",
            "reason": "manual B-layer spot-check in runs/2026-04-07/smoke",
        },
    })
    assert rec["recommended_bucket"] == "usable"   # rules unchanged
    assert rec["final_bucket"] == "reusable"        # override won
    assert rec["override"]["applied"] is True
    assert "spot-check" in rec["override"]["reason"]


def test_override_bucket_must_be_valid():
    try:
        compute_verdict({
            "archetype": "pure-cli",
            "core_layer_tested": True,
            "evidence_completeness": "full",
            "claims": _claims(("critical", "passed")),
            "override": {"apply": True, "bucket": "awesome", "reason": "x"},
        })
    except VerdictError as e:
        assert "override.bucket" in str(e)
    else:
        raise AssertionError("expected VerdictError")


# --- Edge cases ------------------------------------------------------------


def test_no_claims_at_all_is_low_confidence_usable():
    rec = compute_verdict({
        "archetype": "pure-cli",
        "core_layer_tested": True,
        "evidence_completeness": "full",
        "claims": [],
    })
    assert rec["confidence"] == "low"
    assert any("no critical claims" in b for b in rec["blocking_issues"])


def test_passed_with_concerns_counts_as_passed():
    rec = compute_verdict({
        "archetype": "pure-cli",
        "core_layer_tested": True,
        "evidence_completeness": "full",
        "claims": _claims(
            ("critical", "passed_with_concerns"),
            ("critical", "passed"),
            ("high", "passed"),
        ),
    })
    assert rec["recommended_bucket"] in ("reusable", "recommendable")


def test_buckets_constant_matches_docs():
    assert BUCKETS == ["unusable", "usable", "reusable", "recommendable"]


# --- Ad-hoc runner (so tests work without pytest) --------------------------

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
