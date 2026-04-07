# Eval Plan — pure-cli

This is a starter plan for a deterministic command-line tool.
Before running any eval, replace every placeholder below.

## What This Repo Claims

List the concrete, testable promises — not marketing copy.

- Claim 1:
- Claim 2:
- Claim 3:

## What We Will Validate

For a pure-cli the scenarios should include at least:

- Happy path for the main command
- Every documented subcommand at least once
- At least one variation input per subcommand
- Unknown subcommand and missing-arg failure modes
- Repeatability: same input, two runs, compare stdout

## Real Inputs We Will Use

Prefer fixtures from `fixtures/registry.yaml` over inventing new inputs:

- Input A:
- Input B:
- Input C:

## How Many Times We Will Test

- Core path: N times
- Each subcommand: N times each
- Repeatability check: ≥2 back-to-back runs on the same input

## What Counts As Passing

- Exit code matches documented value
- stdout structure matches documented format
- Repeated runs produce byte-identical stdout (or differ only in known volatile fields)
- Failure modes produce non-zero exit codes + actionable stderr

## If Everything Passes, What We Can Trust

- Minimum trust level: `usable` — one happy path works
- Stretch trust level: `reusable` — all subcommands work across variations
- Remaining risk: what this plan still cannot catch
