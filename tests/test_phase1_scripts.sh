#!/usr/bin/env bash
#
# Regression tests for Phase 1 shell scripts.
# Covers the two trust bugs reported against commit 190a096:
#   1. new-run.sh marked captured=true with only EVAL_SESSION_REPLAY_NOTES set
#   2. copy-evidence.sh flipped logs_copied=true on a stub-only entry
#
# Run: bash tests/test_phase1_scripts.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
check() {
  local name="$1"; shift
  if "$@"; then
    echo "  PASS  $name"
    pass=$((pass+1))
  else
    echo "  FAIL  $name"
    fail=$((fail+1))
  fi
}

grep_field() {
  # grep_field <file> <key> <expected-exact-value>
  local file="$1" key="$2" expected="$3"
  local line
  line="$(grep -E "^\s*${key}:" "$file" | head -1 || true)"
  [[ "$line" == *": ${expected}"* ]]
}

# --- Setup: a throwaway eval scaffold so new-run.sh has somewhere to write ---
REPO_SLUG="test--phase1"
mkdir -p "$ROOT/repos/$REPO_SLUG"
: > "$ROOT/repos/$REPO_SLUG/repo.yaml"

cleanup_repo() {
  rm -rf "$ROOT/repos/$REPO_SLUG"
}
trap 'cleanup_repo; rm -rf "$TMP"' EXIT

# --- BUG #1: new-run.sh trust inflation -------------------------------------

# Case A: only an optional field → should NOT be captured, must be partial
unset EVAL_RUNNER EVAL_AGENT EVAL_MODEL \
      EVAL_TERMINAL_SESSION_ID EVAL_AGENT_SESSION_ID \
      EVAL_TRANSCRIPT_PATH EVAL_COMMAND_LOG_PATH
EVAL_SESSION_REPLAY_NOTES="only notes set" \
  "$ROOT/scripts/new-run.sh" "$REPO_SLUG" bug1-optional-only >/dev/null
A="$ROOT/repos/$REPO_SLUG/runs/$(date +%F)/run-bug1-optional-only/run-summary.yaml"

check "new-run: optional-only → captured=false" \
      grep_field "$A" "captured" "false"
check "new-run: optional-only → partial=true" \
      grep_field "$A" "partial" "true"
check "new-run: optional-only → provenance_source=auto" \
      grep_field "$A" "provenance_source" '"auto"'
check "new-run: optional-only → notes were still recorded" \
      grep -q 'session_replay_notes: "only notes set"' "$A"

# Case B: full trio → should be captured and not partial
unset EVAL_SESSION_REPLAY_NOTES
EVAL_RUNNER=cc EVAL_AGENT="Claude Code" EVAL_MODEL=claude-opus-4-6 \
  "$ROOT/scripts/new-run.sh" "$REPO_SLUG" bug1-full-trio >/dev/null
B="$ROOT/repos/$REPO_SLUG/runs/$(date +%F)/run-bug1-full-trio/run-summary.yaml"
check "new-run: full-trio → captured=true" \
      grep_field "$B" "captured" "true"
check "new-run: full-trio → partial=false" \
      grep_field "$B" "partial" "false"
check "new-run: full-trio → provenance_source=auto" \
      grep_field "$B" "provenance_source" '"auto"'

# Case C: partial trio (missing model) → captured=false, partial=true
unset EVAL_MODEL
EVAL_RUNNER=cc EVAL_AGENT="Claude Code" \
  "$ROOT/scripts/new-run.sh" "$REPO_SLUG" bug1-missing-model >/dev/null
C="$ROOT/repos/$REPO_SLUG/runs/$(date +%F)/run-bug1-missing-model/run-summary.yaml"
check "new-run: partial-trio → captured=false" \
      grep_field "$C" "captured" "false"
check "new-run: partial-trio → partial=true" \
      grep_field "$C" "partial" "true"

# Case D: zero env vars → manual + partial
unset EVAL_RUNNER EVAL_AGENT EVAL_MODEL
"$ROOT/scripts/new-run.sh" "$REPO_SLUG" bug1-nothing >/dev/null
D="$ROOT/repos/$REPO_SLUG/runs/$(date +%F)/run-bug1-nothing/run-summary.yaml"
check "new-run: zero → captured=false" \
      grep_field "$D" "captured" "false"
check "new-run: zero → partial=true" \
      grep_field "$D" "partial" "true"
check "new-run: zero → provenance_source=manual" \
      grep_field "$D" "provenance_source" '"manual"'

# --- BUG #2: copy-evidence.sh spurious logs_copied --------------------------

# Build a minimal run dir with a real run-summary.yaml
RUN="$TMP/run"
mkdir -p "$RUN/artifacts" "$RUN/logs"
cat > "$RUN/run-summary.yaml" <<'EOF'
evidence:
  stored_in_repo: true
  artifact_paths_are_relative: true
  logs_copied: false
  manifest_path: "artifacts/manifest.yaml"
EOF

# Case A: stub-only log (exceeds --max-bytes) → logs_copied must stay false
dd if=/dev/zero of="$TMP/big.log" bs=1024 count=16 2>/dev/null
"$ROOT/scripts/copy-evidence.sh" "$RUN" "$TMP/big.log" --into logs --max-bytes 1024 >/dev/null
check "copy-evidence: stub log → logs_copied stays false" \
      grep_field "$RUN/run-summary.yaml" "logs_copied" "false"
check "copy-evidence: stub log → stub entry in manifest" \
      grep -q 'kind: "stub"' "$RUN/artifacts/manifest.yaml"
check "copy-evidence: stub log → bytes NOT in logs/" \
      bash -c "! [ -f '$RUN/logs/big.log' ]"

# Case B: real log copy → logs_copied flips to true
echo "real log line" > "$TMP/small.log"
"$ROOT/scripts/copy-evidence.sh" "$RUN" "$TMP/small.log" --into logs >/dev/null
check "copy-evidence: full log → logs_copied=true" \
      grep_field "$RUN/run-summary.yaml" "logs_copied" "true"
check "copy-evidence: full log → bytes ARE in logs/" \
      test -f "$RUN/logs/small.log"

# --- Summary ----------------------------------------------------------------
echo
echo "----------------------------------------"
if [[ $fail -eq 0 ]]; then
  echo "OK: $pass passed, 0 failed"
  exit 0
else
  echo "FAILED: $pass passed, $fail failed"
  exit 1
fi
