#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: scripts/new-run.sh <owner--repo> <run-slug> [area-slug] [target-repo-path]" >&2
  echo "" >&2
  echo "Optional provenance env vars (auto-populated into run-summary.yaml):" >&2
  echo "  EVAL_RUNNER, EVAL_AGENT, EVAL_MODEL" >&2
  echo "  EVAL_TERMINAL_SESSION_ID, EVAL_AGENT_SESSION_ID" >&2
  echo "  EVAL_TRANSCRIPT_PATH, EVAL_COMMAND_LOG_PATH, EVAL_SESSION_REPLAY_NOTES" >&2
  exit 1
fi

REPO_SLUG="$1"
RUN_SLUG="$2"
AREA_SLUG="${3:-}"
TARGET_REPO_PATH="${4:-}"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TODAY="$(date +%F)"
EVAL_TIMESTAMP="$(date -u +%FT%TZ)"
REPO_EVALS_COMMIT="$(git -C "${BASE_DIR}" rev-parse --short HEAD 2>/dev/null || true)"
RUNNER="${EVAL_RUNNER:-}"
AGENT="${EVAL_AGENT:-}"
MODEL="${EVAL_MODEL:-}"
TERMINAL_SESSION_ID="${EVAL_TERMINAL_SESSION_ID:-}"
AGENT_SESSION_ID="${EVAL_AGENT_SESSION_ID:-}"
TRANSCRIPT_PATH="${EVAL_TRANSCRIPT_PATH:-}"
COMMAND_LOG_PATH="${EVAL_COMMAND_LOG_PATH:-}"
SESSION_REPLAY_NOTES="${EVAL_SESSION_REPLAY_NOTES:-}"
TARGET_REPO_REF=""
TARGET_REPO_COMMIT=""

if [[ -n "$AREA_SLUG" ]]; then
  ROOT_DIR="${BASE_DIR}/repos/${REPO_SLUG}/areas/${AREA_SLUG}"
else
  ROOT_DIR="${BASE_DIR}/repos/${REPO_SLUG}"
fi

RUN_DIR="${ROOT_DIR}/runs/${TODAY}/run-${RUN_SLUG}"

mkdir -p \
  "${RUN_DIR}/logs" \
  "${RUN_DIR}/artifacts" \
  "${RUN_DIR}/screenshots"

# Python helper for safe in-place YAML-ish field patching (string replace on known keys).
# Keeps dependency-free; template keys are unique so we can do key: "" → key: "value".
patch_field() {
  local file="$1"
  local key="$2"
  local value="$3"
  # Escape for perl regex / replacement
  python3 - "$file" "$key" "$value" <<'PY'
import sys, re, pathlib
path, key, value = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(path)
text = p.read_text()
# Only replace first empty occurrence: `  key: ""`
pattern = re.compile(rf'(^\s*{re.escape(key)}:\s*)""\s*$', re.MULTILINE)
def repl(m):
    # YAML-safe quote: escape backslashes and double quotes
    v = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'{m.group(1)}"{v}"'
new_text, n = pattern.subn(repl, text, count=1)
if n:
    p.write_text(new_text)
PY
}

patch_bool() {
  local file="$1"
  local key="$2"
  local value="$3"
  python3 - "$file" "$key" "$value" <<'PY'
import sys, re, pathlib
path, key, value = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(path)
text = p.read_text()
pattern = re.compile(rf'(^\s*{re.escape(key)}:\s*)(true|false)\s*$', re.MULTILINE)
new_text, n = pattern.subn(lambda m: m.group(1) + value, text, count=1)
if n:
    p.write_text(new_text)
PY
}

if [[ ! -f "${RUN_DIR}/run-summary.yaml" ]]; then
  cp "${BASE_DIR}/templates/run/run-summary.yaml" "${RUN_DIR}/run-summary.yaml"
  SUMMARY="${RUN_DIR}/run-summary.yaml"

  # Header fields
  perl -0pi -e "s/RUN_NAME/${RUN_SLUG}/g; s/YYYY-MM-DD/${TODAY}/g" "${SUMMARY}"
  if [[ -n "$AREA_SLUG" ]]; then
    perl -0pi -e "s/area: core/area: ${AREA_SLUG}/g" "${SUMMARY}"
  fi

  # Always known provenance
  patch_field "${SUMMARY}" "repo_evals_commit" "${REPO_EVALS_COMMIT}"
  patch_field "${SUMMARY}" "evaluated_at" "${EVAL_TIMESTAMP}"

  # Target repo (if path provided and is a git checkout)
  if [[ -n "${TARGET_REPO_PATH}" ]]; then
    patch_field "${SUMMARY}" "target_repo_path" "${TARGET_REPO_PATH}"
    if [[ -d "${TARGET_REPO_PATH}/.git" ]]; then
      TARGET_REPO_REF="$(git -C "${TARGET_REPO_PATH}" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
      TARGET_REPO_COMMIT="$(git -C "${TARGET_REPO_PATH}" rev-parse --short HEAD 2>/dev/null || true)"
      patch_field "${SUMMARY}" "target_repo_ref" "${TARGET_REPO_REF}"
      patch_field "${SUMMARY}" "target_repo_commit" "${TARGET_REPO_COMMIT}"
    fi
  fi

  # Runtime env provenance
  CAPTURED_ANYTHING=0
  for pair in "runner:${RUNNER}" "agent:${AGENT}" "model:${MODEL}" \
              "terminal_session_id:${TERMINAL_SESSION_ID}" \
              "agent_session_id:${AGENT_SESSION_ID}" \
              "transcript_path:${TRANSCRIPT_PATH}" \
              "command_log_path:${COMMAND_LOG_PATH}" \
              "session_replay_notes:${SESSION_REPLAY_NOTES}"; do
    key="${pair%%:*}"
    val="${pair#*:}"
    if [[ -n "${val}" ]]; then
      patch_field "${SUMMARY}" "${key}" "${val}"
      CAPTURED_ANYTHING=1
    fi
  done

  if [[ ${CAPTURED_ANYTHING} -eq 1 ]]; then
    patch_bool  "${SUMMARY}" "captured" "true"
    patch_field "${SUMMARY}" "provenance_source" "auto"
  else
    # No env-captured fields — mark provenance as manual so reviewers know
    # this run expects a human to fill it in (not legacy).
    patch_field "${SUMMARY}" "provenance_source" "manual"
    patch_bool  "${SUMMARY}" "partial" "true"
  fi
fi

if [[ ! -f "${RUN_DIR}/business-notes.md" ]]; then
  cp "${BASE_DIR}/templates/run/business-notes.md" "${RUN_DIR}/business-notes.md"
fi

echo "Created run scaffold at ${RUN_DIR}"
