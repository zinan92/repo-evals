#!/usr/bin/env python3
"""trigger_test.py — measure how reliably a skill fires when (and only when) it should.

A skill's value can only materialize if Claude actually loads it at the right
moment. Anthropic's own skill-creator guide flags under-triggering as the
common failure mode; over-triggering (firing on irrelevant queries) is the
symmetric failure. This script probes both.

How it works
------------

1. Parse the target skill's SKILL.md frontmatter (name + description).
2. Generate two phrase banks:
   - ``should_trigger`` — user phrases the skill SHOULD fire on
   - ``should_not_trigger`` — user phrases it should NOT fire on
   Phrases come from ``fixtures/trigger-phrases/<domain>.yaml`` if present,
   otherwise from a small CLIProxyAPI-generated set (~20 phrases total).
3. For each phrase, present Claude with a mini skill registry containing
   the target skill + a few decoys, ask which (if any) should trigger,
   and parse the JSON decision.
4. Tally a confusion matrix; report precision + recall + bucket-ready
   ceiling signal.

Output
------

Writes ``<skill-dir>/trigger-test-<date>.json`` with full per-phrase results,
and prints a summary table. Exit code 0 if precision ≥ threshold, else 1.

Usage
-----

    scripts/trigger_test.py ~/.claude/skills/eval-repo
    scripts/trigger_test.py ~/.claude/skills/eval-repo --phrases fixtures/trigger-phrases/eval-repo.yaml
    scripts/trigger_test.py ~/.claude/skills/eval-repo --threshold 0.8

Environment
-----------

    REPO_EVALS_API_ENDPOINT  default http://localhost:8317/v1/messages
    REPO_EVALS_API_KEY       default sk-cliproxy-wendy
    REPO_EVALS_MODEL         default claude-haiku-4-5-20251001
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


REPO_EVALS_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_ENDPOINT = os.environ.get(
    "REPO_EVALS_API_ENDPOINT", "http://localhost:8317/v1/messages"
)
DEFAULT_API_KEY = os.environ.get("REPO_EVALS_API_KEY", "sk-cliproxy-wendy")
DEFAULT_MODEL = os.environ.get(
    "REPO_EVALS_MODEL", "claude-haiku-4-5-20251001"
)
DEFAULT_THRESHOLD = 0.7
DEFAULT_PHRASE_COUNT = 10  # per direction

# A small handful of real skills to act as decoys. The goal is to mix
# plausible alternatives into the registry so Claude has to discriminate
# rather than picking the only option. Pulled from common user libraries.
DECOY_SKILLS: list[dict[str, str]] = [
    {
        "name": "commit-push-pr",
        "description": "Creates a git commit, pushes the branch, and opens a pull request. Use when the user wants to commit changes and open a PR.",
    },
    {
        "name": "finviz-screener",
        "description": "Builds a FinViz stock screener URL from a natural-language query. Use when the user wants to filter stocks by financial criteria.",
    },
    {
        "name": "seedance-storyboard",
        "description": "Turns an idea into a Seedance 2.0 video storyboard prompt. Use when the user wants to generate a short video or animated clip.",
    },
    {
        "name": "lark-doc",
        "description": "Creates and edits Lark (Feishu) cloud documents via the Lark API. Use when the user wants to write or update a Lark doc.",
    },
]


# ---- data types ----------------------------------------------------------


@dataclass(frozen=True)
class Skill:
    name: str
    description: str


@dataclass
class PhraseOutcome:
    phrase: str
    expected: str  # "should_trigger" | "should_not_trigger"
    picked_skill: str | None
    raw_response: str
    verdict: str  # "TP" | "FP" | "TN" | "FN"


@dataclass
class TriggerReport:
    skill: Skill
    outcomes: list[PhraseOutcome] = field(default_factory=list)

    @property
    def tp(self) -> int:
        return sum(1 for o in self.outcomes if o.verdict == "TP")

    @property
    def fp(self) -> int:
        return sum(1 for o in self.outcomes if o.verdict == "FP")

    @property
    def tn(self) -> int:
        return sum(1 for o in self.outcomes if o.verdict == "TN")

    @property
    def fn(self) -> int:
        return sum(1 for o in self.outcomes if o.verdict == "FN")

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return (self.tp / denom) if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return (self.tp / denom) if denom else 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "skill_name": self.skill.name,
            "skill_description": self.skill.description,
            "confusion_matrix": {
                "TP": self.tp,
                "FP": self.fp,
                "TN": self.tn,
                "FN": self.fn,
            },
            "precision": round(self.precision, 3),
            "recall": round(self.recall, 3),
            "outcomes": [
                {
                    "phrase": o.phrase,
                    "expected": o.expected,
                    "picked_skill": o.picked_skill,
                    "verdict": o.verdict,
                }
                for o in self.outcomes
            ],
        }


# ---- skill parsing -------------------------------------------------------


FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<body>.*?)\n---\s*(\n|$)",
    re.DOTALL,
)


def parse_skill(skill_dir: Path) -> Skill:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"No SKILL.md at {skill_md}", file=sys.stderr)
        sys.exit(2)

    text = skill_md.read_text()
    match = FRONTMATTER_RE.match(text)
    if not match:
        print(
            f"SKILL.md at {skill_md} has no frontmatter block",
            file=sys.stderr,
        )
        sys.exit(2)

    if yaml is None:
        print("PyYAML required — pip install pyyaml", file=sys.stderr)
        sys.exit(2)

    meta = yaml.safe_load(match.group("body")) or {}
    name = str(meta.get("name") or skill_dir.name)
    description = str(meta.get("description") or "").strip()
    if not description:
        print(
            f"SKILL.md {skill_md} has no 'description' — cannot test triggering",
            file=sys.stderr,
        )
        sys.exit(2)
    return Skill(name=name, description=description)


# ---- phrase generation ---------------------------------------------------


def load_phrases_from_fixture(path: Path) -> tuple[list[str], list[str]]:
    if yaml is None:
        return [], []
    data = yaml.safe_load(path.read_text()) or {}
    return (
        list(data.get("should_trigger") or []),
        list(data.get("should_not_trigger") or []),
    )


def generate_phrases_via_llm(
    skill: Skill,
    *,
    count: int,
    endpoint: str,
    api_key: str,
    model: str,
) -> tuple[list[str], list[str]]:
    prompt = (
        f"Below is a Claude Code skill's metadata:\n\n"
        f"Name: {skill.name}\n"
        f'Description: "{skill.description}"\n\n'
        f"Generate exactly {count} realistic user phrases that SHOULD cause "
        f"Claude to load this skill (users asking for what the skill does), "
        f"and exactly {count} phrases that should NOT (adjacent but unrelated "
        f"tasks — e.g. for a 'git commit' skill, generate 'git rebase' or "
        f"'push to staging'). Vary phrasing, language (mix English / Chinese "
        f"since users are bilingual), verbosity, and directness.\n\n"
        f"Return ONLY a JSON object of the exact shape:\n"
        f'{{"should_trigger": ["...", "..."], "should_not_trigger": ["...", "..."]}}\n'
        f"No prose, no code fences, just the JSON object."
    )
    text, _, _, _ = call_claude(
        prompt,
        model=model,
        endpoint=endpoint,
        api_key=api_key,
        max_tokens=2048,
    )
    try:
        data = json.loads(_extract_json(text))
    except (json.JSONDecodeError, ValueError) as exc:
        print(
            f"LLM did not return valid JSON for phrase generation: {exc}\n"
            f"Response preview: {text[:200]}",
            file=sys.stderr,
        )
        sys.exit(2)
    should = [str(p) for p in (data.get("should_trigger") or [])][:count]
    should_not = [str(p) for p in (data.get("should_not_trigger") or [])][:count]
    return should, should_not


def _extract_json(text: str) -> str:
    """Find the first top-level JSON object in a blob of text."""
    stripped = text.strip()
    if stripped.startswith("```"):
        # Strip markdown fence
        stripped = re.sub(r"^```\w*\n", "", stripped)
        stripped = re.sub(r"\n```\s*$", "", stripped)
    # If the response has prose before/after, extract first {..} block.
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return stripped
    return stripped[start : end + 1]


# ---- decision call (the actual triggering probe) ------------------------


DECISION_PROMPT_TEMPLATE = """You are Claude Code's skill router. Given a user message and a list of available skills, decide which single skill (if any) should be loaded to handle the message.

Available skills:
{skills_block}

Decision rules:
- Pick the skill whose description best matches the user's intent.
- If no skill clearly applies, pick null.
- Do not invent new skills.

User message: "{phrase}"

Respond with ONLY a JSON object of this exact shape (no prose, no code fence):
{{"skill_to_use": "<exact-skill-name-or-null>", "reason": "<one short sentence>"}}
"""


def run_decision(
    phrase: str,
    target: Skill,
    decoys: list[dict[str, str]],
    *,
    endpoint: str,
    api_key: str,
    model: str,
) -> tuple[str | None, str]:
    registry = [{"name": target.name, "description": target.description}]
    registry.extend(decoys)
    random.shuffle(registry)

    skills_block = "\n".join(
        f"- {_esc(s['name'])}: {_esc(s['description'])}" for s in registry
    )
    prompt = DECISION_PROMPT_TEMPLATE.format(
        skills_block=skills_block, phrase=phrase.replace('"', '\\"')
    )
    raw, _, _, _ = call_claude(
        prompt,
        model=model,
        endpoint=endpoint,
        api_key=api_key,
        max_tokens=256,
    )
    try:
        data = json.loads(_extract_json(raw))
    except (json.JSONDecodeError, ValueError):
        return None, raw  # treat unparseable as no-pick

    picked = data.get("skill_to_use")
    if picked in ("null", "None", ""):
        picked = None
    return (str(picked) if picked is not None else None), raw


def _esc(s: str) -> str:
    return s.replace("\n", " ").strip()


# ---- API call ------------------------------------------------------------


def call_claude(
    prompt: str,
    *,
    model: str,
    endpoint: str,
    api_key: str,
    max_tokens: int = 1024,
) -> tuple[str, int, int, float]:
    body = json.dumps(
        {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        print(f"API unreachable at {endpoint}: {exc}", file=sys.stderr)
        sys.exit(2)
    elapsed = time.monotonic() - start
    payload = json.loads(raw)
    content = payload.get("content", [])
    text = "".join(p.get("text", "") for p in content if isinstance(p, dict))
    usage = payload.get("usage", {})
    return (
        text,
        int(usage.get("input_tokens", 0)),
        int(usage.get("output_tokens", 0)),
        elapsed,
    )


# ---- main driver --------------------------------------------------------


def run_trigger_test(
    skill: Skill,
    should_trigger: list[str],
    should_not_trigger: list[str],
    *,
    endpoint: str,
    api_key: str,
    model: str,
) -> TriggerReport:
    report = TriggerReport(skill=skill)

    for phrase in should_trigger:
        picked, raw = run_decision(
            phrase, skill, DECOY_SKILLS,
            endpoint=endpoint, api_key=api_key, model=model,
        )
        verdict = "TP" if picked == skill.name else "FN"
        report.outcomes.append(
            PhraseOutcome(
                phrase=phrase,
                expected="should_trigger",
                picked_skill=picked,
                raw_response=raw,
                verdict=verdict,
            )
        )

    for phrase in should_not_trigger:
        picked, raw = run_decision(
            phrase, skill, DECOY_SKILLS,
            endpoint=endpoint, api_key=api_key, model=model,
        )
        verdict = "FP" if picked == skill.name else "TN"
        report.outcomes.append(
            PhraseOutcome(
                phrase=phrase,
                expected="should_not_trigger",
                picked_skill=picked,
                raw_response=raw,
                verdict=verdict,
            )
        )

    return report


def print_summary(report: TriggerReport) -> None:
    print()
    print(f"Skill: {report.skill.name}")
    print(f"Confusion matrix  TP={report.tp}  FP={report.fp}  TN={report.tn}  FN={report.fn}")
    print(f"Precision: {report.precision:.2%}  (target skill is correctly picked when we expected it)")
    print(f"Recall:    {report.recall:.2%}  (target skill actually fires on should-trigger phrases)")
    print()

    for section_name, expected in (
        ("should_trigger",     "should_trigger"),
        ("should_not_trigger", "should_not_trigger"),
    ):
        print(f"--- {section_name} ---")
        for o in report.outcomes:
            if o.expected != expected:
                continue
            mark = {"TP": "✅", "FN": "❌", "TN": "✅", "FP": "❌"}[o.verdict]
            picked = o.picked_skill or "(none)"
            print(f"  {mark} [{o.verdict}] picked={picked}  phrase={o.phrase!r}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", help="Path to a skill directory containing SKILL.md")
    parser.add_argument(
        "--phrases",
        default=None,
        help="YAML fixture with {should_trigger: [...], should_not_trigger: [...]}",
    )
    parser.add_argument("--count", type=int, default=DEFAULT_PHRASE_COUNT)
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Pass threshold for BOTH precision and recall (default {DEFAULT_THRESHOLD})",
    )
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--output",
        default=None,
        help="Where to write the JSON report (default: <skill-dir>/trigger-test-<date>.json)",
    )
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve()
    skill = parse_skill(skill_dir)

    if args.phrases:
        fixture_path = Path(args.phrases).expanduser().resolve()
        should, should_not = load_phrases_from_fixture(fixture_path)
    else:
        print("No fixture given — generating phrases via LLM ...")
        should, should_not = generate_phrases_via_llm(
            skill,
            count=args.count,
            endpoint=args.endpoint,
            api_key=args.api_key,
            model=args.model,
        )
        if not should or not should_not:
            print(
                "LLM phrase generation returned empty banks — cannot proceed",
                file=sys.stderr,
            )
            return 2

    print(f"Running {len(should)} should-trigger + {len(should_not)} should-not-trigger probes ...")
    report = run_trigger_test(
        skill, should, should_not,
        endpoint=args.endpoint, api_key=args.api_key, model=args.model,
    )
    print_summary(report)

    today = time.strftime("%Y-%m-%d")
    out_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else skill_dir / f"trigger-test-{today}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report.as_dict(), indent=2, ensure_ascii=False))
    print(f"Report written to {out_path}")

    if report.precision < args.threshold or report.recall < args.threshold:
        print(
            f"FAIL: precision={report.precision:.2%} or recall={report.recall:.2%} "
            f"below threshold {args.threshold:.0%}",
            file=sys.stderr,
        )
        return 1
    print(f"PASS: precision and recall both ≥ {args.threshold:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
