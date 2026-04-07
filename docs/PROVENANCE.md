# Provenance

Every run in `runs/YYYY-MM-DD/run-<slug>/` should be traceable back to the
exact environment that produced it. This is what the `provenance:` block of
`run-summary.yaml` is for.

## Fields

| Field | Meaning |
|---|---|
| `provenance_source` | `auto` (captured from env by `new-run.sh`), `manual` (filled by hand), `legacy` (imported from before provenance was required), `partial` (some fields missing) |
| `captured` | `true` when at least one env-supplied field was recorded |
| `partial` | `true` when any critical field (`runner`, `agent`, `model`) is still empty |
| `runner` | Where the eval was executed (`cc`, `codex`, `pi`, ...) |
| `agent` | The agent harness name (e.g. `Claude Code`) |
| `model` | The model id (e.g. `claude-opus-4-6`) |
| `terminal_session_id` | Shell session id (optional, helps replay) |
| `agent_session_id` | Agent session id (e.g. Claude Code session UUID) |
| `repo_evals_commit` | Short git hash of this repo at eval time |
| `target_repo_path` | Local path to the target repo checkout |
| `target_repo_ref` | Branch or tag at eval time |
| `target_repo_commit` | Short git hash of the target repo |
| `evaluated_at` | UTC timestamp (ISO-8601) when the run was created |
| `transcript_path` | Path (in-repo or external) to a transcript of the session |
| `command_log_path` | Path to a command log / shell history excerpt |
| `session_replay_notes` | Free text: anything a future reviewer needs to reproduce |

## Capturing provenance automatically

Export these env vars before calling `scripts/new-run.sh`:

```bash
export EVAL_RUNNER="cc"
export EVAL_AGENT="Claude Code"
export EVAL_MODEL="claude-opus-4-6"
export EVAL_AGENT_SESSION_ID="$(uuidgen)"        # optional
export EVAL_TRANSCRIPT_PATH="logs/transcript.jsonl"   # optional
export EVAL_COMMAND_LOG_PATH="logs/commands.log"     # optional

scripts/new-run.sh owner--repo my-run-slug "" /path/to/target/repo
```

The script will:
- resolve the target repo's current branch and short commit from `.git`
- stamp `repo_evals_commit` and `evaluated_at`
- set `provenance_source: auto` and `captured: true` if env vars were present,
  otherwise `provenance_source: manual` and `partial: true`.

## Patching legacy or partial runs

Use `scripts/append-provenance.sh` to upgrade an existing run-summary file:

```bash
EVAL_PROVENANCE_SOURCE=legacy \
EVAL_SESSION_REPLAY_NOTES="imported from pre-provenance era" \
scripts/append-provenance.sh repos/owner--repo/runs/2026-01-01/run-smoke
```

Rules:

- **never clobbers** existing values — only fills empty fields
- injects any new schema keys the legacy file is missing
- marks `partial: true` if critical fields are still empty after the append
- marks `provenance_source: legacy` explicitly, so reviewers know this run
  is not lying about having full capture

## Why this matters

Without provenance:
- reviewers cannot tell whether a result is reproducible
- re-evals cannot diff against a meaningful baseline
- bucket movements over time become uninterpretable

Provenance is the minimum we need to call a repository evaluation *auditable*.
