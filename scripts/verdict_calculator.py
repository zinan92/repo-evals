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

# A claim status is "with_concerns" if it passed but with caveats — these
# count toward coverage but earn fewer points and trigger area-based
# penalties (privacy/security concerns hurt more than cosmetic ones).
WITH_CONCERNS_STATUSES = {"passed_with_concerns", "pass-with-concerns"}


# --- 0-100 score model ---------------------------------------------------
#
# The 4-bucket model (unusable/usable/reusable/recommendable) was too
# coarse — once readers crossed `usable` everything looked OK. The score
# model gives every dossier an explicit 0-100 number with a clear
# 60-is-pass threshold + 6 named tiers.
#
# Score is built up additively from explainable components, so every
# point can be traced back to a piece of evidence.

SCORE_BASE = 40         # given for "project is real, not archived, has license"
SCORE_STATIC_CAP = 30   # ±30 from claim outcomes
SCORE_MAINTAINER_CAP = 15
SCORE_ECOSYSTEM_CAP = 15

# Tier thresholds + bilingual labels.
TIERS: tuple[dict[str, object], ...] = (
    {"min": 90, "key": "recommend", "emoji": "⭐",
     "en": "Recommend", "zh": "公开推荐",
     "blurb_en": "Recommend to strangers, blog posts, PR integrations.",
     "blurb_zh": "可以推荐给陌生人 / 写博客 / 写进 PR 集成。"},
    {"min": 80, "key": "team", "emoji": "🏭",
     "en": "Team-ready", "zh": "团队就绪",
     "blurb_en": "Safe to depend on in team / production pipelines.",
     "blurb_zh": "团队 / 生产 pipeline 可以依赖。"},
    {"min": 70, "key": "self", "emoji": "🛠",
     "en": "Self-use OK", "zh": "自用 OK",
     "blurb_en": "Use it yourself; not yet ready to recommend to others.",
     "blurb_zh": "你自己日常用没问题，还不到推荐给陌生人的程度。"},
    {"min": 60, "key": "try", "emoji": "🧪",
     "en": "Try once", "zh": "试一下",
     "blurb_en": "Install and try; do not put in your critical path yet.",
     "blurb_zh": "装上玩一下行；别让生产环境 / 工作流依赖它。"},
    {"min": 40, "key": "risky", "emoji": "⚠️",
     "en": "Risky", "zh": "慎用",
     "blurb_en": "Runs but has unverified critical issues; expect surprises.",
     "blurb_zh": "跑得通但有未验证的关键问题，会有意外。"},
    {"min": 0, "key": "broken", "emoji": "🛑",
     "en": "Don't use", "zh": "别用",
     "blurb_en": "Won't install / core feature broken / archived.",
     "blurb_zh": "装不上 / 核心功能坏 / 已 archived。"},
)


def tier_for_score(score: int) -> dict[str, object]:
    """Look up the tier dict for a given 0-100 score."""
    for t in TIERS:
        if score >= t["min"]:  # type: ignore[operator]
            return t
    return TIERS[-1]


def _stars_band_points(stars: int) -> int:
    """Ecosystem validation from GitHub stars. Capped at +12.

    Idea: stars are 'others have already verified this' evidence —
    weak per-user but strong in aggregate. We cap at +12 of the +15
    ecosystem budget so other validators can fill the remainder.
    """
    if stars > 50_000:
        return 12
    if stars >= 15_000:
        return 9
    if stars >= 5_000:
        return 6
    if stars >= 1_000:
        return 3
    return 0


def compute_score(inp: dict, claims: list[dict]) -> dict:
    """Compute a 0-100 quality score from claim statuses + repo metadata.

    Reads the same `inp` dict that compute_verdict() reads, plus a few
    optional fields that may be supplied via repo.yaml or derived in
    render_verdict_html._derive_verdict_input():

      stars                       (int)         — GitHub stargazers
      archived                    (bool)        — repo archived flag
      has_license                 (bool)        — LICENSE file present
      multilingual_readme         (bool)        — ≥2 languages
      release_pipeline_score      (0..3)        — see docs/IMPROVEMENT_PLAN.md
      eval_discipline_score       (0..3)        — repo-internal eval/ harness
      recently_active             (bool)        — release in last 90 days

    Returns a dict with `score`, `tier`, and a `breakdown` mapping
    showing where every point came from. The breakdown is what makes
    the score auditable — readers can challenge any number.
    """

    breakdown: dict[str, int] = {"base": SCORE_BASE}
    score = SCORE_BASE

    # --- Static eval contribution (claim-by-claim) ----------------------
    static_delta = 0
    privacy_concern_count = 0
    for c in claims:
        prio = str(c.get("priority", "medium")).strip().lower()
        status = str(c.get("status", "untested")).strip().lower()
        area = str(c.get("area", "") or "").strip().lower()
        if prio == "critical":
            if status in PASS_STATUSES and status not in WITH_CONCERNS_STATUSES:
                static_delta += 5
            elif status in WITH_CONCERNS_STATUSES:
                static_delta += 3
            elif status in FAIL_STATUSES:
                static_delta -= 10
            elif status in UNTESTED_STATUSES:
                static_delta -= 3
        elif prio == "high":
            if status in PASS_STATUSES and status not in WITH_CONCERNS_STATUSES:
                static_delta += 2
            elif status in WITH_CONCERNS_STATUSES:
                static_delta += 1
            elif status in FAIL_STATUSES:
                static_delta -= 4
        # Privacy / security concerns get an extra penalty regardless of
        # priority, because user-facing risk dwarfs categorical priority.
        if status in WITH_CONCERNS_STATUSES and (
            "privacy" in area or "security" in area or "safety" in area
        ):
            privacy_concern_count += 1

    static_delta = max(-SCORE_STATIC_CAP, min(SCORE_STATIC_CAP, static_delta))
    breakdown["static_eval"] = static_delta
    score += static_delta

    # --- Maintainer evidence (CI, eval, multi-platform release) --------
    maint = 0
    if int(inp.get("release_pipeline_score", 0) or 0) >= 2:
        maint += 5
    if int(inp.get("eval_discipline_score", 0) or 0) >= 2:
        maint += 5
    if bool(inp.get("recently_active", False)):
        maint += 3
    if bool(inp.get("multilingual_readme", False)):
        maint += 2
    maint = min(SCORE_MAINTAINER_CAP, maint)
    breakdown["maintainer_evidence"] = maint
    score += maint

    # --- Ecosystem validation (stars-based, conservative) --------------
    eco = _stars_band_points(int(inp.get("stars", 0) or 0))
    eco = min(SCORE_ECOSYSTEM_CAP, eco)
    breakdown["ecosystem"] = eco
    score += eco

    # --- Penalties -----------------------------------------------------
    penalties = 0
    if privacy_concern_count:
        penalties -= 3 * privacy_concern_count
    if not bool(inp.get("has_license", True)):
        penalties -= 5
    if bool(inp.get("archived", False)):
        penalties -= 50
    breakdown["penalties"] = penalties
    score += penalties

    # Clamp + tier
    score = max(0, min(100, score))
    tier = tier_for_score(score)

    return {
        "score": score,
        "breakdown": breakdown,
        "tier_key": tier["key"],
        "tier_emoji": tier["emoji"],
        "tier_en": tier["en"],
        "tier_zh": tier["zh"],
        "tier_blurb_en": tier["blurb_en"],
        "tier_blurb_zh": tier["blurb_zh"],
    }


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

    # Ceiling: trigger precision / recall (if reported) must clear threshold.
    # A skill that Claude never fires on (or fires on the wrong queries) has
    # zero user value regardless of how well the code under it works.
    trigger_threshold = 0.7
    trig_p = inp.get("trigger_precision")
    trig_r = inp.get("trigger_recall")
    if isinstance(trig_p, (int, float)) and trig_p < trigger_threshold:
        ceiling_reasons.append(
            f"trigger_precision={trig_p:.2f} < {trigger_threshold} "
            f"(skill fires on wrong queries) → capped at 'usable'"
        )
        bucket = cap(bucket, "usable")
    if isinstance(trig_r, (int, float)) and trig_r < trigger_threshold:
        ceiling_reasons.append(
            f"trigger_recall={trig_r:.2f} < {trigger_threshold} "
            f"(skill fails to fire when it should) → capped at 'usable'"
        )
        bucket = cap(bucket, "usable")

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

    # 0-100 score (new model). Computed alongside the legacy bucket so
    # consumers can switch over without breaking; bucket stays for
    # backward compat (existing tests, JSON sidecars, dashboards).
    score_block = compute_score(inp, claims)

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
        # New fields — score model
        "score": score_block["score"],
        "score_breakdown": score_block["breakdown"],
        "tier_key": score_block["tier_key"],
        "tier_emoji": score_block["tier_emoji"],
        "tier_en": score_block["tier_en"],
        "tier_zh": score_block["tier_zh"],
        "tier_blurb_en": score_block["tier_blurb_en"],
        "tier_blurb_zh": score_block["tier_blurb_zh"],
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
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="skip auto-rendering + opening the HTML verdict",
    )
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

    # Auto-open the HTML verdict when the input path is inside a
    # repos/<slug>/verdicts/ directory. This is the natural next step
    # after computing the verdict — the user reads the HTML, not the
    # raw numbers.
    if not args.no_html:
        _maybe_render_and_open_html(args.input)
    return 0


def _maybe_render_and_open_html(input_path: pathlib.Path) -> None:
    """If input_path sits inside repos/<slug>/verdicts/, render and open
    the HTML verdict. Fails quietly — this is a convenience, not a
    correctness-critical step."""
    try:
        resolved = input_path.resolve()
        parts = resolved.parts
        if "repos" not in parts or "verdicts" not in parts:
            return
        idx = parts.index("repos")
        if idx + 1 >= len(parts):
            return
        slug = parts[idx + 1]
        here = pathlib.Path(__file__).resolve().parent
        render_script = here / "render_verdict_html.py"
        if not render_script.exists():
            return

        import subprocess

        subprocess.run(
            ["python3", str(render_script), slug, "--open"],
            check=False,
        )
    except Exception:
        # Never let a render/open failure break the verdict calculator.
        return


if __name__ == "__main__":
    sys.exit(main())
