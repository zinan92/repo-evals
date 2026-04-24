#!/usr/bin/env python3
"""
verdict_calculator.py — rule-guided verdict recommendation for repo-evals.

Reads a structured verdict-input file (YAML or JSON) and emits a
verdict-recommendation document. Keeps human override explicit and auditable.

Usage:
    scripts/verdict_calculator.py <input.yaml> [-o output.yaml]
    scripts/verdict_calculator.py <input.yaml> --json

Input schema (all keys optional unless marked required):

    repo: "owner/repo"                # required
    archetype: "hybrid-skill"         # one of the known archetypes
    core_layer_tested: true|false     # required for meaningful verdict
    evidence_completeness:            # one of: none, partial, portable, full
      "portable"
    coverage_summary:
      critical_claims: 5
      critical_covered: 4
      total_claims: 12
      total_covered: 10
    claims:                           # or list of {id, priority, status}
      - id: claim-001
        priority: critical            # critical | high | medium | low
        status: passed                # passed | passed_with_concerns |
                                      # failed | failed_partial | untested
    override:
      apply: true
      bucket: "reusable"
      reason: "manual review: B-layer covered in runs/..."

The tool writes a recommendation file with:
    recommended_bucket, final_bucket, confidence, ceiling_reason,
    blocking_issues, inputs_summary, override

Exit status: 0 on success, 1 on input error.

This is called by hand or by a wrapper; it does not mutate run-summary.yaml
or final-verdict.md — those remain human-owned documents.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

try:
    import yaml  # PyYAML — standard on most dev systems
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

# --- Domain model ---------------------------------------------------------

BUCKETS = ["unusable", "usable", "reusable", "recommendable"]
BUCKET_RANK = {b: i for i, b in enumerate(BUCKETS)}
BUCKET_EMOJI = {
    "unusable": "🔴",
    "usable": "⚪",
    "reusable": "🟡",
    "recommendable": "🟢",
}


def with_emoji(bucket: str | None) -> str:
    """Render a bucket name with its emoji prefix for display output.
    Internal bucket strings remain unchanged — this is display-only."""
    if bucket is None:
        return "—"
    return f"{BUCKET_EMOJI.get(bucket, '·')} {bucket}"

# Archetypes where the user-facing value requires a live LLM / end-to-end
# layer that is hard to validate via static checks alone. These repos get
# a hybrid-cap rule: if the core layer is not tested, overall verdict
# cannot exceed "usable" regardless of support-layer strength.
HYBRID_ARCHETYPES = {"hybrid-skill", "prompt-skill", "orchestrator", "mcp-enhancement"}

EVIDENCE_RANK = {
    "none": 0,
    "partial": 1,
    "portable": 2,
    "full": 3,
}

# Claim statuses that count as "passing" for coverage purposes.
PASS_STATUSES = {"passed", "pass", "passed_with_concerns", "pass-with-concerns"}
FAIL_STATUSES = {"failed", "fail", "failed_partial", "fail-partial"}
UNTESTED_STATUSES = {"untested", "pending", "unknown"}


class VerdictError(ValueError):
    pass


# --- Core logic -----------------------------------------------------------


def cap(bucket: str, ceiling: str) -> str:
    """Return the lower of (bucket, ceiling) by rank."""
    return bucket if BUCKET_RANK[bucket] <= BUCKET_RANK[ceiling] else ceiling


def _classify_claim(c: dict) -> tuple[str, str]:
    """Return (priority, normalized status)."""
    prio = str(c.get("priority", "medium")).lower()
    status = str(c.get("status", "untested")).lower().replace(" ", "_")
    if status in PASS_STATUSES:
        norm = "passed"
    elif status in FAIL_STATUSES:
        norm = "failed"
    elif status in UNTESTED_STATUSES:
        norm = "untested"
    else:
        # Unknown status → treat as untested for safety
        norm = "untested"
    return prio, norm


def compute_verdict(inp: dict) -> dict:
    """Pure function: input dict → recommendation dict."""

    # --- Extract + validate -----------------------------------------------
    repo = inp.get("repo", "")
    archetype = str(inp.get("archetype", "unknown")).lower()
    core_layer_tested = bool(inp.get("core_layer_tested", False))
    evidence_str = str(inp.get("evidence_completeness", "partial")).lower()
    if evidence_str not in EVIDENCE_RANK:
        raise VerdictError(f"unknown evidence_completeness: {evidence_str}")

    claims = inp.get("claims") or []
    if not isinstance(claims, list):
        raise VerdictError("claims must be a list")

    # Aggregate claim stats
    stats = {
        "total": 0,
        "critical_total": 0,
        "critical_passed": 0,
        "critical_failed": 0,
        "critical_untested": 0,
        "high_total": 0,
        "high_failed": 0,
        "high_untested": 0,
        "passed": 0,
        "failed": 0,
        "untested": 0,
    }
    blocking_issues: list[str] = []
    for c in claims:
        prio, status = _classify_claim(c)
        stats["total"] += 1
        stats[status] = stats.get(status, 0) + 1
        if prio == "critical":
            stats["critical_total"] += 1
            if status == "passed":
                stats["critical_passed"] += 1
            elif status == "failed":
                stats["critical_failed"] += 1
                blocking_issues.append(
                    f"critical claim {c.get('id','?')} failed"
                )
            elif status == "untested":
                stats["critical_untested"] += 1
        elif prio == "high":
            stats["high_total"] += 1
            if status == "failed":
                stats["high_failed"] += 1
            elif status == "untested":
                stats["high_untested"] += 1

    # Coverage summary (prefer claim-derived; fall back to explicit block)
    cov = inp.get("coverage_summary") or {}
    total_claims = stats["total"] or int(cov.get("total_claims", 0) or 0)
    total_covered = (
        stats["passed"]
        if stats["total"]
        else int(cov.get("total_covered", 0) or 0)
    )
    critical_total = (
        stats["critical_total"]
        if stats["total"]
        else int(cov.get("critical_claims", 0) or 0)
    )
    critical_covered = (
        stats["critical_passed"]
        if stats["total"]
        else int(cov.get("critical_covered", 0) or 0)
    )

    # --- Baseline bucket from claim results --------------------------------
    # Decision tree (conservative, explainable):
    #
    #   any critical failed      → unusable
    #   no critical covered      → unusable
    #   critical covered < all   → usable (partial core)
    #   all critical passed &
    #     high all resolved &
    #     coverage >= 80%        → reusable
    #   everything passed &
    #     no untested critical   → recommendable
    #
    # Then apply ceilings.

    if stats["critical_failed"] > 0:
        base = "unusable"
    elif critical_total == 0:
        # No critical claims defined — we cannot be confident about core.
        base = "usable"
        blocking_issues.append("no critical claims defined")
    elif critical_covered == 0:
        base = "unusable"
        blocking_issues.append("zero critical claims covered")
    elif critical_covered < critical_total:
        base = "usable"
        blocking_issues.append(
            f"only {critical_covered}/{critical_total} critical claims covered"
        )
    else:
        # All critical claims passed. Now look at breadth.
        coverage_pct = (
            (total_covered / total_claims) if total_claims else 0.0
        )
        if stats["high_failed"] > 0 or coverage_pct < 0.8:
            base = "reusable" if coverage_pct >= 0.5 else "usable"
        elif stats["high_untested"] > 0 or stats["untested"] > 0:
            base = "reusable"
        else:
            base = "recommendable"

    # --- Ceilings ----------------------------------------------------------
    # Record every ceiling that *applies*, even if it didn't actually change
    # the bucket — reviewers should see the full set of constraints the
    # verdict would have to satisfy to go higher.
    ceiling_reasons: list[str] = []
    bucket = base

    # Ceiling 1: untested core layer caps at "usable"
    if not core_layer_tested:
        ceiling_reasons.append(
            "core user-facing layer untested → capped at 'usable'"
        )
        bucket = cap(bucket, "usable")

    # Ceiling 2: hybrid archetypes with untested core layer get a
    # second, more specific reason so reviewers know which rule fired.
    if archetype in HYBRID_ARCHETYPES and not core_layer_tested:
        ceiling_reasons.append(
            f"hybrid-repo rule: archetype '{archetype}' requires "
            "end-to-end evaluation of the user-facing layer"
        )

    # Ceiling 3: weak evidence caps below recommendable
    if EVIDENCE_RANK[evidence_str] < EVIDENCE_RANK["portable"]:
        ceiling_reasons.append(
            f"evidence_completeness='{evidence_str}' "
            "(not portable) → capped at 'usable'"
        )
        bucket = cap(bucket, "usable")
    elif EVIDENCE_RANK[evidence_str] < EVIDENCE_RANK["full"]:
        ceiling_reasons.append(
            f"evidence_completeness='{evidence_str}' → capped at 'reusable'"
        )
        bucket = cap(bucket, "reusable")

    # --- Confidence --------------------------------------------------------
    confidence = "high"
    if stats["total"] == 0:
        confidence = "low"
    elif stats["critical_untested"] > 0 or stats["untested"] > stats["total"] // 3:
        confidence = "low"
    elif ceiling_reasons or stats["high_untested"] > 0:
        confidence = "medium"

    # --- Override ----------------------------------------------------------
    override_in = inp.get("override") or {}
    override_out = {
        "applied": False,
        "bucket": None,
        "reason": None,
    }
    final = bucket
    if override_in.get("apply"):
        ob = override_in.get("bucket")
        reason = override_in.get("reason")
        if ob not in BUCKETS:
            raise VerdictError(f"override.bucket must be one of {BUCKETS}")
        if not reason:
            raise VerdictError("override.reason is required when override.apply=true")
        override_out = {
            "applied": True,
            "bucket": ob,
            "reason": reason,
        }
        final = ob

    return {
        "repo": repo,
        "archetype": archetype,
        "recommended_bucket": bucket,
        "final_bucket": final,
        "confidence": confidence,
        "ceiling_reasons": ceiling_reasons,
        "blocking_issues": blocking_issues,
        "inputs_summary": {
            "core_layer_tested": core_layer_tested,
            "evidence_completeness": evidence_str,
            "claims_total": stats["total"],
            "claims_passed": stats["passed"],
            "claims_failed": stats["failed"],
            "claims_untested": stats["untested"],
            "critical_total": critical_total,
            "critical_covered": critical_covered,
            "critical_failed": stats["critical_failed"],
        },
        "override": override_out,
    }


# --- I/O ------------------------------------------------------------------


def _load(path: pathlib.Path) -> dict:
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        if yaml is None:
            raise VerdictError("PyYAML not installed; use .json input instead")
        data = yaml.safe_load(text)
    elif path.suffix == ".json":
        data = json.loads(text)
    else:
        # Try yaml first, then json
        if yaml is not None:
            try:
                data = yaml.safe_load(text)
            except Exception:
                data = json.loads(text)
        else:
            data = json.loads(text)
    if not isinstance(data, dict):
        raise VerdictError("input must be a mapping")
    return data


def _dump_yaml(data: dict) -> str:
    if yaml is None:
        return json.dumps(data, indent=2)
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def render_markdown(rec: dict) -> str:
    """Human-readable explanation for verdict docs."""
    lines = [
        f"## Verdict Recommendation — {rec.get('repo','')}",
        "",
        f"- **Recommended bucket:** {with_emoji(rec['recommended_bucket'])}",
        f"- **Final bucket:** {with_emoji(rec['final_bucket'])}"
        + (" (override applied)" if rec["override"]["applied"] else ""),
        f"- **Confidence:** {rec['confidence']}",
        f"- **Archetype:** {rec['archetype']}",
        "",
        "### Ceiling Reasons",
    ]
    if rec["ceiling_reasons"]:
        for r in rec["ceiling_reasons"]:
            lines.append(f"- {r}")
    else:
        lines.append("- none")
    lines += ["", "### Blocking Issues"]
    if rec["blocking_issues"]:
        for b in rec["blocking_issues"]:
            lines.append(f"- {b}")
    else:
        lines.append("- none")
    lines += ["", "### Inputs Summary"]
    for k, v in rec["inputs_summary"].items():
        lines.append(f"- {k}: {v}")
    if rec["override"]["applied"]:
        lines += [
            "",
            "### Override",
            f"- bucket: `{rec['override']['bucket']}`",
            f"- reason: {rec['override']['reason']}",
        ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("-o", "--output", type=pathlib.Path, default=None)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--md", action="store_true", help="emit Markdown report")
    args = parser.parse_args(argv)

    try:
        data = _load(args.input)
        rec = compute_verdict(data)
    except VerdictError as e:
        print(f"verdict-calculator: {e}", file=sys.stderr)
        return 1

    if args.md:
        out_text = render_markdown(rec)
    elif args.json:
        out_text = json.dumps(rec, indent=2) + "\n"
    else:
        out_text = _dump_yaml(rec)

    if args.output:
        args.output.write_text(out_text)
        print(f"wrote {args.output}")
    else:
        sys.stdout.write(out_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
