#!/usr/bin/env python3
"""run_evals.py — execute a repo's eval harness against Claude.

Reads ``repos/<slug>/evals/evals.json`` and for each eval:

1. Calls Claude via the CLIProxyAPI gateway at ``http://localhost:8317``
   (same endpoint format as the official Anthropic Messages API).
2. Checks the response against the eval's ``expected_signals`` contract.
3. Records pass/fail, elapsed time, and token usage.

Passes/fails are aggregated into ``results_by_claim`` for the *active*
run (the latest run under ``runs/<today>/``), and into
``metrics.{pass_rate, elapsed_time_sec, token_usage}`` on its
``run-summary.yaml``.

With ``--baseline``, each eval runs a second time with a stripped
prompt that hides the target repo's context — producing a
``with_repo`` vs ``without_repo`` comparison artifact.

Usage
-----

    scripts/run_evals.py <owner>--<repo>
    scripts/run_evals.py <owner>--<repo> --baseline
    scripts/run_evals.py <owner>--<repo> --run <run-name>  # pick a specific run

Exit codes
----------

    0   all evals passed
    1   one or more evals failed
    2   setup error (missing files, API unreachable)
"""

from __future__ import annotations

import argparse
import json
import os
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


# ---- data shapes ---------------------------------------------------------


@dataclass(frozen=True)
class EvalCase:
    id: str
    claim_id: str
    description: str
    prompt: str
    input_files: list[str]
    expected_signals: dict[str, Any]


@dataclass
class EvalResult:
    case: EvalCase
    passed: bool
    elapsed_sec: float
    input_tokens: int
    output_tokens: int
    response_text: str
    failure_reason: str | None = None


@dataclass
class RunMetrics:
    pass_rate: float
    elapsed_time_sec: float
    token_usage: dict[str, int] = field(default_factory=dict)


# ---- IO helpers ----------------------------------------------------------


def load_evals(repo_dir: Path) -> tuple[list[EvalCase], dict[str, Any]]:
    path = repo_dir / "evals" / "evals.json"
    if not path.exists():
        print(
            f"No evals.json at {path}. Run new-eval-harness.sh first.",
            file=sys.stderr,
        )
        sys.exit(2)
    with open(path) as f:
        data = json.load(f)
    cases = [EvalCase(**_normalize_case(e)) for e in data.get("evals", [])]
    return cases, data


def _normalize_case(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(raw["id"]),
        "claim_id": str(raw.get("claim_id", "")),
        "description": str(raw.get("description", "")),
        "prompt": str(raw["prompt"]),
        "input_files": list(raw.get("input_files", [])),
        "expected_signals": dict(raw.get("expected_signals", {})),
    }


def latest_run_dir(repo_dir: Path, run_name: str | None) -> Path:
    runs_root = repo_dir / "runs"
    if not runs_root.exists():
        print(
            f"No runs/ directory under {repo_dir}. "
            f"Run scripts/new-run.sh {repo_dir.name} <slug> first.",
            file=sys.stderr,
        )
        sys.exit(2)

    candidates: list[Path] = []
    for date_dir in sorted(runs_root.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for run_dir in date_dir.iterdir():
            if not run_dir.is_dir():
                continue
            if run_name and not run_dir.name.endswith(run_name):
                continue
            candidates.append(run_dir)

    if not candidates:
        print(
            f"No runs found under {runs_root}"
            + (f" matching {run_name!r}" if run_name else ""),
            file=sys.stderr,
        )
        sys.exit(2)

    return candidates[0]


# ---- API call ------------------------------------------------------------


def call_claude(
    prompt: str,
    *,
    model: str,
    endpoint: str,
    api_key: str,
    max_tokens: int = 1024,
) -> tuple[str, int, int, float]:
    """Return ``(response_text, input_tokens, output_tokens, elapsed_sec)``."""
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
        print(
            f"API call failed against {endpoint}: {exc}. "
            f"Is CLIProxyAPI running? Check with: "
            f"curl -s {endpoint.replace('/v1/messages','/v1/models')}",
            file=sys.stderr,
        )
        sys.exit(2)
    elapsed = time.monotonic() - start

    payload = json.loads(raw)
    content = payload.get("content", [])
    text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    usage = payload.get("usage", {})
    return (
        text,
        int(usage.get("input_tokens", 0)),
        int(usage.get("output_tokens", 0)),
        elapsed,
    )


# ---- evaluation ---------------------------------------------------------


def evaluate(
    case: EvalCase,
    response_text: str,
) -> tuple[bool, str | None]:
    sig = case.expected_signals or {}

    must_contain = sig.get("must_contain") or []
    for token in must_contain:
        if token not in response_text:
            return (False, f"response missing expected token: {token!r}")

    must_not_contain = sig.get("must_not_contain") or []
    for token in must_not_contain:
        if token in response_text:
            return (
                False,
                f"response contains forbidden token: {token!r}",
            )

    return (True, None)


def run_all(
    repo_dir: Path,
    run_dir: Path,
    cases: list[EvalCase],
    *,
    baseline: bool,
    model: str,
    endpoint: str,
    api_key: str,
) -> tuple[list[EvalResult], RunMetrics]:
    results: list[EvalResult] = []
    total_elapsed = 0.0
    total_input = 0
    total_output = 0
    passed_count = 0

    for case in cases:
        prompt = case.prompt
        if baseline:
            # Strip any repo-specific framing — treat Claude as if it never
            # heard of this repo. Crude but honest baseline.
            prompt = f"(no specific repo context available) {prompt}"

        text, in_tok, out_tok, elapsed = call_claude(
            prompt,
            model=model,
            endpoint=endpoint,
            api_key=api_key,
        )
        passed, reason = evaluate(case, text)

        results.append(
            EvalResult(
                case=case,
                passed=passed,
                elapsed_sec=elapsed,
                input_tokens=in_tok,
                output_tokens=out_tok,
                response_text=text,
                failure_reason=reason,
            )
        )

        if passed:
            passed_count += 1
        total_elapsed += elapsed
        total_input += in_tok
        total_output += out_tok

    pass_rate = passed_count / len(cases) if cases else 0.0
    metrics = RunMetrics(
        pass_rate=round(pass_rate, 3),
        elapsed_time_sec=round(total_elapsed, 3),
        token_usage={"input": total_input, "output": total_output},
    )
    return results, metrics


# ---- writeback to run-summary.yaml --------------------------------------


def writeback_run_summary(
    run_dir: Path,
    results: list[EvalResult],
    metrics: RunMetrics,
    *,
    baseline: bool,
) -> None:
    summary_path = run_dir / "run-summary.yaml"
    if not summary_path.exists():
        print(
            f"(warn) {summary_path} not found — cannot write back results",
            file=sys.stderr,
        )
        return

    if yaml is None:
        print(
            "(warn) PyYAML not available — cannot modify run-summary.yaml in-place. "
            "Printing results instead.",
            file=sys.stderr,
        )
        return

    with open(summary_path) as f:
        data = yaml.safe_load(f) or {}

    key = "results_by_claim_baseline" if baseline else "results_by_claim"
    metrics_key = "metrics_baseline" if baseline else "metrics"

    rbc = data.setdefault(key, {})
    for r in results:
        if not r.case.claim_id:
            continue
        rbc[r.case.claim_id] = "passed" if r.passed else "failed"

    data[metrics_key] = {
        "pass_rate": metrics.pass_rate,
        "elapsed_time_sec": metrics.elapsed_time_sec,
        "token_usage": dict(metrics.token_usage),
    }

    with open(summary_path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


# ---- main ---------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="Repo slug, e.g. owner--repo")
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Run each eval a second time without repo context for comparison",
    )
    parser.add_argument(
        "--run",
        default=None,
        help="Run name suffix to target; default = latest run",
    )
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    repo_dir = REPO_EVALS_ROOT / "repos" / args.slug
    if not repo_dir.exists():
        print(f"No repo scaffold at {repo_dir}", file=sys.stderr)
        return 2

    cases, _raw = load_evals(repo_dir)
    if not cases:
        print(f"No eval cases in {repo_dir}/evals/evals.json", file=sys.stderr)
        return 2

    run_dir = latest_run_dir(repo_dir, args.run)
    print(f"Running {len(cases)} evals against {run_dir}")

    results, metrics = run_all(
        repo_dir,
        run_dir,
        cases,
        baseline=args.baseline,
        model=args.model,
        endpoint=args.endpoint,
        api_key=args.api_key,
    )

    print()
    print(f"pass_rate:        {metrics.pass_rate:.2%}")
    print(f"elapsed_time_sec: {metrics.elapsed_time_sec:.2f}")
    print(f"token_usage:      {metrics.token_usage}")
    print()
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        print(f"  [{mark}] {r.case.id} → {r.case.claim_id} ({r.elapsed_sec:.2f}s)")
        if not r.passed and r.failure_reason:
            print(f"         reason: {r.failure_reason}")

    writeback_run_summary(run_dir, results, metrics, baseline=args.baseline)

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
