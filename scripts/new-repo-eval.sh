#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/new-repo-eval.sh <owner/repo> [repo_type]" >&2
  exit 1
fi

TARGET="$1"
REPO_TYPE="${2:-skill}"

if [[ "$TARGET" != */* ]]; then
  echo "Expected <owner/repo>, got: $TARGET" >&2
  exit 1
fi

OWNER="${TARGET%%/*}"
REPO="${TARGET##*/}"
SLUG="${OWNER}--${REPO}"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_DIR="${BASE_DIR}/repos/${SLUG}"
TODAY="$(date +%F)"

mkdir -p \
  "${REPO_DIR}/claims" \
  "${REPO_DIR}/plans" \
  "${REPO_DIR}/verdicts" \
  "${REPO_DIR}/fixtures" \
  "${REPO_DIR}/runs" \
  "${REPO_DIR}/areas"

if [[ ! -f "${REPO_DIR}/repo.yaml" ]]; then
  cp "${BASE_DIR}/templates/repo/repo.yaml" "${REPO_DIR}/repo.yaml"
  perl -0pi -e "s/OWNER/${OWNER}/g; s/REPO/${REPO}/g; s/DISPLAY_NAME/${REPO}/g" "${REPO_DIR}/repo.yaml"
  perl -0pi -e "s/repo_type: skill/repo_type: ${REPO_TYPE}/g" "${REPO_DIR}/repo.yaml"
fi

if [[ ! -f "${REPO_DIR}/claims/claim-map.yaml" ]]; then
  cp "${BASE_DIR}/templates/repo/claim-map.yaml" "${REPO_DIR}/claims/claim-map.yaml"
fi

PLAN_PATH="${REPO_DIR}/plans/${TODAY}-eval-plan.md"
if [[ ! -f "${PLAN_PATH}" ]]; then
  cp "${BASE_DIR}/templates/repo/eval-plan.md" "${PLAN_PATH}"
fi

VERDICT_PATH="${REPO_DIR}/verdicts/${TODAY}-final-verdict.md"
if [[ ! -f "${VERDICT_PATH}" ]]; then
  cp "${BASE_DIR}/templates/repo/final-verdict.md" "${VERDICT_PATH}"
fi

touch "${REPO_DIR}/fixtures/.gitkeep" "${REPO_DIR}/runs/.gitkeep" "${REPO_DIR}/areas/.gitkeep"

echo "Created eval scaffold at ${REPO_DIR}"
