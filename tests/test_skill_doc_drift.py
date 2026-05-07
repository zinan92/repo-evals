"""
Tests that catch drift between framework code and the user-facing docs/templates.

The pattern these tests guard against:
  - Someone updates `scripts/verdict_calculator.py` (e.g. adds a tier,
    renames a category, changes the score base) but forgets to update
    SKILL.md or templates/repo/repo.yaml.
  - The skill keeps shipping the old vocabulary. Claude Code loads stale
    instructions when invoking the skill, produces broken output.
  - The bug only surfaces when someone actually runs `/repo-evals` —
    days or weeks later.

These tests run on every CI build and force the doc/template update to
land in the same PR as the code change.

Run:
    python3 -m pytest tests/test_skill_doc_drift.py -v
or (if pytest not available):
    python3 tests/test_skill_doc_drift.py
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verdict_calculator import (  # noqa: E402
    CATEGORIES,
    SCORE_BASE,
    SCORE_ECOSYSTEM_CAP,
    SCORE_MAINTAINER_CAP,
    SCORE_STATIC_CAP,
    TIERS,
)


SKILL_MD = (ROOT / "SKILL.md").read_text(encoding="utf-8")
TEMPLATE_REPO_YAML = (ROOT / "templates" / "repo" / "repo.yaml").read_text(
    encoding="utf-8"
)
TEMPLATE_CLAIM_MAP = (ROOT / "templates" / "repo" / "claim-map.yaml").read_text(
    encoding="utf-8"
)
TEMPLATE_FINAL_VERDICT = (ROOT / "templates" / "repo" / "final-verdict.md").read_text(
    encoding="utf-8"
)


# --- Score model constants must surface in SKILL.md ----------------------


def test_skill_md_mentions_score_base():
    """SKILL.md must reference the actual SCORE_BASE constant.

    If you change SCORE_BASE in verdict_calculator.py, you must also
    update the additive-score formula block in SKILL.md.
    """
    assert str(SCORE_BASE) in SKILL_MD, (
        f"SKILL.md does not mention SCORE_BASE={SCORE_BASE}. "
        f"If you changed the score base, update the formula block in SKILL.md."
    )


def test_skill_md_mentions_static_cap():
    """SKILL.md must reference the static-eval cap."""
    cap = str(SCORE_STATIC_CAP)
    assert cap in SKILL_MD, (
        f"SKILL.md does not mention SCORE_STATIC_CAP={cap}. "
        f"If you changed the cap, update the additive-score block in SKILL.md."
    )


def test_skill_md_mentions_maintainer_and_ecosystem_caps():
    """Both ±15 caps must appear in SKILL.md (as ±15 or 15 in the formula)."""
    for cap, name in (
        (SCORE_MAINTAINER_CAP, "SCORE_MAINTAINER_CAP"),
        (SCORE_ECOSYSTEM_CAP, "SCORE_ECOSYSTEM_CAP"),
    ):
        assert str(cap) in SKILL_MD, (
            f"SKILL.md does not mention {name}={cap}. Update the formula block."
        )


# --- Every tier must surface in SKILL.md ----------------------------------


def test_skill_md_lists_all_tiers():
    """Every tier defined in verdict_calculator.TIERS must appear in SKILL.md.

    Either the EN label or the ZH label is enough — but at least one
    representation must be there. If you add a tier and forget to update
    SKILL.md, this test fails.
    """
    missing = []
    for tier in TIERS:
        en = str(tier["en"])
        zh = str(tier["zh"])
        if en not in SKILL_MD and zh not in SKILL_MD:
            missing.append(f"{tier['key']} ({en} / {zh})")
    assert not missing, (
        f"SKILL.md is missing tier(s): {missing}. "
        f"If you renamed or added a tier in verdict_calculator.TIERS, "
        f"reflect it in the SKILL.md tier table."
    )


# --- Every category must surface in SKILL.md ------------------------------


def test_skill_md_lists_all_categories():
    """Every display category from verdict_calculator.CATEGORIES must appear."""
    missing = []
    for cat in CATEGORIES:
        en = str(cat.get("en", ""))
        zh = str(cat.get("zh", ""))
        if en and en not in SKILL_MD and (not zh or zh not in SKILL_MD):
            missing.append(f"{cat.get('key')} ({en} / {zh})")
    assert not missing, (
        f"SKILL.md is missing category/categories: {missing}. "
        f"Update the 4-category table in SKILL.md."
    )


# --- Required dossier fields must be in the template ----------------------


REQUIRED_REPO_YAML_FIELDS = (
    # Identity / status
    "owner", "repo", "display_name", "repo_url", "repo_type",
    "archetype", "layer", "complexity", "status",
    # Score-model inputs (drive the 0-100 score)
    "stars", "archived", "has_license", "multilingual_readme",
    "release_pipeline_score", "eval_discipline_score", "recently_active",
    # Top-level dossier sections
    "product_view",
    "deployment", "third_party_services", "workflow_placements",
    "workflow_diagram",     # drives Atom/Molecule/Compound section
    "similar_repos",        # drives "对比我们已经测评过的"
    # product_view sub-fields (drive specific dossier sections)
    "one_liner",            # always shown — top of dossier
    "persona",              # drives "谁用"
    "scenario",             # drives "什么时候用"
    "without_this",         # drives without/with comparison
    "with_this",            # same comparison block
    "how",                  # drives "怎么用"
    "examples",             # drives "三个真实场景里怎么唤醒"
    "next_step",            # drives "提升评分的下一步"
)


def test_repo_yaml_template_has_score_input_fields():
    """templates/repo/repo.yaml must scaffold every field the score model
    reads. If a new field gets added to compute_score(), it must show up
    in the template (at least as a commented-out section) so new evals
    don't ship broken dossier output."""
    missing = [f for f in REQUIRED_REPO_YAML_FIELDS if f not in TEMPLATE_REPO_YAML]
    assert not missing, (
        f"templates/repo/repo.yaml is missing field(s): {missing}. "
        f"Add scaffolding for these in the template, even if commented out."
    )


# --- claim-map template must teach the user view --------------------------


REQUIRED_CLAIM_USER_VIEW_KEYS = (
    "user_icon", "user_title", "user_description",
)


def test_claim_map_template_teaches_user_view():
    """SKILL.md says every claim MUST have user_icon + user_title +
    user_description. The starter template must show those fields, or
    new evals won't include them."""
    missing = [k for k in REQUIRED_CLAIM_USER_VIEW_KEYS if k not in TEMPLATE_CLAIM_MAP]
    assert not missing, (
        f"templates/repo/claim-map.yaml is missing user_view key(s): {missing}. "
        f"Update the starter template to include the user view."
    )


def test_archetype_claim_maps_teach_user_view():
    """Same constraint applies to every archetype's starter claim-map.
    new-repo-eval.sh --archetype X copies these, not templates/repo/."""
    missing_per_archetype = {}
    for path in sorted((ROOT / "archetypes").glob("*/claim-map.yaml")):
        text = path.read_text(encoding="utf-8")
        missing = [k for k in REQUIRED_CLAIM_USER_VIEW_KEYS if k not in text]
        if missing:
            missing_per_archetype[path.parent.name] = missing
    assert not missing_per_archetype, (
        f"Archetype claim-maps missing user_view: {missing_per_archetype}. "
        f"Add user_icon/user_title/user_description to each starter claim."
    )


# --- final-verdict template must use score language -----------------------


def test_final_verdict_template_uses_score_vocabulary():
    """The final-verdict.md scaffold must reference Score, not just bucket."""
    assert "Score" in TEMPLATE_FINAL_VERDICT, (
        "templates/repo/final-verdict.md should reference 'Score' (0-100). "
        "If you reverted to bucket-only language, update the template."
    )
    assert "Category" in TEMPLATE_FINAL_VERDICT, (
        "templates/repo/final-verdict.md should reference 'Category' "
        "(production/available/risky/dont_use)."
    )


# --- Standalone runner ----------------------------------------------------


if __name__ == "__main__":
    import traceback

    tests = [
        test_skill_md_mentions_score_base,
        test_skill_md_mentions_static_cap,
        test_skill_md_mentions_maintainer_and_ecosystem_caps,
        test_skill_md_lists_all_tiers,
        test_skill_md_lists_all_categories,
        test_repo_yaml_template_has_score_input_fields,
        test_claim_map_template_teaches_user_view,
        test_archetype_claim_maps_teach_user_view,
        test_final_verdict_template_uses_score_vocabulary,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
        except Exception:
            failed += 1
            print(f"ERROR {fn.__name__}:")
            traceback.print_exc()
    if failed:
        print(f"\n{failed} test(s) failed")
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed")
