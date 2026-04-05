#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: scripts/new-area.sh <owner--repo> <area-slug>" >&2
  exit 1
fi

REPO_SLUG="$1"
AREA_SLUG="$2"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AREA_DIR="${BASE_DIR}/repos/${REPO_SLUG}/areas/${AREA_SLUG}"

mkdir -p \
  "${AREA_DIR}/claims" \
  "${AREA_DIR}/plans" \
  "${AREA_DIR}/verdicts" \
  "${AREA_DIR}/fixtures" \
  "${AREA_DIR}/runs"

if [[ ! -f "${AREA_DIR}/area.yaml" ]]; then
  cp "${BASE_DIR}/templates/area/area.yaml" "${AREA_DIR}/area.yaml"
  perl -0pi -e "s/AREA_SLUG/${AREA_SLUG}/g; s/DISPLAY_NAME/${AREA_SLUG}/g" "${AREA_DIR}/area.yaml"
fi

if [[ ! -f "${AREA_DIR}/claims/claim-map.yaml" ]]; then
  cp "${BASE_DIR}/templates/repo/claim-map.yaml" "${AREA_DIR}/claims/claim-map.yaml"
fi

touch "${AREA_DIR}/fixtures/.gitkeep" "${AREA_DIR}/runs/.gitkeep"

echo "Created area scaffold at ${AREA_DIR}"
