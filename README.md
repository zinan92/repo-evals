<div align="center">

# repo-evals

**Claim-first 仓库评测框架 — 把"这个 skill / repo 到底能不能用"变成一份可审计、可对比的双语 dossier。**

[![Python](https://img.shields.io/badge/python-3.11+-3776ab.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-claim--first-blue.svg)](docs/FRAMEWORK.md)
[![Score](https://img.shields.io/badge/score-0--100-orange.svg)](docs/VERDICT-CALCULATOR.md)
[![Categories](https://img.shields.io/badge/categories-4_bands-purple.svg)](docs/VERDICT-CALCULATOR.md)
[![Layers](https://img.shields.io/badge/layers-atom_·_molecule_·_compound-2d7866.svg)](docs/LAYERS.md)
[![Tests](https://img.shields.io/badge/tests-142_passing-4ade80.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

```
in   target repo (owner/repo) + handwritten claim-map.yaml
out  bilingual dossier with:
       - 0-100 auditable score (6-component breakdown)
       - 4-category band: 🏭 Production · 🛠 Available · ⚠️ Risky · 🛑 Don't use
       - layer (atom · molecule · compound) + workflow SVG diagram
       - benefits cards: persona · scenario · without · with · cost · examples
       - similar-repos comparison drawn from this corpus (no web search)
     plus a master dashboard indexing the entire corpus

fail  no claim-map.yaml          → render falls back to legacy fields
fail  similar slug not in corpus → comparison block stays empty (honest)
fail  static-only eval           → score capped <90 (Production-ready
                                   reserved for repos with logged
                                   live e2e evidence)
```

The framework is its own first user: **30+ repos already evaluated** under
this model. The score for any repo is auditable point-by-point — the
six named components (`base / static_eval / maintainer_evidence /
ecosystem / layer_bonus / penalties`) appear in every dossier, so a
reader who disagrees with a number can challenge that exact number.

## 示例输出

A rendered dossier flows top-to-bottom in priority order:

```
┌──────────────────────────────────────────────────────────────┐
│ obra/superpowers                                             │
│ A 14-skill methodology bundle that auto-triggers when your   │
│ coding agent starts work — brainstorming, planning, TDD ...  │
├──────────────────────────────────────────────────────────────┤
│ #2  WHAT KIND OF SKILL IS THIS?                              │
│ ┌─ atom ─┐ → ┌─ molecule ─┐ → [ COMPOUND ← you are here ]    │
├──────────────────────────────────────────────────────────────┤
│ #3  HOW USABLE IS IT?                                        │
│ 🛑 Don't │ ⚠️ Risky │ [🛠 AVAILABLE] │ 🏭 Production         │
│  0-29   │  30-49  │     50-79     │      80+                │
│                              ▼ 77                            │
│                         (this repo)                          │
├──────────────────────────────────────────────────────────────┤
│ #4  WHAT THIS SKILL ACTUALLY BUYS YOU                        │
│ 👤 Who         🎯 When        😩 Without        ✨ With      │
│                                                              │
│ ↳ Three concrete moments where you would invoke it           │
│   You are: an indie dev about to add OAuth to a SaaS         │
│   You say: "Add GitHub OAuth login to my-saas..."           │
│   What happens: brainstorming auto-fires, asks about ...     │
├──────────────────────────────────────────────────────────────┤
│ #5  HOW IT ACTUALLY WORKS                                    │
│ Tree workflow — diamond decision nodes highlight LLM-runtime │
│ branches that make this compound (not molecule):             │
│                                                              │
│         user request                                         │
│              ↓                                               │
│         ◇ spec clear?  ─── no ──→ brainstorming              │
│              │ yes                       │                   │
│              ↓                           ↓                   │
│         writing-plans ←──────────────────┘                   │
│              ↓                                               │
│         test-driven-development                              │
│              ↓                                               │
│         ◇ big enough to split?  ─── yes ──→ subagent-driven  │
│              │ no                              │             │
│              ↓                                 ↓             │
│         verification-before-completion ←───────┘             │
│              ↓                                               │
│         finishing-a-development-branch                       │
│              ↓                                               │
│         receiving-code-review                                │
├──────────────────────────────────────────────────────────────┤
│ #6  HOW DOES IT COMPARE TO ONES WE ALREADY EVALUATED?        │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ ↳ Closer peers we have not evaluated yet                 │ │
│ │ Pending evaluation: G-Stack ...                          │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

Live samples to read:

- [`repos/obra--superpowers/verdicts/2026-05-05-verdict.html`](repos/obra--superpowers/) — compound (tree workflow)
- [`repos/NanmiCoder--MediaCrawler/verdicts/`](repos/NanmiCoder--MediaCrawler/) — molecule (linear pipeline)
- [`repos/zarazhangrui--frontend-slides/verdicts/`](repos/zarazhangrui--frontend-slides/) — atom (input → output)
- [`repos/zinan92--repo-evals/verdicts/`](repos/zinan92--repo-evals/) — the framework's self-eval
- [`dashboard/all-evals.html`](dashboard/all-evals.html) — sortable master index

## Score model — 6 auditable components

| Component | Range | What it measures |
|---|---|---|
| **base** | +40 | "the project is real, not archived, has a license" |
| **static_eval** | ±30 | claim-by-claim outcomes (passed / failed / untested) |
| **maintainer_evidence** | +0 to +15 | release pipeline, eval discipline, recent activity |
| **ecosystem** | +0 to +12 | GitHub stars (capped — peer validation, not popularity) |
| **layer_bonus** | −3 to +5 | atom +5, molecule +0, compound −3 (static eval can't validate runtime branches) |
| **penalties** | varies | LICENSE missing, privacy concerns, archived repo |

Sum is clamped to 0–100 and dropped into one of 4 categories:

| Category | Range | Meaning |
|---|---|---|
| 🏭 **Production-ready** | 80+ | Safe to depend on in team / production pipelines |
| 🛠 **Available** | 50–79 | Use it; not yet for production-critical paths |
| ⚠️ **Risky** | 30–49 | Runs but has unverified critical issues |
| 🛑 **Don't use** | <30 | Won't install / core feature broken / archived |

## Layer model — atom · molecule · compound

| Layer | What it means | Visualisation |
|---|---|---|
| **atom** | Single user-facing capability with deterministic internal phases | input → atom → output |
| **molecule** | Fixed pipeline of atoms (LLM doesn't decide next step at runtime) | left-to-right pipeline diagram |
| **compound** | LLM decides at runtime which atom/molecule fires next | top-down tree with diamond LLM-decision nodes |

The dossier explicitly explains *why* a given repo is at its layer
(e.g., why a methodology bundle is compound and not molecule). See
[`docs/LAYERS.md`](docs/LAYERS.md) for the long form.

## Quick start

```bash
git clone https://github.com/zinan92/repo-evals.git
cd repo-evals
python3 -m pip install pyyaml

# 1. Scaffold a new evaluation
scripts/new-repo-eval.sh owner/some-skill skill

# 2. Hand-author the claim map
# $EDITOR repos/owner--some-skill/claims/claim-map.yaml
# (write 6-10 claims; mark statuses as you verify each)

# 3. Fill repo.yaml product_view (persona / scenario / without / with /
#    cost_summary / examples) + workflow_diagram + similar_repos
# $EDITOR repos/owner--some-skill/repo.yaml

# 4. Render the bilingual dossier
python3 scripts/render_verdict_html.py owner--some-skill

# 5. Rebuild the master dashboard
python3 scripts/build_master_dashboard.py
```

## 标准流程 (架构)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 1. scaffold  │───▶│ 2. claim-map │───▶│ 3. static    │───▶│ 4. verdict   │───▶│ 5. render +  │
│ (new-repo)   │    │  (6-10 claims │    │    checks    │    │  calculator  │    │   dashboard  │
│              │    │   per repo)   │    │              │    │  (0-100 +    │    │              │
│              │    │              │    │              │    │   category)  │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

The pipeline is fully deterministic from step 3 onward — the labour
cost lives in step 2 (authoring a thoughtful claim-map, ~30-60 min
per repo). Step 1 + 5 are tooling, step 3 is the human verifying
each claim against the actual repo.

## What the new dossier surfaces

Every dossier (since 2026-05-05) renders these blocks in priority order:

1. **Hero** — repo name + slug + one-line tagline
2. **🔬 Layer strip** — 3-card spectrum (atom · molecule · compound), current highlighted
3. **📊 Category strip** — 4-zone score bar with a tick at the actual score
4. **✨ Benefits** — 4 cards (persona / scenario / without / with) + 3 concrete usage examples each (context + actual quote + what happens)
5. **🛠 Workflow diagram** — self-contained SVG, 3 layouts (io / linear / tree) matching the layer
6. **🔍 Similar repos** — comparison cards drawn from this corpus only; live scores via `verdict_calculator`. No web search.
7. Deployment + cost surface, watch-outs, claim ledger, score breakdown (collapsible)

## Tools

| Script | What it does |
|---|---|
| `scripts/new-repo-eval.sh <owner/repo>` | Scaffold a new evaluation directory |
| `scripts/extract_claims.py <target>` | Draft a claim-map from README/SKILL.md (every claim marked `needs_review: true`) |
| `scripts/coverage_gap_detector.py <slug>` | Surface critical / warning / info gaps in claim coverage |
| `scripts/verdict_calculator.py <slug>` | Compute the 0-100 score with full breakdown |
| `scripts/render_verdict_html.py <slug>` | Render the bilingual HTML dossier |
| `scripts/build_master_dashboard.py` | Rebuild `dashboard/all-evals.html` master index |
| `scripts/reeval_diff.py <slug>` | Structured diff between two evals of the same repo |

## For AI agents

```yaml
name: repo-evals
capability:
  summary: Claim-first repository evaluation harness producing 0-100 scores + bilingual dossiers
  in: target repo (owner/repo) + handwritten claim-map.yaml + repo.yaml product_view
  out: bilingual HTML dossier + master dashboard entry
  fail:
    - "no claim-map → render falls back to legacy product_view fields"
    - "similar slug not in corpus → comparison stays empty (honest stub)"
    - "static-only eval → score capped below 90 (Production reserved for live e2e)"
cli_commands:
  - cmd: scripts/new-repo-eval.sh
    args: ["<owner/repo>", "[skill|tool|framework]"]
  - cmd: scripts/render_verdict_html.py
    args: ["<owner--repo>"]
  - cmd: scripts/build_master_dashboard.py
    args: []
artifacts:
  claim_map: repos/<slug>/claims/claim-map.yaml
  repo_yaml: repos/<slug>/repo.yaml
  verdict_md: repos/<slug>/verdicts/<date>-final-verdict.md
  dossier_html: repos/<slug>/verdicts/<date>-verdict.html
  dashboard: dashboard/all-evals.html
score_components: [base, static_eval, maintainer_evidence, ecosystem, layer_bonus, penalties]
categories: [production, available, risky, dont_use]
layers: [atom, molecule, compound]
```

```python
import subprocess

# Evaluate a new repo
subprocess.run(
    ["scripts/new-repo-eval.sh", "owner/some-skill", "skill"],
    cwd="/path/to/repo-evals", check=True,
)

# After a human authors claim-map + repo.yaml, render the dossier
subprocess.run(
    ["python3", "scripts/render_verdict_html.py", "owner--some-skill"],
    cwd="/path/to/repo-evals", check=True,
)

# Refresh the master dashboard
subprocess.run(
    ["python3", "scripts/build_master_dashboard.py"],
    cwd="/path/to/repo-evals", check=True,
)
```

## 相关项目

The framework was used to evaluate itself — see
[`repos/zinan92--repo-evals/verdicts/`](repos/zinan92--repo-evals/) for
the meta-eval, including the two real defects the framework caught on
itself (no LICENSE before this README, README was stale before this
README) plus the path to higher score.

A handful of representative evaluated peers:

| Repo | Layer | Category | Score | Where the dossier sits |
|---|---|---|---|---|
| obra/superpowers | compound | 🛠 Available | 77 | [link](repos/obra--superpowers/verdicts/) |
| NanmiCoder/MediaCrawler | molecule | 🛠 Available | 75 | [link](repos/NanmiCoder--MediaCrawler/verdicts/) |
| anthropics/skill-creator | atom | 🏭 Production | 81 | [link](repos/anthropics--skill-creator/verdicts/) |
| zarazhangrui/frontend-slides | atom | 🛠 Available | 62 | [link](repos/zarazhangrui--frontend-slides/verdicts/) |
| zinan92/content-downloader | molecule | 🛑 Don't use | 29 | [link](repos/zinan92--content-downloader/verdicts/) |

Full sortable / filterable list: [`dashboard/all-evals.html`](dashboard/all-evals.html).

## 文档

- [FRAMEWORK.md](docs/FRAMEWORK.md) — Full framework definition
- [VERDICT-CALCULATOR.md](docs/VERDICT-CALCULATOR.md) — Score model + tier/category mapping
- [LAYERS.md](docs/LAYERS.md) — atom · molecule · compound classification rules
- [ARCHETYPES.md](docs/ARCHETYPES.md) — 7 repo archetypes (pure-cli, prompt-skill, hybrid-skill, adapter, orchestrator, api-service, mcp-enhancement)
- [DASHBOARD.md](docs/DASHBOARD.md) — Master dashboard generation
- [REEVAL-DIFF.md](docs/REEVAL-DIFF.md) — Structured diffs between two evals
- [PROVENANCE.md](docs/PROVENANCE.md) — Evidence capture + provenance discipline
- [CLAIM-EXTRACTION.md](docs/CLAIM-EXTRACTION.md) — Conservative claim-map drafting

## License

MIT — see [LICENSE](LICENSE).
