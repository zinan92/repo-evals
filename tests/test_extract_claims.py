"""
Tests for scripts/extract_claims.py — the conservative claim extractor.
"""

from __future__ import annotations

import pathlib
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import extract_claims as ex  # noqa: E402


# --- Synthetic repo helper -------------------------------------------------


def _mk_repo(tmp: pathlib.Path, files: dict[str, str]) -> pathlib.Path:
    repo = tmp / "target"
    repo.mkdir()
    for path, content in files.items():
        p = repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return repo


def _rules(claims):
    return [c.extractor_rule for c in claims]


# --- Feature section bullets -----------------------------------------------


README_FEATURES = """\
# Demo

## Features

- Downloads videos from 4 platforms
- Parses metadata into a stable shape
- Fails clearly on unknown input

## Installation

- pip install demo
- Run `demo --help` to get started
"""


def test_features_section_yields_feature_bullets():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": README_FEATURES})
        claims = ex.run(repo)
        feature_claims = [c for c in claims if c.extractor_rule == "feature_bullet"]
        titles = {c.title for c in feature_claims}
        assert "Downloads videos from 4 platforms" in titles
        assert "Fails clearly on unknown input" in titles


def test_installation_bullets_are_excluded():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": README_FEATURES})
        claims = ex.run(repo)
        titles = {c.title for c in claims}
        # Nothing from the Installation section should show up as a claim
        assert not any("pip install" in t for t in titles)
        assert not any("demo --help" in t for t in titles)


def test_feature_bullets_default_to_high_priority_or_higher():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": README_FEATURES})
        claims = [
            c for c in ex.run(repo) if c.extractor_rule == "feature_bullet"
        ]
        for c in claims:
            assert c.priority in ("critical", "high")


def test_verbs_like_download_promote_to_critical():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": README_FEATURES})
        claims = ex.run(repo)
        download_claim = next(
            c for c in claims if "downloads videos" in c.title.lower()
        )
        assert download_claim.priority == "critical"


# --- Commands table --------------------------------------------------------


README_COMMANDS = """\
# Demo

## Commands

| Command | Description |
|---------|-------------|
| `demo list` | List known items |
| `demo show <id>` | Show one item |
"""


def test_commands_table_extracts_each_row():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": README_COMMANDS})
        claims = ex.run(repo)
        command_claims = [c for c in claims if c.extractor_rule == "command_table_row"]
        titles = " ".join(c.title for c in command_claims)
        assert "demo list" in titles
        assert "demo show <id>" in titles


def test_commands_table_separator_is_not_a_claim():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": README_COMMANDS})
        claims = ex.run(repo)
        command_claims = [c for c in claims if c.extractor_rule == "command_table_row"]
        assert len(command_claims) == 2  # exactly two data rows


# --- Numeric regex --------------------------------------------------------


def test_numeric_claim_supports_n_pattern():
    text = "# Demo\n\n## Features\n- supports 4 platforms\n"
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": text})
        claims = ex.run(repo)
        numeric = [c for c in claims if c.extractor_rule == "numeric_claim_regex"]
        assert any("4" in c.statement for c in numeric)


def test_numeric_claim_handles_up_to_pattern():
    text = "# Demo\n\n## Features\n- handles up to 10 MB files\n"
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": text})
        claims = ex.run(repo)
        numeric = [c for c in claims if c.extractor_rule == "numeric_claim_regex"]
        assert numeric


# --- Excluded sections ---------------------------------------------------


def test_license_and_contributing_are_excluded():
    text = """\
# Demo

## License

- MIT
- Copyright 2026

## Contributing

- Fork the repo
- Open a PR
"""
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": text})
        claims = ex.run(repo)
        titles = " ".join(c.title for c in claims)
        assert "MIT" not in titles
        assert "Fork the repo" not in titles


# --- Case-insensitive filesystem dedup (the macOS bug) ------------------


def test_readme_is_only_processed_once_on_case_insensitive_fs():
    text = "# Demo\n\n## Features\n- does the thing\n"
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": text})
        # On macOS's default HFS+/APFS, README.md / Readme.md / readme.md
        # all point to the same file. We verify dedup works even in that
        # case — the same text should not produce 3 copies of the same
        # extraction.
        sources = ex.discover_sources(repo, None)
        # There should be exactly one entry per actual inode
        inodes = {p.stat().st_ino for p in sources}
        assert len(sources) == len(inodes), (
            f"discover_sources returned duplicates: {[str(p) for p in sources]}"
        )


# --- Dedupe --------------------------------------------------------------


def test_dedupe_prefers_higher_confidence():
    a = ex.DraftClaim(
        title="same", statement="same", source="README.md", source_ref="x",
        confidence="low", extractor_rule="generic_section_bullet",
    )
    b = ex.DraftClaim(
        title="same", statement="same", source="README.md", source_ref="x",
        confidence="high", extractor_rule="feature_bullet",
    )
    result = ex.dedupe([a, b])
    assert len(result) == 1
    assert result[0].confidence == "high"


# --- YAML output ---------------------------------------------------------


def test_yaml_output_has_auto_extracted_header():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": README_FEATURES})
        claims = ex.run(repo)
        out = ex.to_yaml(claims)
        assert "AUTO-EXTRACTED" in out
        assert "needs_review" in out


def test_yaml_output_every_claim_has_required_fields():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": README_FEATURES})
        claims = ex.run(repo)
        out = ex.to_yaml(claims)
        parsed = yaml.safe_load(out)
        assert "claims" in parsed
        for c in parsed["claims"]:
            for required in (
                "id", "title", "source", "priority", "area",
                "status", "needs_review", "confidence", "extractor_rule",
            ):
                assert required in c, f"missing {required} in {c}"
            assert c["status"] == "untested"
            assert c["needs_review"] is True


def test_yaml_output_is_parseable_as_claim_map():
    """Guarantees the extractor's draft can be fed straight to the
    coverage gap detector."""
    import coverage_gap_detector as cgd  # noqa: E402

    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"README.md": README_FEATURES})
        draft = ex.to_yaml(ex.run(repo))
        # Write into a fake repo dir and check coverage-gap-detector can load it
        fake = pathlib.Path(t) / "fake-repo"
        (fake / "claims").mkdir(parents=True)
        (fake / "claims" / "claim-map.yaml").write_text(draft)
        (fake / "repo.yaml").write_text("owner: x\nrepo: y\narchetype: pure-cli\n")
        claims = cgd.load_claim_map(fake)
        assert len(claims) >= 1


# --- Empty / no-source repo ----------------------------------------------


def test_repo_without_readme_returns_empty():
    with tempfile.TemporaryDirectory() as t:
        repo = _mk_repo(pathlib.Path(t), {"LICENSE": "MIT"})
        claims = ex.run(repo)
        assert claims == []


# --- Ad-hoc runner -------------------------------------------------------


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
