#!/usr/bin/env python3
"""
audit_has_license.py — verify the `has_license` field in every repo.yaml
matches reality on GitHub.

Why: `has_license` drives a -2 to -5 score penalty. README MIT badges lie.
README files claiming MIT without a LICENSE file are common. This script
reconciles the eval state with what GitHub actually reports.

Treats GitHub's three response shapes correctly:
  - `license: null` → no LICENSE file → has_license MUST be false
  - `license: {spdx_id: "MIT", ...}` → recognized OSS license → has_license: true
  - `license: {spdx_id: "NOASSERTION", ...}` → LICENSE file exists but is
      modified / non-standard (e.g. modified MIT non-commercial). The file
      is real, so has_license stays true; we surface a `caveat` so the
      evaluator can decide whether the modification matters for downstream
      use (commercial fork, redistribution, etc.).

Usage:
    python3 scripts/audit_has_license.py                # report all mismatches
    python3 scripts/audit_has_license.py --slug zinan92--intel  # one repo
    python3 scripts/audit_has_license.py --json         # machine-readable

Run periodically. Not currently wired to CI — license state changes
slowly enough that a manual sweep before each ship is fine.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _gh_api(endpoint: str) -> dict[str, Any] | None:
    """Call `gh api <endpoint>` and return parsed JSON, or None on error."""
    try:
        result = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _read_yaml(path: pathlib.Path) -> dict[str, Any]:
    import yaml

    with open(path) as f:
        return yaml.safe_load(f) or {}


def _slug_to_owner_repo(slug: str) -> tuple[str, str]:
    """`zinan92--intel` → (`zinan92`, `intel`). Only first `--` is the split."""
    parts = slug.split("--", 1)
    if len(parts) != 2:
        raise ValueError(f"unexpected slug shape: {slug}")
    return parts[0], parts[1]


def audit_repo(slug: str) -> dict[str, Any]:
    """Audit one repo. Returns a dict with status + diagnostics."""
    repo_yaml = ROOT / "repos" / slug / "repo.yaml"
    if not repo_yaml.exists():
        return {"slug": slug, "status": "missing_yaml"}

    repo = _read_yaml(repo_yaml)
    declared = repo.get("has_license")
    owner, name = _slug_to_owner_repo(slug)

    api = _gh_api(f"repos/{owner}/{name}")
    if api is None:
        return {"slug": slug, "status": "api_error", "declared": declared}

    license_obj = api.get("license")
    if license_obj is None:
        actual = "missing"
        spdx = None
    else:
        spdx = license_obj.get("spdx_id")
        if spdx == "NOASSERTION":
            actual = "noassertion"
        else:
            actual = "present"

    # Determine truth: NOASSERTION still counts as has_license=true because
    # a LICENSE file exists, but we surface a caveat.
    expected_has_license = actual in ("present", "noassertion")
    matches = bool(declared) == expected_has_license

    return {
        "slug": slug,
        "status": "ok" if matches else "mismatch",
        "declared": declared,
        "actual": actual,
        "spdx_id": spdx,
        "expected_has_license": expected_has_license,
        "caveat": (
            "LICENSE file exists but is non-standard — review for commercial / "
            "redistribution restrictions"
            if actual == "noassertion"
            else None
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--slug",
        help="Audit a single slug (e.g. zinan92--intel). Default: all repos.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON (machine-readable). Default: human text.",
    )
    parser.add_argument(
        "--mismatches-only",
        action="store_true",
        help="Only show repos where declared != actual.",
    )
    args = parser.parse_args(argv)

    if args.slug:
        slugs = [args.slug]
    else:
        slugs = sorted(p.parent.name for p in (ROOT / "repos").glob("*/repo.yaml"))

    results = [audit_repo(s) for s in slugs]
    # Always count the full set; --mismatches-only only filters the JSON
    # listing and the per-repo printout below.
    visible = (
        [r for r in results if r["status"] == "mismatch"]
        if args.mismatches_only
        else results
    )

    if args.json:
        print(json.dumps(visible, indent=2, ensure_ascii=False))
    else:
        ok = sum(1 for r in results if r["status"] == "ok")
        mismatches = sum(1 for r in results if r["status"] == "mismatch")
        api_errors = sum(1 for r in results if r["status"] == "api_error")
        noassertion = sum(1 for r in results if r.get("actual") == "noassertion")

        print(f"Audited {len(results)} repos:")
        print(f"  ok:           {ok}")
        print(f"  mismatch:     {mismatches}")
        print(f"  api_error:    {api_errors}")
        print(f"  noassertion:  {noassertion}  (LICENSE file present but non-standard)")
        print()

        if mismatches:
            print("=== mismatches (declared != actual) ===")
            for r in results:
                if r["status"] != "mismatch":
                    continue
                print(
                    f"  {r['slug']:50s}  declared={r['declared']!s:5s}  "
                    f"actual={r['actual']:11s}  expected={r['expected_has_license']}"
                )
            print()

        if noassertion:
            print("=== NOASSERTION (review needed) ===")
            for r in results:
                if r.get("actual") != "noassertion":
                    continue
                print(f"  {r['slug']:50s}  spdx={r.get('spdx_id')}")
                if r.get("caveat"):
                    print(f"    {r['caveat']}")

    return 1 if any(r["status"] == "mismatch" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
