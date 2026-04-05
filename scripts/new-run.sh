#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: scripts/new-run.sh <owner--repo> <run-slug> [area-slug]" >&2
  exit 1
fi

REPO_SLUG="$1"
RUN_SLUG="$2"
AREA_SLUG="${3:-}"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TODAY="$(date +%F)"

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
fi

if [[ ! -f "${RUN_DIR}/business-notes.md" ]]; then
  cp "${BASE_DIR}/templates/run/business-notes.md" "${RUN_DIR}/business-notes.md"
fi

echo "Created run scaffold at ${RUN_DIR}"
