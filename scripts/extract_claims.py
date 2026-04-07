#!/usr/bin/env python3
"""
extract_claims.py — draft a claim map from README / SKILL.md / docs.

Given a target repo path, this tool produces a draft `claim-map.yaml`
where every entry is marked `needs_review: true` and `status: untested`.
It is deliberately conservative: it would rather under-claim than
invent capabilities the repo never promised.

Usage:
    scripts/extract_claims.py <target-repo-path> [-o draft-claim-map.yaml]
    scripts/extract_claims.py <target-repo-path> --stdout
    scripts/extract_claims.py <target-repo-path> --sources README.md,SKILL.md

What it looks at, in order of trust:
    README.md
    SKILL.md
    docs/*.md  (first 5, for breadth not depth)

What it extracts, all tagged with confidence:
    high   — Feature / Capability bullets under clearly-named sections
    high   — Rows in a Commands / Usage table
    medium — Numeric promises ("supports 3 formats", "handles 10 MB")
    medium — Badge versions (acts as an environment claim)
    low    — Bullets under any section that looks feature-ish but wasn't
             explicitly labeled

Every extracted claim gets:
    - confidence (low | medium | high)
    - needs_review: true
    - status: untested
    - source_ref: the file + heading path it came from
    - extractor_rule: which rule fired

The tool does NOT write claims for:
    - Installation steps
    - Licensing
    - Contributing / Code of conduct
    - Anything that looks like a disclaimer

A reviewer is expected to run this, read the YAML, and prune / edit
before using it as a real claim map.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:  # pragma: no cover
    print("extract_claims.py: PyYAML required", file=sys.stderr)
    sys.exit(2)


# --- Data model -----------------------------------------------------------


@dataclass
class DraftClaim:
    title: str
    statement: str
    source: str
    source_ref: str
    priority: str = "medium"
    area: str = "core"
    confidence: str = "low"
    extractor_rule: str = ""
    business_expectation: str = ""
    evidence_needed: str = ""


# --- Heading / section parsing --------------------------------------------


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# Sections that almost always contain claim-worthy material.
# Keep this list short and boring — the whole point is to stay conservative.
HIGH_TRUST_FEATURE_HEADINGS = {
    "features",
    "what this does",
    "what it does",
    "capabilities",
    "capability",
    "功能",
    "功能一览",
    "功能列表",
    "capability contract",
}

HIGH_TRUST_COMMAND_HEADINGS = {
    "commands",
    "available commands",
    "usage",
    "命令",
    "命令列表",
}

# Sections that should NEVER produce claims. If we are currently inside
# one of these, we skip bullets entirely.
EXCLUDE_HEADINGS = {
    "installation",
    "install",
    "安装",
    "license",
    "licensing",
    "contributing",
    "contribution",
    "code of conduct",
    "changelog",
    "acknowledgements",
    "credits",
    "sponsors",
    "authors",
    "table of contents",
    "toc",
}


def _normalize_heading(text: str) -> str:
    # Strip emoji / markdown formatting / trailing punctuation
    text = re.sub(r"[#*_`~]", "", text).strip()
    text = re.sub(r"^[\s\W]+", "", text)
    text = re.sub(r"[\s\W]+$", "", text)
    return text.lower()


@dataclass
class Section:
    level: int
    title: str
    body_lines: list[str] = field(default_factory=list)


def split_sections(text: str) -> list[Section]:
    """Naive section splitter: each markdown heading starts a new section."""
    sections: list[Section] = []
    current = Section(level=0, title="(prelude)")
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            if current.body_lines or current.title != "(prelude)":
                sections.append(current)
            current = Section(level=len(m.group(1)), title=m.group(2).strip())
        else:
            current.body_lines.append(line)
    sections.append(current)
    return sections


# --- Bullet / row extraction ----------------------------------------------


BULLET_RE = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
NUMERIC_CLAIM_RE = re.compile(
    r"\b(?:"
    r"supports?\s+(\d+)\s+\w+"            # "supports 4 platforms"
    r"|handles?\s+(?:up\s+to\s+)?(\d+)\s*\w+"  # "handles 10 MB"
    r"|up\s+to\s+(\d+)\s+\w+"             # "up to 100 files"
    r"|(\d+)\+\s+\w+"                     # "10+ connectors"
    r")",
    re.IGNORECASE,
)

BADGE_RE = re.compile(
    r"\[!\[([^\]]+)\]\([^)]+(?:/badge/)?([^)]*)\)\]?"
)


def _clean_bullet(body: str) -> str:
    body = body.strip()
    # Strip leading inline code or bold markers
    body = re.sub(r"^(`[^`]+`|\*\*[^*]+\*\*)\s*[-—:]\s*", "", body)
    # Strip trailing citations / punctuation
    body = body.rstrip(".,;")
    return body.strip()


def bullets_in_section(section: Section) -> list[str]:
    out: list[str] = []
    for line in section.body_lines:
        m = BULLET_RE.match(line)
        if not m:
            continue
        text = _clean_bullet(m.group(1))
        if not text:
            continue
        # Ignore obvious sub-bullets of installation / licenses
        if any(tok in text.lower() for tok in ("pip install", "npm install", "git clone", "©")):
            continue
        out.append(text)
    return out


def table_rows_in_section(section: Section) -> list[list[str]]:
    rows: list[list[str]] = []
    seen_separator = False
    for line in section.body_lines:
        m = TABLE_ROW_RE.match(line)
        if not m:
            if rows:
                break
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        # Skip header-separator rows: ---|---|---
        if all(re.fullmatch(r":?-+:?", c or "") for c in cells):
            seen_separator = True
            continue
        if seen_separator:
            rows.append(cells)
    return rows


# --- Extraction rules -----------------------------------------------------


def extract_from_feature_section(
    section: Section, source_label: str, inside_excluded: bool
) -> list[DraftClaim]:
    if inside_excluded:
        return []
    out: list[DraftClaim] = []
    title_norm = _normalize_heading(section.title)

    is_high_trust = any(
        h in title_norm for h in HIGH_TRUST_FEATURE_HEADINGS
    )
    is_command_section = any(
        h in title_norm for h in HIGH_TRUST_COMMAND_HEADINGS
    )

    if is_command_section:
        for row in table_rows_in_section(section):
            # Expect: command | description (at least 2 cells)
            if len(row) < 2:
                continue
            cmd = row[0]
            desc = row[1]
            if not cmd or not desc:
                continue
            # Strip backticks from the command name
            cmd_clean = cmd.strip("`").strip()
            if not cmd_clean:
                continue
            out.append(DraftClaim(
                title=f"`{cmd_clean}` — {desc[:60]}".rstrip(),
                statement=(
                    f"The command `{cmd_clean}` delivers on this described "
                    f"behavior: {desc}"
                ),
                source=source_label,
                source_ref=f"section '{section.title}' / commands table",
                priority="high",
                area="core",
                confidence="high",
                extractor_rule="command_table_row",
                business_expectation=(
                    f"A user running `{cmd_clean}` gets the behavior "
                    f"described in the README's commands table."
                ),
                evidence_needed=(
                    f"A real invocation of `{cmd_clean}` on a realistic "
                    f"input, with the output matching the described "
                    f"behavior and exit code 0."
                ),
            ))
        return out

    if not is_high_trust:
        # Low-trust: we still pull bullets but tag them as such
        for b in bullets_in_section(section):
            out.append(DraftClaim(
                title=b[:80],
                statement=b,
                source=source_label,
                source_ref=f"section '{section.title}'",
                priority="medium",
                area="core",
                confidence="low",
                extractor_rule="generic_section_bullet",
                business_expectation="",
                evidence_needed="",
            ))
        return out

    # High-trust feature bullets
    for b in bullets_in_section(section):
        prio = "critical" if _looks_critical(b) else "high"
        out.append(DraftClaim(
            title=b[:80],
            statement=b,
            source=source_label,
            source_ref=f"section '{section.title}'",
            priority=prio,
            area="core",
            confidence="high",
            extractor_rule="feature_bullet",
            business_expectation=(
                "Listed as a top-level capability in the README."
            ),
            evidence_needed=(
                "A real run exercising this capability, with the output "
                "matching what the bullet promises."
            ),
        ))
    return out


def _looks_critical(bullet_text: str) -> bool:
    """Very simple heuristic — a bullet feels 'critical' if it names the
    headline capability verbs."""
    t = bullet_text.lower()
    signals = [
        "download", "generate", "convert", "transform", "deploy", "install",
        "render", "parse", "extract", "analyze", "analyse", "route",
        "validate", "search",
        "下载", "生成", "转换", "部署", "安装", "渲染", "解析", "提取", "分析",
    ]
    return any(s in t for s in signals)


def extract_numeric_claims(
    text: str, source_label: str
) -> list[DraftClaim]:
    out: list[DraftClaim] = []
    for line in text.splitlines():
        for m in NUMERIC_CLAIM_RE.finditer(line):
            snippet = m.group(0).strip()
            # Take the surrounding bullet or sentence as title
            title = line.strip(" -*+|").strip()[:80]
            if not title:
                title = snippet
            out.append(DraftClaim(
                title=f"numeric: {snippet}",
                statement=(
                    f"Numeric claim found in source: '{snippet}' "
                    f"(context: {title[:120]})"
                ),
                source=source_label,
                source_ref="numeric regex match",
                priority="medium",
                area="numeric-claims",
                confidence="medium",
                extractor_rule="numeric_claim_regex",
                business_expectation=(
                    "Numeric promises in README should either be true "
                    "or removed."
                ),
                evidence_needed=(
                    "Run a real test that counts / measures the value "
                    "and confirm it matches the promised number."
                ),
            ))
    return out


def extract_badges(text: str, source_label: str) -> list[DraftClaim]:
    out: list[DraftClaim] = []
    for m in BADGE_RE.finditer(text):
        label = m.group(1)
        if not label or "license" in label.lower():
            continue
        # We only care about version-ish or count-ish badges as claims
        if not re.search(r"\d", label):
            continue
        out.append(DraftClaim(
            title=f"badge claim: {label}",
            statement=(
                f"README badge asserts: '{label}'. A badge is a public "
                f"claim about the repo and should either be accurate or "
                f"removed."
            ),
            source=source_label,
            source_ref="README badge",
            priority="low",
            area="meta",
            confidence="medium",
            extractor_rule="badge_claim",
            business_expectation="Badge matches reality.",
            evidence_needed="Cross-check the badge value against the source.",
        ))
    return out


# --- Orchestration --------------------------------------------------------


def _is_excluded_section(title: str) -> bool:
    norm = _normalize_heading(title)
    return any(h == norm or h in norm for h in EXCLUDE_HEADINGS)


def extract_from_text(text: str, source_label: str) -> list[DraftClaim]:
    sections = split_sections(text)
    out: list[DraftClaim] = []
    excluded_stack: list[int] = []  # stack of section levels currently excluded

    for s in sections:
        # Pop excluded sections that this heading has moved out of
        while excluded_stack and s.level <= excluded_stack[-1]:
            excluded_stack.pop()

        if _is_excluded_section(s.title):
            excluded_stack.append(s.level)
            continue

        inside_excluded = bool(excluded_stack)
        out.extend(extract_from_feature_section(s, source_label, inside_excluded))

    out.extend(extract_numeric_claims(text, source_label))
    out.extend(extract_badges(text, source_label))
    return out


def dedupe(claims: list[DraftClaim]) -> list[DraftClaim]:
    seen: dict[str, DraftClaim] = {}
    order: list[str] = []
    for c in claims:
        key = (c.statement.strip().lower(), c.source)
        k = "|".join(str(x) for x in key)
        if k not in seen:
            seen[k] = c
            order.append(k)
        else:
            # Prefer higher-confidence entries
            ranks = {"low": 0, "medium": 1, "high": 2}
            if ranks.get(c.confidence, 0) > ranks.get(seen[k].confidence, 0):
                seen[k] = c
    return [seen[k] for k in order]


def discover_sources(
    repo: pathlib.Path, names: list[str] | None
) -> list[pathlib.Path]:
    """Discover source files, deduping by resolved real path so that
    case-insensitive filesystems (macOS default) don't process the same
    README three times just because we checked README.md / Readme.md /
    readme.md separately."""
    candidates: list[pathlib.Path] = []

    if names:
        for n in names:
            p = repo / n
            if p.exists():
                candidates.append(p)
    else:
        for name in ("README.md", "Readme.md", "readme.md", "SKILL.md"):
            p = repo / name
            if p.exists():
                candidates.append(p)
        docs = repo / "docs"
        if docs.exists():
            candidates.extend(sorted(docs.glob("*.md"))[:5])

    # Dedupe by filesystem identity (device, inode) — this correctly
    # handles case-insensitive filesystems on macOS where README.md,
    # Readme.md, and readme.md all refer to the same underlying file
    # but .resolve() preserves caller casing.
    seen: set[tuple[int, int]] = set()
    out: list[pathlib.Path] = []
    for p in candidates:
        try:
            st = p.stat()
            key = (st.st_dev, st.st_ino)
        except OSError:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def to_yaml(claims: list[DraftClaim]) -> str:
    """Emit a draft claim-map.yaml with an explicit AUTO header."""
    header = (
        "# AUTO-EXTRACTED claim map — review before use.\n"
        "# Every entry has:\n"
        "#   - needs_review: true\n"
        "#   - status: untested\n"
        "#   - confidence: low | medium | high (how much the extractor trusts itself)\n"
        "#   - extractor_rule: which rule produced this entry\n"
        "# Expect to delete, merge, re-title, and rewrite statements before\n"
        "# using this as a real claim map. The tool is conservative by design.\n"
        "#\n"
        "# Generated by scripts/extract_claims.py\n"
    )
    entries = []
    for i, c in enumerate(claims, start=1):
        entries.append({
            "id": f"claim-{i:03d}",
            "title": c.title,
            "source": c.source,
            "source_ref": c.source_ref,
            "priority": c.priority,
            "area": c.area,
            "statement": c.statement,
            "business_expectation": c.business_expectation,
            "evidence_needed": c.evidence_needed,
            "status": "untested",
            "needs_review": True,
            "confidence": c.confidence,
            "extractor_rule": c.extractor_rule,
        })
    return header + yaml.safe_dump(
        {"claims": entries},
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def run(
    repo_dir: pathlib.Path,
    *,
    sources: list[str] | None = None,
) -> list[DraftClaim]:
    files = discover_sources(repo_dir, sources)
    if not files:
        return []
    all_claims: list[DraftClaim] = []
    for f in files:
        label = str(f.relative_to(repo_dir))
        all_claims.extend(extract_from_text(f.read_text(), label))
    return dedupe(all_claims)


# --- CLI ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("repo_dir", type=pathlib.Path)
    parser.add_argument("-o", "--output", type=pathlib.Path, default=None)
    parser.add_argument(
        "--stdout", action="store_true",
        help="write the draft to stdout instead of a file",
    )
    parser.add_argument(
        "--sources",
        help="comma-separated list of source files relative to repo_dir "
             "(default: README.md + SKILL.md + docs/*.md)",
    )
    args = parser.parse_args(argv)

    if not args.repo_dir.exists():
        print(f"no such repo dir: {args.repo_dir}", file=sys.stderr)
        return 2

    sources = args.sources.split(",") if args.sources else None
    claims = run(args.repo_dir, sources=sources)

    text = to_yaml(claims)

    if args.stdout or not args.output:
        sys.stdout.write(text)
        print(f"# {len(claims)} draft claims extracted", file=sys.stderr)
        return 0

    args.output.write_text(text)
    print(f"wrote {args.output} ({len(claims)} draft claims)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
