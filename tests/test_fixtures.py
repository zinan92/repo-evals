"""
Tests for scripts/fixtures.py — the shared fixture registry CLI.

Covers:
  - schema validation catches bad entries
  - filtering by archetype / media_type / language
  - duplicate id detection
  - registry: reference resolution from run-summary.yaml
  - in-repo location existence check

Run:
    python3 tests/test_fixtures.py
    # or
    python3 -m pytest tests/test_fixtures.py -v
"""

from __future__ import annotations

import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fixtures as fx  # noqa: E402


# --- Real-registry sanity --------------------------------------------------


def test_real_registry_validates():
    data = fx.load_registry()
    problems = fx.validate(data)
    assert problems == [], f"real registry has problems: {problems}"


def test_real_registry_has_known_ids():
    data = fx.load_registry()
    idx = fx.index(data)
    # Smoke check the bootstrap fixtures are present
    for fid in (
        "markdown-readme-small-en",
        "html-slide-deck-minimal",
        "json-content-item-valid",
    ):
        assert fid in idx, f"missing bootstrap fixture: {fid}"


def test_real_registry_in_repo_assets_exist():
    data = fx.load_registry()
    for e in data["fixtures"]:
        loc = str(e["location"])
        if not loc.startswith(("external:", "http://", "https://")):
            assert (ROOT / loc).exists(), f"{e['id']}: missing asset at {loc}"


# --- Synthetic registries for validation logic -----------------------------


def _mk_data(fixtures_list, *, enums=None):
    return {
        "registry_version": 1,
        "enums": enums or {
            "media_type": ["markdown", "json"],
            "complexity": ["simple", "moderate"],
            "privacy": ["public", "synthetic"],
            "applicable_archetypes": ["pure-cli", "hybrid-skill"],
        },
        "fixtures": fixtures_list,
    }


def _good(**overrides):
    base = {
        "id": "good-1",
        "description": "ok",
        "media_type": "markdown",
        "language": "en",
        "complexity": "simple",
        "applicable_archetypes": ["pure-cli"],
        "privacy": "synthetic",
        "location": "external:https://example.test/x",
        "added_at": "2026-04-07",
    }
    base.update(overrides)
    return base


def test_validate_catches_missing_fields():
    data = _mk_data([{"id": "incomplete", "media_type": "markdown"}])
    problems = fx.validate(data)
    assert any("missing fields" in p for p in problems)


def test_validate_catches_unknown_media_type():
    data = _mk_data([_good(media_type="chatbot")])
    problems = fx.validate(data)
    assert any("unknown media_type" in p for p in problems)


def test_validate_catches_unknown_archetype():
    data = _mk_data([_good(applicable_archetypes=["magical-unicorn"])])
    problems = fx.validate(data)
    assert any("unknown archetypes" in p for p in problems)


def test_validate_catches_empty_archetype_list():
    data = _mk_data([_good(applicable_archetypes=[])])
    problems = fx.validate(data)
    assert any("applicable_archetypes" in p for p in problems)


def test_validate_catches_duplicate_ids():
    data = _mk_data([_good(id="dup"), _good(id="dup")])
    problems = fx.validate(data)
    assert any("duplicate" in p for p in problems)


def test_validate_catches_missing_in_repo_file():
    data = _mk_data([_good(location="fixtures/assets/does-not-exist.md")])
    problems = fx.validate(data)
    assert any("in-repo location does not exist" in p for p in problems)


def test_validate_passes_external_location_without_filesystem_check():
    data = _mk_data([_good(location="external:https://still-ok.test/z")])
    assert fx.validate(data) == []


# --- Filtering -------------------------------------------------------------


def test_filter_by_archetype():
    data = _mk_data([
        _good(id="md-cli", applicable_archetypes=["pure-cli"]),
        _good(id="md-hybrid", applicable_archetypes=["hybrid-skill"]),
    ])
    out = fx.filter_fixtures(data, archetype="hybrid-skill")
    assert [e["id"] for e in out] == ["md-hybrid"]


def test_filter_by_media_type_and_language():
    data = _mk_data([
        _good(id="md-en", media_type="markdown", language="en"),
        _good(id="md-zh", media_type="markdown", language="zh"),
        _good(id="json-en", media_type="json", language="en"),
    ])
    out = fx.filter_fixtures(data, media_type="markdown", language="en")
    assert [e["id"] for e in out] == ["md-en"]


def test_filter_returns_all_when_no_constraints():
    data = _mk_data([_good(id="a"), _good(id="b")])
    assert len(fx.filter_fixtures(data)) == 2


# --- Reference checking ----------------------------------------------------


def test_extract_registry_refs_handles_mixed_fixture_list():
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(
            "fixtures:\n"
            "  - \"registry:markdown-readme-small-en\"\n"
            "  - \"local: repos/x/fixtures/my.txt\"\n"
            "  - \"registry:json-content-item-valid\"\n"
        )
        path = pathlib.Path(f.name)
    try:
        refs = fx.extract_registry_refs(path)
        assert refs == ["markdown-readme-small-en", "json-content-item-valid"]
    finally:
        path.unlink()


def test_check_refs_flags_unknown_ids():
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(
            "fixtures:\n"
            "  - \"registry:markdown-readme-small-en\"\n"
            "  - \"registry:totally-made-up-id\"\n"
        )
        path = pathlib.Path(f.name)
    try:
        missing = fx.check_refs(path)
        assert "totally-made-up-id" in missing
        assert "markdown-readme-small-en" not in missing
    finally:
        path.unlink()


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
