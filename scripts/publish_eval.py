#!/usr/bin/env python3
"""Render one or more verdict dossiers, then refresh the master dashboard.

Use this as the default publishing command after editing a repo eval:

    python3 scripts/publish_eval.py owner--repo --lang zh
    python3 scripts/publish_eval.py owner/repo --date 2026-07-09
    python3 scripts/publish_eval.py --all --lang zh
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def normalise_slug(target: str) -> str:
    """Accept either owner--repo or owner/repo and return owner--repo."""

    value = target.strip().strip("/")
    if not value:
        raise ValueError("empty repo target")
    if "/" in value:
        parts = [p for p in value.split("/") if p]
        if len(parts) != 2:
            raise ValueError(f"expected owner/repo or owner--repo, got: {target}")
        return f"{parts[0]}--{parts[1]}"
    return value


def discover_slugs() -> list[str]:
    """Return every complete eval slug under repos/."""

    slugs: list[str] = []
    for repo_dir in sorted((ROOT / "repos").iterdir()):
        if not repo_dir.is_dir():
            continue
        if (repo_dir / "repo.yaml").exists() and (
            repo_dir / "claims" / "claim-map.yaml"
        ).exists():
            slugs.append(repo_dir.name)
    return slugs


def build_commands(
    slugs: list[str],
    *,
    date: str | None = None,
    lang: str = "auto",
) -> list[list[str]]:
    """Build subprocess commands in the exact order they should run."""

    commands: list[list[str]] = []
    for slug in slugs:
        cmd = [
            sys.executable,
            str(SCRIPTS / "render_verdict_html.py"),
            slug,
            "--lang",
            lang,
            "--no-dashboard",
        ]
        if date:
            cmd.extend(["--date", date])
        commands.append(cmd)
    commands.append([sys.executable, str(SCRIPTS / "build_master_dashboard.py")])
    return commands


def run_commands(commands: list[list[str]], *, dry_run: bool = False) -> int:
    for cmd in commands:
        print("+ " + " ".join(cmd), flush=True)
        if dry_run:
            continue
        result = subprocess.run(cmd, cwd=ROOT, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "targets",
        nargs="*",
        help="Repo slug(s), owner--repo or owner/repo. Omit with --all.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Render every complete eval under repos/, then rebuild the dashboard once.",
    )
    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="Only rebuild dashboard/all-evals.html.",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Date prefix of the verdict to render; default = latest.",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "zh", "auto"],
        default="auto",
        help="Initial UI language passed to render_verdict_html.py.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without running them.",
    )
    args = parser.parse_args()

    if args.dashboard_only:
        return run_commands(
            [[sys.executable, str(SCRIPTS / "build_master_dashboard.py")]],
            dry_run=args.dry_run,
        )

    if args.all:
        slugs = discover_slugs()
    else:
        slugs = [normalise_slug(t) for t in args.targets]

    if not slugs:
        parser.error("provide at least one target, or use --all / --dashboard-only")

    missing = [s for s in slugs if not (ROOT / "repos" / s / "repo.yaml").exists()]
    if missing:
        parser.error(f"repo.yaml not found for: {', '.join(missing)}")

    commands = build_commands(slugs, date=args.date, lang=args.lang)
    return run_commands(commands, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
