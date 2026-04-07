#!/usr/bin/env python3
"""
archetypes.py — discovery CLI for repo archetypes.

Usage:
    scripts/archetypes.py list                    # one line per archetype
    scripts/archetypes.py show <name>             # full detail
    scripts/archetypes.py show <name> --json      # JSON output
    scripts/archetypes.py validate                # schema-check every archetype

Archetypes live in archetypes/<name>/ and each has:
    archetype.yaml
    claim-map.yaml
    eval-plan.md

This CLI is the machine-readable layer on top of those files. The files
themselves remain the source of truth.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    print("archetypes.py: PyYAML is required", file=sys.stderr)
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARCH_DIR = ROOT / "archetypes"

REQUIRED_META_FIELDS = {
    "name",
    "description",
    "default_verdict_ceiling",
    "evaluation_dimensions",
    "recommended_evidence",
    "default_claim_prompts",
}

REQUIRED_FILES = ["archetype.yaml", "claim-map.yaml", "eval-plan.md"]


def list_archetypes() -> list[pathlib.Path]:
    if not ARCH_DIR.exists():
        return []
    return sorted(
        p for p in ARCH_DIR.iterdir()
        if p.is_dir() and (p / "archetype.yaml").exists()
    )


def load_metadata(archetype_dir: pathlib.Path) -> dict:
    path = archetype_dir / "archetype.yaml"
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path}: not a mapping")
    return data


def validate_one(archetype_dir: pathlib.Path) -> list[str]:
    problems: list[str] = []
    name = archetype_dir.name

    for required in REQUIRED_FILES:
        if not (archetype_dir / required).exists():
            problems.append(f"{name}: missing {required}")

    arch_yaml = archetype_dir / "archetype.yaml"
    if arch_yaml.exists():
        try:
            data = load_metadata(archetype_dir)
        except Exception as e:
            problems.append(f"{name}: archetype.yaml parse error: {e}")
            return problems
        missing = REQUIRED_META_FIELDS - set(data)
        if missing:
            problems.append(f"{name}: missing metadata fields {sorted(missing)}")
        if data.get("name") != name:
            problems.append(
                f"{name}: archetype.yaml 'name' ({data.get('name')!r}) "
                f"does not match directory name"
            )

    claim_map = archetype_dir / "claim-map.yaml"
    if claim_map.exists():
        try:
            cm = yaml.safe_load(claim_map.read_text()) or {}
            if "claims" not in cm or not isinstance(cm["claims"], list):
                problems.append(f"{name}: claim-map.yaml has no 'claims' list")
            elif not cm["claims"]:
                problems.append(f"{name}: claim-map.yaml has empty 'claims'")
            else:
                for c in cm["claims"]:
                    if "priority" not in c or "status" not in c:
                        problems.append(
                            f"{name}: claim {c.get('id','?')} missing priority/status"
                        )
                # At least one critical claim is strongly recommended.
                if not any(
                    str(c.get("priority", "")).lower() == "critical"
                    for c in cm["claims"]
                ):
                    problems.append(
                        f"{name}: claim-map.yaml has no critical claims"
                    )
        except Exception as e:
            problems.append(f"{name}: claim-map.yaml parse error: {e}")

    return problems


def validate_all() -> list[str]:
    problems: list[str] = []
    dirs = list_archetypes()
    if not dirs:
        problems.append("no archetypes found under archetypes/")
        return problems
    for d in dirs:
        problems.extend(validate_one(d))
    return problems


def render_show(data: dict) -> str:
    lines = [
        f"name:                      {data['name']}",
        f"default_verdict_ceiling:   {data['default_verdict_ceiling']}",
        "",
        "description:",
    ]
    for ln in str(data.get("description", "")).strip().splitlines():
        lines.append(f"  {ln}")
    lines += ["", "evaluation_dimensions:"]
    for d in data.get("evaluation_dimensions", []):
        if isinstance(d, dict):
            for k, v in d.items():
                lines.append(f"  - {k}: {v}")
        else:
            lines.append(f"  - {d}")
    lines += ["", "recommended_evidence:"]
    for e in data.get("recommended_evidence", []):
        lines.append(f"  - {e}")
    lines += ["", "default_claim_prompts:"]
    for p in data.get("default_claim_prompts", []):
        lines.append(f"  - {p}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list all archetypes")

    p_show = sub.add_parser("show", help="show an archetype in detail")
    p_show.add_argument("name")
    p_show.add_argument("--json", action="store_true")

    sub.add_parser("validate", help="schema-check every archetype")

    args = parser.parse_args(argv)

    if args.cmd == "list":
        dirs = list_archetypes()
        if not dirs:
            print("(no archetypes)")
            return 0
        print(f"{'name':15s}  ceiling                              description")
        print("-" * 100)
        for d in dirs:
            meta = load_metadata(d)
            desc = str(meta.get("description", "")).strip().splitlines()[0]
            ceiling = str(meta.get("default_verdict_ceiling", ""))[:35]
            print(f"{meta['name']:15s}  {ceiling:37s}  {desc}")
        return 0

    if args.cmd == "show":
        d = ARCH_DIR / args.name
        if not d.exists():
            print(f"no such archetype: {args.name}", file=sys.stderr)
            return 1
        meta = load_metadata(d)
        if args.json:
            print(json.dumps(meta, indent=2, ensure_ascii=False))
        else:
            sys.stdout.write(render_show(meta))
        return 0

    if args.cmd == "validate":
        problems = validate_all()
        if not problems:
            n = len(list_archetypes())
            print(f"OK: {n} archetypes, no problems")
            return 0
        print("FAIL:")
        for p in problems:
            print(f"  - {p}")
        return 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
