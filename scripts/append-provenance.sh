#!/usr/bin/env bash
#
# append-provenance.sh — attach provenance fields to an existing run-summary.yaml.
#
# Usage:
#   scripts/append-provenance.sh <run-dir>
#
# Reads the same EVAL_* env vars as new-run.sh:
#   EVAL_RUNNER, EVAL_AGENT, EVAL_MODEL
#   EVAL_TERMINAL_SESSION_ID, EVAL_AGENT_SESSION_ID
#   EVAL_TRANSCRIPT_PATH, EVAL_COMMAND_LOG_PATH, EVAL_SESSION_REPLAY_NOTES
#   EVAL_TARGET_REPO_PATH, EVAL_TARGET_REPO_REF, EVAL_TARGET_REPO_COMMIT
#   EVAL_PROVENANCE_SOURCE (default: "manual")
#
# Only overwrites fields that are currently empty — never clobbers existing
# provenance values. Use this to upgrade legacy runs without lying about
# what was captured.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/append-provenance.sh <run-dir>" >&2
  exit 1
fi

RUN_DIR="$1"
SUMMARY="${RUN_DIR}/run-summary.yaml"

if [[ ! -f "${SUMMARY}" ]]; then
  echo "No run-summary.yaml at ${SUMMARY}" >&2
  exit 1
fi

python3 - "$SUMMARY" <<'PY'
import os, sys, pathlib, re

summary_path = pathlib.Path(sys.argv[1])
text = summary_path.read_text()

# Schema migration: if legacy file lacks new fields, inject them under provenance:
new_keys = [
    ("provenance_source", ""),
    ("partial", False),
    ("transcript_path", ""),
    ("command_log_path", ""),
    ("session_replay_notes", ""),
]

for key, default in new_keys:
    if re.search(rf'^\s*{re.escape(key)}:\s', text, re.MULTILINE):
        continue
    # Insert right after `  captured:` line if present, else after `provenance:`
    anchor = re.search(r'^\s*captured:\s*(?:true|false)\s*$', text, re.MULTILINE)
    if not anchor:
        anchor = re.search(r'^provenance:\s*$', text, re.MULTILINE)
    if not anchor:
        continue
    insert_at = anchor.end()
    if isinstance(default, bool):
        line = f'\n  {key}: {"true" if default else "false"}'
    else:
        line = f'\n  {key}: ""'
    text = text[:insert_at] + line + text[insert_at:]

# Also make sure `manifest_path` exists under evidence:
if not re.search(r'^\s*manifest_path:\s', text, re.MULTILINE):
    anchor = re.search(r'^\s*logs_copied:\s*(?:true|false)\s*$', text, re.MULTILINE)
    if anchor:
        text = text[:anchor.end()] + '\n  manifest_path: "artifacts/manifest.yaml"' + text[anchor.end():]

# Field-by-field append (only if currently empty string)
def env(name, default=""):
    v = os.environ.get(name, "")
    return v if v else default

pairs = [
    ("runner",               env("EVAL_RUNNER")),
    ("agent",                env("EVAL_AGENT")),
    ("model",                env("EVAL_MODEL")),
    ("terminal_session_id",  env("EVAL_TERMINAL_SESSION_ID")),
    ("agent_session_id",     env("EVAL_AGENT_SESSION_ID")),
    ("transcript_path",      env("EVAL_TRANSCRIPT_PATH")),
    ("command_log_path",     env("EVAL_COMMAND_LOG_PATH")),
    ("session_replay_notes", env("EVAL_SESSION_REPLAY_NOTES")),
    ("target_repo_path",     env("EVAL_TARGET_REPO_PATH")),
    ("target_repo_ref",      env("EVAL_TARGET_REPO_REF")),
    ("target_repo_commit",   env("EVAL_TARGET_REPO_COMMIT")),
]

any_filled = False
for key, value in pairs:
    if not value:
        continue
    pattern = re.compile(rf'(^\s*{re.escape(key)}:\s*)""\s*$', re.MULTILINE)
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    new_text, n = pattern.subn(lambda m, e=escaped: f'{m.group(1)}"{e}"', text, count=1)
    if n:
        text = new_text
        any_filled = True

# Mark provenance_source if still empty
source = env("EVAL_PROVENANCE_SOURCE", "manual")
text = re.sub(
    r'(^\s*provenance_source:\s*)""\s*$',
    lambda m: f'{m.group(1)}"{source}"',
    text, count=1, flags=re.MULTILINE,
)

# Decide `partial` and `captured` heuristically — only if env asked us to or they were empty.
# We never downgrade an existing `captured: true` to false.
def still_empty(key):
    return bool(re.search(rf'^\s*{re.escape(key)}:\s*""\s*$', text, re.MULTILINE))

critical = ["runner", "agent", "model"]
missing_any = any(still_empty(k) for k in critical)
text = re.sub(
    r'(^\s*partial:\s*)(true|false)\s*$',
    lambda m: f'{m.group(1)}{"true" if missing_any else "false"}',
    text, count=1, flags=re.MULTILINE,
)

if any_filled and not missing_any:
    text = re.sub(
        r'(^\s*captured:\s*)false\s*$',
        lambda m: f'{m.group(1)}true',
        text, count=1, flags=re.MULTILINE,
    )

summary_path.write_text(text)
print(f"Updated provenance in {summary_path}")
PY
