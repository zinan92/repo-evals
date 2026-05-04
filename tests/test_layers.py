"""Tests for scripts/layers.py and the layer-aware dashboard rendering.

Run:
    pytest tests/test_layers.py -q
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import layers  # noqa: E402
import yaml  # noqa: E402


# --- normalise_layer + applicable_levels ---------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("atom", "atom"),
        ("Atom", "atom"),
        (" molecule ", "molecule"),
        ("compound", "compound"),
        ("nope", "unknown"),
        (None, "unknown"),
        ("", "unknown"),
    ],
)
def test_normalise_layer(raw: str | None, expected: str) -> None:
    assert layers.normalise_layer(raw) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "layer, expected",
    [
        ("atom", ("atom",)),
        ("molecule", ("atom", "molecule")),
        ("compound", ("atom", "molecule", "compound")),
        ("unknown", ()),
        ("garbage", ()),
    ],
)
def test_applicable_levels_stack_correctly(layer: str, expected: tuple[str, ...]) -> None:
    assert layers.applicable_levels(layer) == expected


# --- archetype heuristic --------------------------------------------------


@pytest.mark.unit
def test_default_layer_for_archetype_covers_phase2_archetypes() -> None:
    """Every archetype shipped on disk must have a default layer mapping."""

    archetypes_dir = ROOT / "archetypes"
    on_disk = {
        path.name
        for path in archetypes_dir.iterdir()
        if path.is_dir() and (path / "archetype.yaml").exists()
    }
    for archetype in on_disk:
        assert layers.default_layer_for_archetype(archetype) in layers.LAYERS, (
            f"archetype {archetype!r} has no default layer mapping in layers.py"
        )


@pytest.mark.unit
def test_default_layer_for_unknown_archetype() -> None:
    assert layers.default_layer_for_archetype(None) == "unknown"
    assert layers.default_layer_for_archetype("not-a-real-archetype") == "unknown"


# --- dimensions -----------------------------------------------------------


@pytest.mark.unit
def test_each_level_has_at_least_three_dimensions() -> None:
    for level in layers.LAYERS:
        dims = layers.dimensions_for_level(level)
        assert len(dims) >= 3, f"{level} has only {len(dims)} dimensions"


@pytest.mark.unit
def test_dimension_keys_are_unique_within_level() -> None:
    for level in layers.LAYERS:
        keys = [d.key for d in layers.dimensions_for_level(level)]
        assert len(keys) == len(set(keys)), f"duplicate keys in {level}: {keys}"


# --- compound experiments -------------------------------------------------


@pytest.mark.unit
def test_experiments_only_for_compound() -> None:
    assert layers.experiments_for("atom", None) == ()
    assert layers.experiments_for("molecule", None) == ()
    assert layers.experiments_for("unknown", None) == ()


@pytest.mark.unit
def test_compound_experiments_have_required_bilingual_fields() -> None:
    experiments = layers.experiments_for("compound", "hybrid-skill")
    assert len(experiments) >= 3, "compound layer needs ≥3 generic experiments"
    for exp in experiments:
        # Each experiment must carry both en and zh content for every field.
        assert exp.title_en.strip() and exp.title_zh.strip()
        assert exp.system_prompt_en.strip() and exp.system_prompt_zh.strip()
        assert len(exp.watch_for_en) >= 2
        assert len(exp.watch_for_en) == len(exp.watch_for_zh), (
            f"watch_for length mismatch for {exp.title_en!r}: "
            f"en={len(exp.watch_for_en)} zh={len(exp.watch_for_zh)}"
        )
        assert exp.expected_sub_molecules_en.strip()
        assert exp.expected_sub_molecules_zh.strip()
        # The bilingual property accessors should expose both halves.
        assert exp.title["en"] and exp.title["zh"]
        assert exp.watch_for[0]["en"] and exp.watch_for[0]["zh"]


@pytest.mark.unit
def test_dimension_questions_are_bilingual() -> None:
    for level in layers.LAYERS:
        for d in layers.dimensions_for_level(level):
            assert d.question_en.strip(), f"{level}.{d.key} missing en question"
            assert d.question_zh.strip(), f"{level}.{d.key} missing zh question"
            assert d.question["en"] == d.question_en
            assert d.question["zh"] == d.question_zh


@pytest.mark.unit
def test_layer_label_is_bilingual_with_chinese_words() -> None:
    """Spot-check that the canonical Chinese terms are in the labels."""

    assert layers.layer_label("atom") == {"en": "Atom", "zh": "原子"}
    assert layers.layer_label("molecule") == {"en": "Molecule", "zh": "分子"}
    assert layers.layer_label("compound") == {"en": "Compound", "zh": "复合物"}


@pytest.mark.unit
def test_orchestrator_compound_gets_extra_experiments() -> None:
    generic = layers.experiments_for("compound", "hybrid-skill")
    orchestrator = layers.experiments_for("compound", "orchestrator")
    assert len(orchestrator) > len(generic), (
        "orchestrator should add archetype-specific compound experiments"
    )


# --- repo.yaml integration ------------------------------------------------


@pytest.mark.integration
def test_every_existing_repo_has_a_known_layer() -> None:
    """Every repos/*/repo.yaml must declare a layer (or fall back to known unknown)."""

    repos_dir = ROOT / "repos"
    for repo_dir in repos_dir.iterdir():
        repo_yaml = repo_dir / "repo.yaml"
        if not repo_yaml.exists():
            continue
        meta = yaml.safe_load(repo_yaml.read_text()) or {}
        normalised = layers.normalise_layer(meta.get("layer"))
        # Allow 'unknown' explicitly, but warn loudly if a repo has no
        # layer declared at all so we notice it on the next dashboard build.
        assert normalised in ("atom", "molecule", "compound", "unknown"), (
            f"{repo_dir.name}: layer field {meta.get('layer')!r} is malformed"
        )
