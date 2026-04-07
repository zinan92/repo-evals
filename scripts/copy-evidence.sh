#!/usr/bin/env bash
#
# copy-evidence.sh — copy evidence into a run folder and record a manifest.
#
# Usage:
#   scripts/copy-evidence.sh <run-dir> <source> [--into artifacts|logs|screenshots] [--as <name>] [--max-bytes N] [--note "..."]
#
# Behavior:
#   - If <source> is a file:
#       - if size <= max-bytes: copy into <run-dir>/<into>/<name>, record sha256 + size
#       - else: write a stub entry only (metadata + sha256 computed from original)
#   - If <source> is a directory:
#       - if total size <= max-bytes: snapshot (cp -R) and record aggregate size + file count
#       - else: write a stub entry with total size and file count
#   - Appends an entry to <run-dir>/artifacts/manifest.yaml
#   - Also toggles `evidence.logs_copied: true` in run-summary.yaml when --into=logs
#
# Exit codes:
#   0 success, 1 usage/source-missing, 2 destination conflict (non-fatal: skipped).

set -euo pipefail

MAX_BYTES=$((10 * 1024 * 1024))   # 10 MB default
INTO="artifacts"
AS=""
NOTE=""

if [[ $# -lt 2 ]]; then
  echo "Usage: scripts/copy-evidence.sh <run-dir> <source> [--into artifacts|logs|screenshots] [--as <name>] [--max-bytes N] [--note \"...\"]" >&2
  exit 1
fi

RUN_DIR="$1"; shift
SOURCE="$1"; shift

while [[ $# -gt 0 ]]; do
  case "$1" in
    --into)       INTO="$2";       shift 2 ;;
    --as)         AS="$2";         shift 2 ;;
    --max-bytes)  MAX_BYTES="$2";  shift 2 ;;
    --note)       NOTE="$2";       shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -e "$SOURCE" ]]; then
  echo "Source not found: $SOURCE" >&2
  exit 1
fi

case "$INTO" in
  artifacts|logs|screenshots) ;;
  *) echo "--into must be one of: artifacts, logs, screenshots" >&2; exit 1 ;;
esac

mkdir -p "${RUN_DIR}/${INTO}" "${RUN_DIR}/artifacts"
MANIFEST="${RUN_DIR}/artifacts/manifest.yaml"

# Resolve dest name
if [[ -z "$AS" ]]; then
  AS="$(basename "$SOURCE")"
fi
DEST_REL="${INTO}/${AS}"
DEST_ABS="${RUN_DIR}/${DEST_REL}"

python3 - "$SOURCE" "$DEST_ABS" "$DEST_REL" "$MANIFEST" "$MAX_BYTES" "$NOTE" "$RUN_DIR" "$INTO" <<'PY'
import hashlib, os, pathlib, shutil, sys, datetime

source, dest_abs, dest_rel, manifest_path, max_bytes, note, run_dir, into = sys.argv[1:]
max_bytes = int(max_bytes)
src = pathlib.Path(source)
dest = pathlib.Path(dest_abs)
manifest = pathlib.Path(manifest_path)

def sha256_file(path, chunk=1 << 16):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(chunk), b''):
            h.update(blk)
    return h.hexdigest()

def dir_stats(root):
    total = 0
    count = 0
    # Hash of sorted (relpath, size) — cheap content-independent fingerprint
    h = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            p = pathlib.Path(dirpath) / name
            try:
                sz = p.stat().st_size
            except OSError:
                continue
            total += sz
            count += 1
            rel = p.relative_to(root).as_posix()
            h.update(f"{rel}\0{sz}\0".encode())
    return total, count, h.hexdigest()

entry = {
    "source": str(src),
    "dest": dest_rel,
    "copied_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
if note:
    entry["note"] = note

if src.is_file():
    size = src.stat().st_size
    entry["kind"] = "file"
    entry["size_bytes"] = size
    entry["sha256"] = sha256_file(src)
    if size <= max_bytes:
        if dest.exists():
            print(f"skip (exists): {dest_rel}", file=sys.stderr)
            sys.exit(2)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        entry["stored"] = "full"
    else:
        entry["kind"] = "stub"
        entry["stored"] = "metadata-only"
        entry["reason"] = f"size {size} > max_bytes {max_bytes}"
elif src.is_dir():
    total, count, fp = dir_stats(src)
    entry["kind"] = "directory"
    entry["size_bytes"] = total
    entry["file_count"] = count
    entry["fingerprint"] = fp
    if total <= max_bytes:
        if dest.exists():
            print(f"skip (exists): {dest_rel}", file=sys.stderr)
            sys.exit(2)
        shutil.copytree(src, dest)
        entry["stored"] = "full"
    else:
        entry["kind"] = "stub"
        entry["stored"] = "metadata-only"
        entry["reason"] = f"size {total} > max_bytes {max_bytes}"
else:
    print(f"unsupported source type: {src}", file=sys.stderr)
    sys.exit(1)

# Write / update manifest.yaml
# Minimal YAML: we control the whole file.
if manifest.exists():
    text = manifest.read_text()
else:
    text = (
        "manifest_version: 1\n"
        f"run_dir: {pathlib.Path(run_dir).name}\n"
        "entries:\n"
    )

def yaml_quote(s):
    s = str(s)
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

lines = ["  - source: " + yaml_quote(entry["source"])]
for k in ("dest", "kind", "stored", "reason", "note", "copied_at", "sha256", "fingerprint"):
    if k in entry:
        lines.append(f"    {k}: " + yaml_quote(entry[k]))
for k in ("size_bytes", "file_count"):
    if k in entry:
        lines.append(f"    {k}: {entry[k]}")
text = text.rstrip() + "\n" + "\n".join(lines) + "\n"
manifest.write_text(text)

# If we dropped something into logs/, toggle evidence.logs_copied in run-summary.yaml
if into == "logs":
    summary = pathlib.Path(run_dir) / "run-summary.yaml"
    if summary.exists():
        s = summary.read_text()
        import re
        s2, n = re.subn(r'(^\s*logs_copied:\s*)false\s*$',
                        lambda m: m.group(1) + "true", s, count=1, flags=re.MULTILINE)
        if n:
            summary.write_text(s2)

print(f"Recorded: {entry['kind']} → {dest_rel} ({entry.get('stored','?')})")
PY
