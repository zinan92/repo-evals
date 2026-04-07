#!/usr/bin/env bash
#
# new-repo-eval.sh — scaffold a new repo evaluation.
#
# Usage:
#   scripts/new-repo-eval.sh <owner/repo> [repo_type] [--archetype <name>]
#
# Examples:
#   scripts/new-repo-eval.sh zinan92/content-downloader
#   scripts/new-repo-eval.sh zinan92/content-downloader skill
#   scripts/new-repo-eval.sh zinan92/content-downloader skill --archetype adapter
#   scripts/new-repo-eval.sh nicobailon/visual-explainer --archetype hybrid-skill
#
# Without --archetype, generic templates from templates/repo/ are used
# (backward compatible). With --archetype, the starter claim-map and
# eval-plan come from archetypes/<name>/ and `archetype: <name>` is
# stamped into repo.yaml.

set -euo pipefail

ARCHETYPE=""
POSITIONAL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archetype)
      ARCHETYPE="${2:-}"
      shift 2
      ;;
    --archetype=*)
      ARCHETYPE="${1#--archetype=}"
      shift
      ;;
    -h|--help)
      sed -n '1,25p' "$0"
      exit 0
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [[ ${#POSITIONAL[@]} -lt 1 ]]; then
  echo "Usage: scripts/new-repo-eval.sh <owner/repo> [repo_type] [--archetype <name>]" >&2
  exit 1
fi

TARGET="${POSITIONAL[0]}"
REPO_TYPE="${POSITIONAL[1]:-skill}"

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

# Validate archetype if given
if [[ -n "$ARCHETYPE" ]]; then
  ARCH_DIR="${BASE_DIR}/archetypes/${ARCHETYPE}"
  if [[ ! -d "$ARCH_DIR" ]]; then
    echo "Unknown archetype: $ARCHETYPE" >&2
    echo "Available archetypes:" >&2
    ls "${BASE_DIR}/archetypes" 2>/dev/null | grep -v '^README' || true
    exit 1
  fi
  for required in archetype.yaml claim-map.yaml eval-plan.md; do
    if [[ ! -f "${ARCH_DIR}/${required}" ]]; then
      echo "Archetype ${ARCHETYPE} is missing ${required}" >&2
      exit 1
    fi
  done
fi

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
  if [[ -n "$ARCHETYPE" ]]; then
    perl -0pi -e "s/archetype: unknown/archetype: ${ARCHETYPE}/g" "${REPO_DIR}/repo.yaml"
  fi
fi

# Claim map: archetype-specific if given, else generic.
if [[ ! -f "${REPO_DIR}/claims/claim-map.yaml" ]]; then
  if [[ -n "$ARCHETYPE" ]]; then
    cp "${BASE_DIR}/archetypes/${ARCHETYPE}/claim-map.yaml" "${REPO_DIR}/claims/claim-map.yaml"
  else
    cp "${BASE_DIR}/templates/repo/claim-map.yaml" "${REPO_DIR}/claims/claim-map.yaml"
  fi
fi

# Eval plan: archetype-specific if given, else generic.
PLAN_PATH="${REPO_DIR}/plans/${TODAY}-eval-plan.md"
if [[ ! -f "${PLAN_PATH}" ]]; then
  if [[ -n "$ARCHETYPE" ]]; then
    cp "${BASE_DIR}/archetypes/${ARCHETYPE}/eval-plan.md" "${PLAN_PATH}"
  else
    cp "${BASE_DIR}/templates/repo/eval-plan.md" "${PLAN_PATH}"
  fi
fi

VERDICT_PATH="${REPO_DIR}/verdicts/${TODAY}-final-verdict.md"
if [[ ! -f "${VERDICT_PATH}" ]]; then
  cp "${BASE_DIR}/templates/repo/final-verdict.md" "${VERDICT_PATH}"
fi

touch "${REPO_DIR}/fixtures/.gitkeep" "${REPO_DIR}/runs/.gitkeep" "${REPO_DIR}/areas/.gitkeep"

if [[ -n "$ARCHETYPE" ]]; then
  echo "Created eval scaffold at ${REPO_DIR} (archetype=${ARCHETYPE})"
else
  echo "Created eval scaffold at ${REPO_DIR}"
fi
