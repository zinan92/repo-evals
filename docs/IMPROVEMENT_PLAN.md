# repo-evals · Improvement Plan v1

> **Status:** draft, 2026-05-04
> **Source:** the 10-repo page-1 starred-repo batch eval, plus the
> meta-reflection in `dashboard/stars-page1-summary.html`

## TL;DR

The 10/10 `usable` outcome on page-1 is **a calibration symptom, not
a result.** Every cap is the molecule/compound rule firing (no live
runs logged). The framework caught more than expected on static
evidence (8 cross-repo findings) but is structurally biased toward
"can't promote without a live run". This doc proposes **5 new
dimensions, 3 calibration changes, and 2 workflow/tooling fixes**,
ranked.

---

## 1. Why 10/10 `usable` is a real problem

### Bucket distribution should not be uniform across heterogeneous repos

The page-1 batch covers everything from:
- **`tab-out`** — 4-file Chrome extension (~80 KB, single-purpose)
- **`CLIProxyAPI`** — 30K-star Go API gateway with 8-platform release pipeline + 9-package SDK + 7 OAuth flows
- **`OpenMAIC`** — Tsinghua-affiliated multi-agent classroom platform with in-repo eval harness
- **`remotion-dev/skills`** — official maintainer's curated 110 KB skill content

…and they all land at `usable`. That can't be right at the
information-theoretic level: bucket should encode **how confident
we are in this repo**, and the framework currently has no way to
distinguish a pristine 30K-star Go service from a 1K-star hobby
extension when both pass static checks.

### The cause: "core layer untested" is too coarse

Today the framework has one reason to cap at `usable`:
`core_layer_tested=false`. We read this as "no live run", but several
repos provide **stronger static evidence than a single one-shot live
run would**:

- **CLIProxyAPI** ships consistent multi-platform binaries + checksums
  via goreleaser. That implies dozens of CI runs across the build
  matrix, more reliable than a single `curl http://localhost/v1/chat/completions` test on the evaluator's machine.
- **OpenMAIC** ships its own `eval/` harness with two named runners.
  The maintainers run those continuously; we'd be lower-fidelity by
  duplicating their work.
- **remotion-dev/skills** is part of the broader Remotion 4.x
  release pipeline (private package); the maintainers self-test
  three of the rules as live React. That's stronger than a one-off
  user trial.

The framework treats those signals as zero. It should not.

---

## 2. Five new dimensions to add

### 2.1 `release-pipeline-score` (priority: high)

Multi-platform release artefacts + checksums + CI badges are a
strong, cheap-to-detect maturity signal. Specifically:

| Score | Signal |
|---|---|
| 0 | No releases, or only source tarball |
| 1 | Single-platform release, no checksums |
| 2 | Multi-platform release (≥2 OS / arch combos), checksums file present |
| 3 | Multi-platform + checksums + signed (cosign / GPG) + reproducible-build evidence |

Implementation: add `release_pipeline_score` to `repo.yaml`,
auto-detect via `gh api releases` + asset name pattern matching.
Bonus to the bucket-derivation logic: `release_pipeline_score >= 2`
contributes evidence equivalent to one live run.

### 2.2 `eval-discipline-score` (priority: high)

Some repos ship their own evals. That's high-signal — the
maintainers have already done the live-run work. Specifically:

| Score | Signal |
|---|---|
| 0 | No tests |
| 1 | Unit tests only |
| 2 | Integration / e2e tests + CI |
| 3 | LLM-output-quality eval harness (e.g., OpenMAIC's `eval/`) |

A `score >= 2` should also count as live-run-equivalent evidence —
but only for the surface the eval covers. The framework should
record **what the eval covers** and **what it leaves uncovered**.

### 2.3 `extension-permission-audit` (priority: high)

For any repo containing `manifest.json` with `manifest_version: 3`,
auto-run a permission audit:

- **Red-flag perms** (`debugger`, `<all_urls>`, `webRequestBlocking`,
  `unlimitedStorage`): require explicit README disclosure or downgrade
  the bucket.
- **Privilege scope** (`host_permissions`): score by narrowness.
- **External requests in script body**: grep for `fetch(` /
  `XMLHttpRequest` / `<img src="https?://`. If found and the README
  says "no external API calls", flag.

This caught the tab-out → Google favicon leak. Should be automatic.

### 2.4 `catalog-sample-quality` (priority: medium)

For catalog repos (`prompt-skill` or `hybrid-skill` archetypes with
≥10 sub-skills), structural checks (count, frontmatter, install path)
are necessary but not sufficient. Add a **sample-N-skills** dimension
that picks 3 random skills and audits each:

- Does SKILL.md ≥ 30 lines and contain a "When to use" trigger?
- If hybrid: do the referenced scripts/ exist and pass syntax check?
- If listed in a manifest: does `installation.supports` array match
  README's headline platform list?

Prevents the "we have 204 skills" claim from masking 50 stub skills.

### 2.5 `docs-currency-score` (priority: medium)

The "code is richer than docs" pattern showed up in 4 of 10 repos:

- `goose-skills` 108 → 204
- `MediaCrawler` extra crawler types + storage backends
- `CLIProxyAPI` Kimi + Vertex OAuth
- `finance-skills` 8 → 10 dirs

Auto-flag when README's headline numbers (X skills, N providers, M
backends) under-count what the manifest / source layout reveals. This
isn't a defect — it's an under-promise — but it's a discoverability
gap users should know about.

---

## 3. Three calibration changes

### 3.1 Ladder the `core_layer_tested` flag (priority: high)

Replace the binary `core_layer_tested: true|false` with a **levels**
field that captures gradations of evidence:

| Level | Meaning |
|---|---|
| `none` | Static-only audit, no live evidence |
| `static-strong` | Static + multi-platform release + checksums + repo-internal eval / CI passing |
| `live-one` | One operator-logged live scenario |
| `live-multi` | ≥3 logged scenarios across operators |

Bucket-ladder mapping changes accordingly:

| Level | Bucket ceiling |
|---|---|
| `none` | `usable` (today's default) |
| `static-strong` | **`reusable`** (new) — strong static + repo's own eval gives us reasonable evidence |
| `live-one` | `reusable` |
| `live-multi` | `recommendable` |

This breaks the 10/10 `usable` log-jam without lowering the bar
dishonestly. CLIProxyAPI and OpenMAIC would justifiably move to
`static-strong → reusable`.

### 3.2 Differentiate molecule cap from compound cap (priority: medium)

Currently both molecule and compound layers cap at `usable` without
live evidence. But:

- A molecule's user-facing layer is the **deterministic pipeline**.
  Static evidence + the project's own integration tests can largely
  validate it.
- A compound's user-facing layer is **runtime LLM-driven decisions**.
  Static evidence cannot validate that no matter how thorough.

Suggest: molecule should accept `static-strong` evidence as
live-equivalent (per 3.1). Compound should still require ≥1 logged
scenario.

### 3.3 Don't read `repo.yaml::current_bucket` as authoritative (priority: low)

The bug we just fixed had a confusing element: `repo.yaml` has a
`current_bucket` field that the dossier ignored. Either:

- (a) Remove the field from the schema (single source of truth =
  claim-map + verdict-input)
- (b) Keep it as a *cache* and have the dossier display "stale" if
  `compute_verdict()` disagrees with `current_bucket`

Suggest (b) — useful for at-a-glance dashboards, but the dossier is
authoritative.

---

## 4. Two workflow / tooling fixes

### 4.1 Auto-derive `verdict-input.yaml` (priority: high — half done)

We just shipped this for the dossier renderer. But the
`verdict_calculator.py` CLI still expects a hand-written input. Two
fixes needed:

1. Make `verdict_calculator.py` accept `--from-claim-map` to derive
   input on the fly.
2. Add a one-shot `scripts/derive_verdict_inputs.sh` that walks
   `repos/*/` and writes `<date>-verdict-input.yaml` everywhere that
   doesn't have one.

Result: never again render `unknown` because we forgot a sidecar.

### 4.2 Add `repo-evals lint` for batch quality checks (priority: medium)

A new CLI that runs across all repos and reports:

- Repos missing `layer:` field
- Repos with `current_bucket` that disagrees with `compute_verdict()`
- Repos with passed claims but no run-summary.yaml evidence
- Repos where claim-map mentions sub-paths that don't exist
  (`source_ref: pyproject.toml` — does that file exist?)
- Repos with a `passed_with_concerns` status but no `note` field
  explaining the concern

Would have caught the 14-repo `unknown` rendering bug before users hit
it.

---

## 5. Prioritized roadmap

| Phase | Effort | What | Why |
|---|---|---|---|
| 1 | small | Auto-derive verdict-input in CLI (4.1) | Already half done; finish to prevent regressions |
| 2 | medium | Ladder `core_layer_tested` (3.1) | Breaks the 10/10 `usable` log-jam |
| 3 | small | `release-pipeline-score` dimension (2.1) | Cheap to detect, high signal |
| 4 | small | `eval-discipline-score` dimension (2.2) | Trivial detection (look for `eval/`); rewards good practice |
| 5 | medium | `extension-permission-audit` (2.3) | Catches real defects (tab-out favicon, xhs Bridge debugger) |
| 6 | medium | Differentiate molecule vs compound cap (3.2) | Honest about what static evidence can and cannot validate |
| 7 | medium | `repo-evals lint` (4.2) | Catches workflow bugs early |
| 8 | medium | `catalog-sample-quality` (2.4) | Prevents catalog-of-stubs |
| 9 | small | `docs-currency-score` (2.5) | Surfaces under-promise pattern |
| 10 | small | Resolve `current_bucket` semantics (3.3) | Cleans up the schema |

---

## 6. What this would do to the page-1 batch

Re-running the same 10 repos with the proposed framework v2:

| Repo | Current | After improvements | Why |
|---|---|---|---|
| tradecat | usable | usable → **reusable**? | Static-strong: comprehensive install path + dataset registry + TUI fallback all verified |
| goose-skills | usable | usable | Catalog-sample-quality (2.4) would force sampling; might surface uneven skill quality |
| tab-out | usable | usable | extension-permission-audit (2.3) would auto-flag favicon leak and possibly downgrade |
| QuantDinger | usable | usable | Compound layer keeps cap; but eval-discipline-score (2.2) would flag absence of LLM-output evals |
| remotion-skills | usable | **reusable** | Static-strong: official maintainer + studio harness self-tests rules |
| xiaohongshu-skills | usable | usable | extension-permission-audit (2.3) would *downgrade* — `debugger` not disclosed |
| ai-goofish-monitor | usable | usable | Foot-shotgun (admin/admin123 + 0.0.0.0) would explicitly downgrade per 2.3 hardening rule |
| finance-skills | usable | usable | docs-currency-score (2.5) would flag 8 → 10 catalog drift |
| OpenMAIC | usable | **reusable** | Static-strong: in-repo eval/ harness + multi-version release cadence + AGPL-3.0 + 16K stars |
| CLIProxyAPI | usable | **reusable** | Static-strong: 8-platform release pipeline + checksums + 9-package SDK + 7 OAuth flows |

That's a more meaningful distribution: 6 `usable` + 3 `reusable` + 1
maybe `reusable` (tradecat). The 3 `reusable` candidates would still
need ≥1 logged live run to escape that ceiling toward
`recommendable`.

---

## 7. Open questions for the framework owner (Wendy)

1. **Is `static-strong` evidence acceptable as live-run-equivalent?**
   The proposal trades evaluator certainty (we ran it ourselves) for
   maintainer certainty (they ran it on their CI / their eval).
   That's a tradeoff worth deciding explicitly.

2. **Should the framework have an opinion on commercial overlap?**
   QuantDinger / CLIProxyAPI / OpenMAIC all blur OSS / SaaS lines.
   We currently note this in `watch_out` but don't downgrade. Should
   we?

3. **Should anti-bot fragility downgrade browser-driven repos
   automatically?**
   MediaCrawler / xiaohongshu-skills / ai-goofish-monitor /
   tradecat-extension all depend on third-party DOM/signing. Today
   we treat that as `passed_with_concerns`. Should it be a hard
   ceiling?

4. **Catalog quality vs catalog count** — for goose-skills (204
   skills), how do we decide how many to sample? 3 is too few;
   sampling all 204 is impractical. Suggest 5 with stratified
   sampling across categories.
