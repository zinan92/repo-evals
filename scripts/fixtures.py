#!/usr/bin/env python3
"""
fixtures.py — discovery and validation CLI for the shared fixture registry.

Usage:
    scripts/fixtures.py list                               # one-line summary
    scripts/fixtures.py list --archetype hybrid-skill      # filter by archetype
    scripts/fixtures.py list --media-type markdown         # filter by media
    scripts/fixtures.py show <id>                          # full detail
    scripts/fixtures.py find --lang en --complexity simple # multi-filter
    scripts/fixtures.py validate                           # schema check
    scripts/fixtures.py check-refs <run-summary.yaml>      # verify registry:<id>
                                                           #   references resolve

The registry is intentionally file-based (fixtures/registry.yaml) so that:
  - Git remains the source of truth
  - Fixtures can be reviewed in PRs
  - Any agent or human can read the catalog without running this script

This CLI is a convenience layer on top of that file, not a replacement.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("fixtures.py: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "fixtures" / "registry.yaml"


# --- Loading --------------------------------------------------------------


class RegistryError(ValueError):
    pass


def load_registry(path: pathlib.Path = REGISTRY_PATH) -> dict:
    if not path.exists():
        raise RegistryError(f"registry not found: {path}")
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or "fixtures" not in data:
        raise RegistryError("registry.yaml must be a mapping with a 'fixtures' list")
    if not isinstance(data["fixtures"], list):
        raise RegistryError("registry.yaml 'fixtures' must be a list")
    return data


def index(data: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for entry in data["fixtures"]:
        if not isinstance(entry, dict) or "id" not in entry:
            raise RegistryError(f"fixture entry missing id: {entry!r}")
        fid = entry["id"]
        if fid in out:
            raise RegistryError(f"duplicate fixture id: {fid}")
        out[fid] = entry
    return out


# --- Validation -----------------------------------------------------------


REQUIRED_FIELDS = {
    "id",
    "description",
    "media_type",
    "language",
    "complexity",
    "applicable_archetypes",
    "privacy",
    "location",
    "added_at",
}


def validate(data: dict) -> list[str]:
    """Return a list of problems found; empty list = OK."""
    problems: list[str] = []
    enums = data.get("enums", {}) or {}
    allowed_media = set(enums.get("media_type", []))
    allowed_complexity = set(enums.get("complexity", []))
    allowed_privacy = set(enums.get("privacy", []))
    allowed_archetypes = set(enums.get("applicable_archetypes", []))

    ids_seen: set[str] = set()
    for entry in data.get("fixtures", []):
        fid = entry.get("id", "<no id>")
        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            problems.append(f"{fid}: missing fields {sorted(missing)}")
            continue
        if fid in ids_seen:
            problems.append(f"{fid}: duplicate id")
        ids_seen.add(fid)

        if allowed_media and entry["media_type"] not in allowed_media:
            problems.append(f"{fid}: unknown media_type '{entry['media_type']}'")
        if allowed_complexity and entry["complexity"] not in allowed_complexity:
            problems.append(f"{fid}: unknown complexity '{entry['complexity']}'")
        if allowed_privacy and entry["privacy"] not in allowed_privacy:
            problems.append(f"{fid}: unknown privacy '{entry['privacy']}'")

        archs = entry["applicable_archetypes"]
        if not isinstance(archs, list) or not archs:
            problems.append(f"{fid}: applicable_archetypes must be a non-empty list")
        elif allowed_archetypes:
            bad = [a for a in archs if a not in allowed_archetypes]
            if bad:
                problems.append(f"{fid}: unknown archetypes {bad}")

        # If location points into this repo, make sure the file exists.
        loc = str(entry["location"])
        if not loc.startswith(("external:", "http://", "https://")):
            p = ROOT / loc
            if not p.exists():
                problems.append(f"{fid}: in-repo location does not exist: {loc}")
    return problems


# --- Filtering ------------------------------------------------------------


def filter_fixtures(
    data: dict,
    *,
    archetype: str | None = None,
    media_type: str | None = None,
    language: str | None = None,
    complexity: str | None = None,
    privacy: str | None = None,
) -> list[dict]:
    out = []
    for entry in data["fixtures"]:
        if archetype and archetype not in (entry.get("applicable_archetypes") or []):
            continue
        if media_type and entry.get("media_type") != media_type:
            continue
        if language and entry.get("language") != language:
            continue
        if complexity and entry.get("complexity") != complexity:
            continue
        if privacy and entry.get("privacy") != privacy:
            continue
        out.append(entry)
    return out


# --- run-summary reference check -----------------------------------------


def extract_registry_refs(run_summary_path: pathlib.Path) -> list[str]:
    data = yaml.safe_load(run_summary_path.read_text()) or {}
    fixtures = data.get("fixtures") or []
    refs: list[str] = []
    for item in fixtures:
        if isinstance(item, str) and item.startswith("registry:"):
            refs.append(item.split(":", 1)[1].strip())
    return refs


def check_refs(run_summary_path: pathlib.Path) -> list[str]:
    data = load_registry()
    ids = set(index(data).keys())
    refs = extract_registry_refs(run_summary_path)
    return [r for r in refs if r not in ids]


# --- Rendering ------------------------------------------------------------


def short_line(e: dict) -> str:
    return (
        f"{e['id']:38s}  "
        f"{e['media_type']:9s}  "
        f"{e['language']:3s}  "
        f"{e['complexity']:9s}  "
        f"{e['privacy']:10s}  "
        f"{','.join(e.get('applicable_archetypes', []))}"
    )


def render_show(e: dict) -> str:
    lines = [
        f"id:            {e['id']}",
        f"media_type:    {e['media_type']}",
        f"language:      {e['language']}",
        f"complexity:    {e['complexity']}",
        f"privacy:       {e['privacy']}",
        f"archetypes:    {', '.join(e.get('applicable_archetypes', []))}",
        f"location:      {e['location']}",
        f"added_at:      {e['added_at']}",
        "",
        "description:",
    ]
    for ln in str(e.get("description", "")).strip().splitlines():
        lines.append(f"  {ln}")
    if e.get("known_caveats"):
        lines += ["", "known_caveats:"]
        for ln in str(e["known_caveats"]).strip().splitlines():
            lines.append(f"  {ln}")
    return "\n".join(lines) + "\n"


# --- CLI ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="list all fixtures, one per line")
    p_list.add_argument("--archetype")
    p_list.add_argument("--media-type")
    p_list.add_argument("--language")
    p_list.add_argument("--complexity")
    p_list.add_argument("--privacy")
    p_list.add_argument("--json", action="store_true")

    p_show = sub.add_parser("show", help="show one fixture in detail")
    p_show.add_argument("id")
    p_show.add_argument("--json", action="store_true")

    p_find = sub.add_parser("find", help="alias for `list` with filters")
    p_find.add_argument("--archetype")
    p_find.add_argument("--media-type")
    p_find.add_argument("--language")
    p_find.add_argument("--complexity")
    p_find.add_argument("--privacy")
    p_find.add_argument("--json", action="store_true")

    sub.add_parser("validate", help="schema-check the registry")

    p_refs = sub.add_parser("check-refs", help="verify registry:<id> refs in a run-summary")
    p_refs.add_argument("run_summary", type=pathlib.Path)

    args = parser.parse_args(argv)

    try:
        data = load_registry()
    except RegistryError as e:
        print(f"fixtures: {e}", file=sys.stderr)
        return 1

    if args.cmd in ("list", "find"):
        entries = filter_fixtures(
            data,
            archetype=getattr(args, "archetype", None),
            media_type=getattr(args, "media_type", None),
            language=getattr(args, "language", None),
            complexity=getattr(args, "complexity", None),
            privacy=getattr(args, "privacy", None),
        )
        if getattr(args, "json", False):
            print(json.dumps(entries, indent=2, ensure_ascii=False))
        else:
            if not entries:
                print("(no matches)")
                return 0
            print(f"{'id':38s}  {'media':9s}  {'lng':3s}  {'complex':9s}  {'privacy':10s}  archetypes")
            print("-" * 110)
            for e in entries:
                print(short_line(e))
        return 0

    if args.cmd == "show":
        idx = index(data)
        if args.id not in idx:
            print(f"no such fixture: {args.id}", file=sys.stderr)
            return 1
        e = idx[args.id]
        if args.json:
            print(json.dumps(e, indent=2, ensure_ascii=False))
        else:
            sys.stdout.write(render_show(e))
        return 0

    if args.cmd == "validate":
        problems = validate(data)
        if not problems:
            print(f"OK: {len(data['fixtures'])} fixtures, no problems")
            return 0
        print("FAIL:")
        for p in problems:
            print(f"  - {p}")
        return 1

    if args.cmd == "check-refs":
        if not args.run_summary.exists():
            print(f"no such run-summary: {args.run_summary}", file=sys.stderr)
            return 1
        missing = check_refs(args.run_summary)
        if not missing:
            print(f"OK: all registry refs in {args.run_summary} resolve")
            return 0
        print("FAIL: unresolved registry refs:")
        for m in missing:
            print(f"  - registry:{m}")
        return 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
