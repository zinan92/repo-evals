# Evidence Copier

`scripts/copy-evidence.sh` brings outside evidence into a run folder so the
entire eval can be reviewed from GitHub, without any dependency on `/tmp`,
a specific machine, or a still-running server.

## Usage

```bash
scripts/copy-evidence.sh <run-dir> <source> \
    [--into artifacts|logs|screenshots] \
    [--as <name>] \
    [--max-bytes N] \
    [--note "..."]
```

Examples:

```bash
RUN=repos/owner--repo/runs/2026-04-07/run-smoke

# Copy a single JSON artifact
scripts/copy-evidence.sh $RUN /tmp/result.json --note "end-to-end happy path"

# Snapshot a small output directory (everything under it)
scripts/copy-evidence.sh $RUN /tmp/outputs --as outputs-snap

# Copy a server log into logs/ (auto-toggles evidence.logs_copied → true)
scripts/copy-evidence.sh $RUN /tmp/server.log --into logs

# Stub a large artifact (>10MB) — metadata only, not the bytes
scripts/copy-evidence.sh $RUN /tmp/huge.bin --max-bytes 1048576
```

## What gets recorded

Every call appends an entry to `<run-dir>/artifacts/manifest.yaml`:

```yaml
manifest_version: 1
run_dir: run-smoke
entries:
  - source: "/tmp/result.json"
    dest: "artifacts/result.json"
    kind: "file"
    stored: "full"
    copied_at: "2026-04-07T05:32:24Z"
    sha256: "6a47c31b..."
    size_bytes: 18
  - source: "/tmp/huge.bin"
    dest: "artifacts/huge.bin"
    kind: "stub"
    stored: "metadata-only"
    reason: "size 20480000 > max_bytes 1048576"
    sha256: "99bc76fe..."
    size_bytes: 20480000
```

- `kind`: `file`, `directory`, or `stub`
- `stored`: `full` (bytes are in the repo) or `metadata-only` (stub entry)
- `sha256` is computed from the **source** (so stubs still let you verify
  whether a later re-eval saw the same file)
- `fingerprint` (directories only): sha256 over a sorted list of
  `(relpath, size)` pairs — content-independent, useful for diffs

## Rules of thumb

- Copy **representative** files, not everything. Manifests are for audit,
  not for carrying the whole `/tmp` tree into git.
- Copy failing cases first: they are the ones a reviewer will ask about.
- Stub anything over 10MB by default, or adjust `--max-bytes` per call.
- If you skip a file intentionally, add a manual entry to `manifest.yaml`
  explaining why (`stored: "omitted"`).

## When GitHub is the review surface

The invariant the manifest protects is:

> Given only the GitHub view of this run, a reviewer can tell exactly what
> was observed, how big it was, and whether it was truly copied or only
> referenced.

If a future reviewer cannot answer those three questions, the evidence
copier was not called where it should have been.
