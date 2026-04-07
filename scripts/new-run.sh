#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: scripts/new-run.sh <owner--repo> <run-slug> [area-slug] [target-repo-path]" >&2
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

if [[ ! -f "${RUN_DIR}/run-summary.yaml" ]]; then
  cp "${BASE_DIR}/templates/run/run-summary.yaml" "${RUN_DIR}/run-summary.yaml"
  perl -0pi -e "s/RUN_NAME/${RUN_SLUG}/g; s/YYYY-MM-DD/${TODAY}/g" "${RUN_DIR}/run-summary.yaml"
  if [[ -n "$AREA_SLUG" ]]; then
    perl -0pi -e "s/area: core/area: ${AREA_SLUG}/g" "${RUN_DIR}/run-summary.yaml"
  fi
  perl -0pi -e "s#repo_evals_commit: \"\"#repo_evals_commit: \"${REPO_EVALS_COMMIT}\"#g; s#evaluated_at: \"\"#evaluated_at: \"${EVAL_TIMESTAMP}\"#g" "${RUN_DIR}/run-summary.yaml"
fi

if [[ ! -f "${RUN_DIR}/business-notes.md" ]]; then
  cp "${BASE_DIR}/templates/run/business-notes.md" "${RUN_DIR}/business-notes.md"
fi

if [[ -n "${TARGET_REPO_PATH}" && -d "${TARGET_REPO_PATH}/.git" ]]; then
  TARGET_REPO_REF="$(git -C "${TARGET_REPO_PATH}" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  TARGET_REPO_COMMIT="$(git -C "${TARGET_REPO_PATH}" rev-parse --short HEAD 2>/dev/null || true)"
  perl -0pi -e "s#target_repo_path: \"\"#target_repo_path: \"${TARGET_REPO_PATH}\"#g; s#target_repo_ref: \"\"#target_repo_ref: \"${TARGET_REPO_REF}\"#g; s#target_repo_commit: \"\"#target_repo_commit: \"${TARGET_REPO_COMMIT}\"#g" "${RUN_DIR}/run-summary.yaml"
fi

if [[ -n "${RUNNER}" || -n "${AGENT}" || -n "${MODEL}" || -n "${TERMINAL_SESSION_ID}" || -n "${AGENT_SESSION_ID}" ]]; then
  perl -0pi -e "s#runner: \"\"#runner: \"${RUNNER}\"#g; s#agent: \"\"#agent: \"${AGENT}\"#g; s#model: \"\"#model: \"${MODEL}\"#g; s#terminal_session_id: \"\"#terminal_session_id: \"${TERMINAL_SESSION_ID}\"#g; s#agent_session_id: \"\"#agent_session_id: \"${AGENT_SESSION_ID}\"#g; s#captured: false#captured: true#g" "${RUN_DIR}/run-summary.yaml"
fi

echo "Created run scaffold at ${RUN_DIR}"
