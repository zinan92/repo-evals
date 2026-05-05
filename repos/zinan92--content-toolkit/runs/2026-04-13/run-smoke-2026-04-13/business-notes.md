# Business Notes — content-toolkit smoke test

## Scenario

First-time evaluation of content-toolkit as an orchestrator. Tested:
- CLI help and routing
- Smart input detection (URL, .mp4)
- Capability listing and health reporting
- Auto-install of uninstalled capability
- Three videocut subcommands (transcribe, autocut, subtitle)
- Error handling for unknown commands and missing arguments
- Existing test suite

## What Happened

**Orchestration layer: Excellent.**
The CLI help is comprehensive and Chinese-first. Smart input detection works
perfectly — bare URLs suggest `download`, bare `.mp4` suggests videocut commands.
Unknown commands get clear Chinese error messages. Alias routing (intelligence→analyze)
works. `content list` and `content health` provide useful status info.

**Auto-install: Works but with quality issues.**
Running `node cli.js intelligence` auto-cloned zinan92/content-intelligence, created
venv, ran pip install. But the capability ended up in "degraded" state because
`pip install -e .` failed due to pyproject.toml module path configuration. The install
machinery itself works; the downstream repo has a packaging bug.

**Videocut: 2/3 subcommands work.**
- `transcribe` → PASS: produced transcript.json, .txt, .srt, audio.mp3
- `autocut` → PASS: produced cut.mp4 (68KB) plus all intermediate files
- `subtitle` → FAIL: exit code 0, empty output directory, no error message. Classic silent failure.

**Test suite: Completely broken.**
All 80+ tests fail with `TypeError: <function> is not a function`. The CLI functions
(normalizeCapabilityName, buildCommandPlan, etc.) are not exported from cli.js.
Additionally, importing cli.js prints the full help screen as a side effect.

**Error propagation: Mixed.**
`content download` (no args) correctly passes through the downstream error from
content-downloader. But `videocut subtitle` silently fails — exit 0, no output,
no error message. Inconsistent.

## Was The Result Usable?

For a power user who already knows the toolkit: **yes, for the happy paths that work.**
Download, transcribe, autocut, and the pipeline preset all function. The help and
routing layer is genuinely well-designed.

For a new user exploring: **frustrating.** Several advertised capabilities silently
fail or produce nothing, and the test suite that should catch these is 100% broken.

## Anything Surprising?

1. **Silent failures are the biggest problem.** The orchestrator does a great job on
   routing and help, but when a downstream capability fails silently (subtitle, cover,
   clip), the user gets exit code 0 and an empty directory. This violates the
   "capability execution error → passthrough upstream error" claim.

2. **Test suite rot.** 80+ tests exist but none pass. This means the routing logic
   (which actually works well) has zero automated verification. Any regression
   would go undetected.

3. **intelligence capability auto-install degraded.** The install machinery works,
   but the downstream repo has a pyproject.toml bug, so the capability is immediately
   degraded. The health system correctly reports this, which is good observability.

4. **Existing TEST-REPORT.md is honest.** The repo already documents 7/20 pass rate
   with detailed bug/UX analysis (dated 2026-03-31). Our findings are consistent
   with that report — the known issues haven't been fixed since.
