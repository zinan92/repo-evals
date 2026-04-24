#!/usr/bin/env bash
# new-eval-harness.sh — seed the evaluation harness for a scaffolded repo.
#
# Reads the repo's archetype from repo.yaml and copies the matching
# evals.json.template into repos/<slug>/evals/evals.json (if not already
# present). Then stubs one eval per critical claim found in claim-map.yaml.
#
# Usage:
#   scripts/new-eval-harness.sh <owner>--<repo>
#
# Idempotent: will not overwrite an existing evals.json.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/new-eval-harness.sh <owner>--<repo>" >&2
  exit 1
fi

SLUG="$1"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_DIR="${BASE_DIR}/repos/${SLUG}"

if [[ ! -d "$REPO_DIR" ]]; then
  echo "Repo scaffold not found: $REPO_DIR" >&2
  echo "Run scripts/new-repo-eval.sh <owner>/<repo> --archetype <name> first." >&2
  exit 1
fi

REPO_YAML="${REPO_DIR}/repo.yaml"
if [[ ! -f "$REPO_YAML" ]]; then
  echo "Missing $REPO_YAML" >&2
  exit 1
fi

ARCHETYPE="$(grep -E '^archetype:' "$REPO_YAML" | head -1 | awk '{print $2}' | tr -d '"')"
if [[ -z "$ARCHETYPE" || "$ARCHETYPE" == "unknown" ]]; then
  ARCHETYPE="adapter"
  echo "(warn) repo.yaml archetype missing or 'unknown' — defaulting to 'adapter' harness template" >&2
fi

TEMPLATE="${BASE_DIR}/archetypes/${ARCHETYPE}/evals.json.template"
if [[ ! -f "$TEMPLATE" ]]; then
  # Fall back to adapter template if the chosen archetype hasn't shipped one yet.
  FALLBACK="${BASE_DIR}/archetypes/adapter/evals.json.template"
  if [[ -f "$FALLBACK" ]]; then
    echo "(info) no evals.json.template under archetype '$ARCHETYPE' — using adapter fallback" >&2
    TEMPLATE="$FALLBACK"
  else
    echo "No evals.json.template available — cannot seed harness" >&2
    exit 1
  fi
fi

mkdir -p "${REPO_DIR}/evals"
TARGET="${REPO_DIR}/evals/evals.json"

if [[ -f "$TARGET" ]]; then
  echo "Already present: $TARGET (leaving untouched)"
  exit 0
fi

cp "$TEMPLATE" "$TARGET"

# Replace placeholders with the real slug so the file is self-describing.
python3 - "$TARGET" "$SLUG" "$ARCHETYPE" <<'PY'
import json, sys
path, slug, archetype = sys.argv[1:4]
with open(path) as f:
    data = json.load(f)
data["repo_slug"] = slug
data["archetype"] = archetype
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

echo "Seeded $TARGET"
echo
echo "Next steps:"
echo "  1. Open $TARGET and fill in one eval per critical claim."
echo "  2. Run: scripts/run_evals.py $SLUG"
echo "  3. (optional) scripts/run_evals.py $SLUG --baseline  # with/without comparison"
