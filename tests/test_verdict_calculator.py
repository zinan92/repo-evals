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
    # Under the rebased confidence semantics (2026-05-05), confidence
    # is "how deep was the eval", not "how shaky is the bucket". An
    # untested critical claim already costs score points; we don't
    # double-count it as low confidence. With 3 claims, critical defined,
    # not all untested → medium is correct.
    assert rec["confidence"] == "medium"


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


# --- 0-100 score model ----------------------------------------------------


def test_score_base_is_40_for_empty_eval():
    """A minimal compute returns the base 40 — no claims = no static delta."""

    out = compute_verdict({
        "repo": "x/y", "archetype": "pure-cli", "core_layer_tested": False,
        "claims": [], "stars": 0, "has_license": True,
    })
    assert "score" in out
    assert out["score_breakdown"]["base"] == 40


def test_score_clean_static_eval_lifts_above_pass_line():
    """All-passed critical claims should land above 60 (the 'try' line)."""

    out = compute_verdict({
        "repo": "x/y", "archetype": "pure-cli", "core_layer_tested": False,
        "claims": [
            {"id": "c1", "priority": "critical", "status": "passed"},
            {"id": "c2", "priority": "critical", "status": "passed"},
            {"id": "c3", "priority": "critical", "status": "passed"},
            {"id": "c4", "priority": "high", "status": "passed"},
        ],
        "stars": 0, "has_license": True,
    })
    # 40 base + 5+5+5 critical + 2 high = 57 — below 60 (try) line.
    # A 4-claim pass shouldn't be enough to clear 60 alone — need
    # ecosystem or maintainer evidence too.
    assert out["score"] == 57
    assert out["tier_key"] == "risky"


def test_score_with_ecosystem_clears_try_line():
    """Same claims + 5K stars should clear 60 (tier 'try')."""

    out = compute_verdict({
        "repo": "x/y", "archetype": "pure-cli", "core_layer_tested": False,
        "claims": [
            {"id": "c1", "priority": "critical", "status": "passed"},
            {"id": "c2", "priority": "critical", "status": "passed"},
            {"id": "c3", "priority": "critical", "status": "passed"},
            {"id": "c4", "priority": "high", "status": "passed"},
        ],
        "stars": 5_000, "has_license": True,
    })
    assert out["score"] >= 60
    assert out["tier_key"] in {"try", "self"}


def test_score_failed_critical_pulls_below_pass_line():
    out = compute_verdict({
        "repo": "x/y", "archetype": "pure-cli", "core_layer_tested": True,
        "claims": [
            {"id": "c1", "priority": "critical", "status": "failed"},
            {"id": "c2", "priority": "critical", "status": "passed"},
        ],
        "stars": 100_000, "has_license": True,
    })
    assert out["score"] < 60


def test_score_archived_repo_floors_score():
    out = compute_verdict({
        "repo": "x/y", "archetype": "pure-cli", "core_layer_tested": True,
        "claims": [{"id": "c1", "priority": "critical", "status": "passed"}],
        "stars": 50_000, "has_license": True, "archived": True,
    })
    assert out["score"] < 40
    assert out["tier_key"] == "broken"


def _input_with_concern_area(area: str) -> dict:
    return {
        "repo": "x/y", "archetype": "adapter", "core_layer_tested": True,
        "claims": [
            {"id": "c1", "priority": "critical",
             "status": "passed_with_concerns", "area": area},
        ],
        "stars": 1_000, "has_license": True,
    }


def test_score_privacy_concerns_penalised():
    """passed_with_concerns in a privacy/security area should cost points."""

    cosmetic = compute_verdict(_input_with_concern_area("install-quality"))
    privacy  = compute_verdict(_input_with_concern_area("privacy"))
    assert privacy["score"] < cosmetic["score"]


def test_confidence_default_is_medium_for_static_eval():
    """Confidence describes eval depth, not score shakiness.

    A standard static eval with critical claims defined and a normal
    pass/untested mix should be `medium` — not `low` just because some
    claims weren't live-tested. (That's already captured in the score.)
    """
    out = compute_verdict({
        "repo": "x/y", "archetype": "pure-cli", "core_layer_tested": False,
        "evidence_completeness": "partial",
        "claims": [
            {"id": "c1", "priority": "critical", "status": "passed"},
            {"id": "c2", "priority": "critical", "status": "passed"},
            {"id": "c3", "priority": "critical", "status": "untested"},
            {"id": "c4", "priority": "high", "status": "passed"},
        ],
        "stars": 1_000, "has_license": True,
    })
    assert out["confidence"] == "medium"


def test_confidence_low_when_too_few_claims():
    out = compute_verdict({
        "repo": "x/y", "archetype": "pure-cli", "core_layer_tested": True,
        "claims": [{"id": "c1", "priority": "critical", "status": "passed"}],
        "stars": 0, "has_license": True,
    })
    assert out["confidence"] == "low"


def test_confidence_high_when_critical_failure_or_full_evidence():
    """Confidence in the bad news, or in live-run evidence."""
    bad = compute_verdict({
        "repo": "x/y", "archetype": "pure-cli", "core_layer_tested": True,
        "claims": [
            {"id": "c1", "priority": "critical", "status": "passed"},
            {"id": "c2", "priority": "critical", "status": "failed"},
            {"id": "c3", "priority": "high", "status": "passed"},
        ],
        "stars": 1_000, "has_license": True,
    })
    assert bad["confidence"] == "high"

    full = compute_verdict({
        "repo": "x/y", "archetype": "pure-cli", "core_layer_tested": True,
        "evidence_completeness": "full",
        "claims": [
            {"id": "c1", "priority": "critical", "status": "passed"},
            {"id": "c2", "priority": "critical", "status": "passed"},
            {"id": "c3", "priority": "high", "status": "passed"},
        ],
        "stars": 1_000, "has_license": True,
    })
    assert full["confidence"] == "high"


def test_score_tier_thresholds():
    """Tier boundaries match docs: 90/80/70/60/40/0."""
    from verdict_calculator import tier_for_score
    assert tier_for_score(95)["key"] == "recommend"
    assert tier_for_score(85)["key"] == "team"
    assert tier_for_score(75)["key"] == "self"
    assert tier_for_score(65)["key"] == "try"
    assert tier_for_score(50)["key"] == "risky"
    assert tier_for_score(20)["key"] == "broken"
    # Boundary checks
    assert tier_for_score(90)["key"] == "recommend"
    assert tier_for_score(89)["key"] == "team"
    assert tier_for_score(60)["key"] == "try"
    assert tier_for_score(59)["key"] == "risky"
    assert tier_for_score(40)["key"] == "risky"
    assert tier_for_score(39)["key"] == "broken"


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
