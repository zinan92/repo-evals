"""
Tests for scripts/archetypes.py and the archetype scaffolding contract.

Covers:
  - all six Phase-2 archetypes exist with the three required files
  - every archetype.yaml has the required metadata fields
  - every claim-map.yaml has at least one critical claim and every claim
    is `status: untested` (starter status)
  - the `name` field matches the directory name
  - hybrid-cap archetypes declared in verdict_calculator.HYBRID_ARCHETYPES
    actually exist on disk
  - fixture registry's applicable_archetypes enum lists every archetype
    that exists on disk (catch drift between registry and archetypes/)
  - new-repo-eval.sh --archetype scaffolds archetype-specific files

Run:
    python3 tests/test_archetypes.py
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import archetypes as arch  # noqa: E402
import fixtures as fx  # noqa: E402
import verdict_calculator as vc  # noqa: E402
import yaml  # noqa: E402


PHASE2_ARCHETYPES = {
    "pure-cli",
    "prompt-skill",
    "hybrid-skill",
    "adapter",
    "orchestrator",
    "api-service",
}


# --- Structural invariants --------------------------------------------------


def test_all_phase2_archetypes_present():
    dirs = {p.name for p in arch.list_archetypes()}
    missing = PHASE2_ARCHETYPES - dirs
    assert not missing, f"missing archetypes: {sorted(missing)}"


def test_every_archetype_has_required_files():
    for d in arch.list_archetypes():
        for required in ("archetype.yaml", "claim-map.yaml", "eval-plan.md"):
            assert (d / required).exists(), f"{d.name}: missing {required}"


def test_validate_all_is_clean():
    problems = arch.validate_all()
    assert problems == [], f"archetype validation problems: {problems}"


def test_archetype_name_matches_directory():
    for d in arch.list_archetypes():
        meta = arch.load_metadata(d)
        assert meta["name"] == d.name, (
            f"{d.name}: archetype.yaml name is {meta['name']!r}"
        )


def test_every_archetype_has_at_least_one_critical_claim():
    for d in arch.list_archetypes():
        cm = yaml.safe_load((d / "claim-map.yaml").read_text())
        criticals = [c for c in cm["claims"] if c.get("priority") == "critical"]
        assert criticals, f"{d.name}: no critical claims"


def test_every_starter_claim_is_untested():
    for d in arch.list_archetypes():
        cm = yaml.safe_load((d / "claim-map.yaml").read_text())
        for c in cm["claims"]:
            assert c.get("status") == "untested", (
                f"{d.name}: claim {c.get('id')} is {c.get('status')!r}, "
                "starter claim maps must all be untested"
            )


# --- Cross-file invariants --------------------------------------------------


def test_hybrid_archetypes_in_calculator_exist_on_disk():
    dirs = {p.name for p in arch.list_archetypes()}
    missing = vc.HYBRID_ARCHETYPES - dirs
    assert not missing, (
        f"verdict_calculator.HYBRID_ARCHETYPES lists archetypes with no "
        f"scaffold on disk: {sorted(missing)}"
    )


def test_fixture_registry_enum_covers_every_archetype():
    data = fx.load_registry()
    enum_list = set(data.get("enums", {}).get("applicable_archetypes", []))
    dirs = {p.name for p in arch.list_archetypes()}
    missing = dirs - enum_list
    assert not missing, (
        f"fixtures/registry.yaml enums.applicable_archetypes is missing: "
        f"{sorted(missing)}"
    )


def test_verdict_calculator_applies_hybrid_ceiling_for_hybrid_archetypes():
    """Smoke-check that every hybrid archetype actually triggers the
    hybrid-repo rule message when core_layer_tested=False."""
    for name in vc.HYBRID_ARCHETYPES:
        rec = vc.compute_verdict({
            "archetype": name,
            "core_layer_tested": False,
            "evidence_completeness": "full",
            "claims": [
                {"id": "c1", "priority": "critical", "status": "passed"},
            ],
        })
        assert rec["recommended_bucket"] == "usable"
        assert any(
            "hybrid-repo rule" in r for r in rec["ceiling_reasons"]
        ), f"archetype {name} did not surface the hybrid-repo rule"


# --- Scaffolding integration (new-repo-eval.sh --archetype) ----------------


def test_new_repo_eval_with_archetype_scaffolds_archetype_files():
    # Safe because the script is idempotent and the slug is test-scoped.
    slug = "test--archetype-scaffold"
    repo_dir = ROOT / "repos" / slug
    # Guarantee clean starting state
    shutil.rmtree(repo_dir, ignore_errors=True)
    try:
        subprocess.run(
            [
                str(ROOT / "scripts" / "new-repo-eval.sh"),
                "test/archetype-scaffold",
                "skill",
                "--archetype",
                "adapter",
            ],
            check=True,
            cwd=ROOT,
            capture_output=True,
        )
        repo_yaml = yaml.safe_load((repo_dir / "repo.yaml").read_text())
        assert repo_yaml["archetype"] == "adapter"

        claim_map = yaml.safe_load((repo_dir / "claims" / "claim-map.yaml").read_text())
        # The starter should include an adapter-specific claim id we know
        # from archetypes/adapter/claim-map.yaml
        ids = [c["id"] for c in claim_map["claims"]]
        assert "claim-001" in ids
        # And at least one of the adapter claims should mention
        # "platform" or "adapter" in its title — that's the smell test
        titles = " ".join(str(c.get("title", "")) for c in claim_map["claims"])
        assert ("平台" in titles) or ("platform" in titles.lower()) or ("adapter" in titles.lower())

        # Plan should be the archetype's plan, not the generic one
        plans = list((repo_dir / "plans").glob("*-eval-plan.md"))
        assert plans, "no plan created"
        plan_text = plans[0].read_text()
        assert "Eval Plan — adapter" in plan_text, (
            "plan file is not the archetype-specific one"
        )
    finally:
        shutil.rmtree(repo_dir, ignore_errors=True)


def test_new_repo_eval_without_archetype_still_works():
    """Backward compat: no --archetype flag → generic templates, archetype field stays 'unknown'."""
    slug = "test--generic-scaffold"
    repo_dir = ROOT / "repos" / slug
    shutil.rmtree(repo_dir, ignore_errors=True)
    try:
        subprocess.run(
            [
                str(ROOT / "scripts" / "new-repo-eval.sh"),
                "test/generic-scaffold",
            ],
            check=True,
            cwd=ROOT,
            capture_output=True,
        )
        repo_yaml = yaml.safe_load((repo_dir / "repo.yaml").read_text())
        assert repo_yaml["archetype"] == "unknown"
        claim_map = yaml.safe_load((repo_dir / "claims" / "claim-map.yaml").read_text())
        # Generic template has one placeholder claim
        assert claim_map["claims"][0]["id"] == "claim-001"
        assert claim_map["claims"][0]["title"] == "Main claim"
    finally:
        shutil.rmtree(repo_dir, ignore_errors=True)


def test_unknown_archetype_is_rejected():
    slug = "test--bad-archetype"
    repo_dir = ROOT / "repos" / slug
    shutil.rmtree(repo_dir, ignore_errors=True)
    try:
        result = subprocess.run(
            [
                str(ROOT / "scripts" / "new-repo-eval.sh"),
                "test/bad-archetype",
                "skill",
                "--archetype",
                "not-a-real-archetype",
            ],
            cwd=ROOT,
            capture_output=True,
        )
        assert result.returncode != 0, "expected failure on unknown archetype"
        # The repo should NOT have been created on rejection
        assert not repo_dir.exists(), "repo dir was created despite bad archetype"
    finally:
        shutil.rmtree(repo_dir, ignore_errors=True)


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
