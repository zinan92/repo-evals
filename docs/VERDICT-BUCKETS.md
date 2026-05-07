# Verdicts: Score, Categories, Buckets

> **Heads up — this doc has both the current model and the legacy model.**
> The 4-bucket model below is still implemented for backward compatibility
> (a few old evals reference it), but **the current source of truth is the
> 0-100 score + 4-category dossier**. New evals should think in score, not
> bucket.

## Current model — 0-100 score + 4 categories

Every dossier shows an explicit numeric score (0–100). Pass-threshold is 60. Underneath the score sit two display layers:

### 4 display categories (filter pills, dashboard headers)

| Score | Category | Emoji | EN / ZH |
|---|---|---|---|
| 80–100 | `production` | 🏭 | Production-ready / 可用于生产 |
| 50–79  | `available`  | 🛠 | Available / 可使用 |
| 30–49  | `risky`      | ⚠️ | Risky / 有风险 |
| 0–29   | `dont_use`   | 🛑 | Don't use / 不可使用 |

### 6 underlying tiers (fine-grained sort)

| Score | Tier key | Emoji | EN / ZH | Meaning |
|---|---|---|---|---|
| ≥90 | `recommend` | ⭐ | Recommend / 公开推荐 | Recommend to strangers, blog posts, PR integrations |
| ≥80 | `team`      | 🏭 | Team-ready / 团队就绪 | Safe to depend on in team / production pipelines |
| ≥65 | `self`      | 🛠 | Self-use OK / 自用 OK | Use it yourself; not yet ready to recommend |
| ≥50 | `try`       | 🧪 | Try once / 试一下 | Install + try; do not put in critical path |
| ≥30 | `risky`     | ⚠️ | Risky / 慎用 | Runs but has unverified critical issues |
| <30 | `broken`    | 🛑 | Don't use / 别用 | Won't install / core feature broken / archived |

### Score model (additive)

```
SCORE_BASE        = 40   (project is real, not archived, has license)
+ static claims   ±30    (claim pass/fail, weighted by priority)
+ maintainer      ±15    (release_pipeline + eval_discipline + recently_active)
+ ecosystem       ±15    (stars band + multilingual_readme)
+ layer_bonus     ±?     (atom can reach full marks; molecule + compound capped
                          until live e2e logged)
- license_penalty       (no LICENSE — penalty scales with stars)
```

Implementation: `scripts/verdict_calculator.py::compute_score`. Every component is auditable in the breakdown — readers can challenge any number.

### Why a score replaced 4 buckets

The 4-bucket model was too coarse. Once a repo crossed `usable`, everything looked OK; readers couldn't tell `usable + barely` from `reusable - barely`. The score gives every dossier a clear pass-line (60) and explicit drivers ("+15 from claim coverage, -8 from missing LICENSE, …").

## Legacy 4-bucket model (still in code, used by old evals)

The bucket names below are still emitted by `verdict_calculator.py` for compatibility. New evals derive these from the score, but old `verdicts/<date>-final-verdict.md` files reference them.

| Emoji | Bucket | One-line meaning |
|---|---|---|
| 🔴 | `unusable` | Core claims fail or only pass by accident — do not use |
| ⚪ | `usable` | Works once, low confidence — experimental only |
| 🟡 | `reusable` | Stable across multiple real scenarios — internal reuse OK |
| 🟢 | `recommendable` | Boundaries clear, stable — share with others |

### Bucket → category mapping

When you read a legacy bucket, here's roughly what it means in the current model:

| Bucket | Score range | Category |
|---|---|---|
| `unusable` | 0–29 | `dont_use` 🛑 |
| `usable` | 30–49 (sometimes ~50) | `risky` ⚠️ ↔ low end of `available` 🛠 |
| `reusable` | 50–79 | `available` 🛠 |
| `recommendable` | 80–100 | `production` 🏭 |

These are heuristics, not hard rules — bucket-era evals didn't track the underlying signals (stars, LICENSE, layer) the same way, so the conversion is approximate.

## Ceiling Rules (apply to both score and bucket)

- **Weak plan + all-pass** does not justify a strong verdict on its own
- **Untested core user-facing layer** caps the score (and bucket). For atom layer, static eval suffices. For molecule + compound, a logged live run is required to lift the cap.
- **`evidence_completeness: partial`** caps the score lower than `portable`
- Strong support-layer evidence can still appear in the narrative, even when the final score stays conservative

Encoded in `scripts/verdict_calculator.py`, covered by `tests/test_verdict_calculator.py`. See [VERDICT-CALCULATOR.md](VERDICT-CALCULATOR.md) for the full rule table, override path, and usage examples.
