# Claim Extraction Assistant

`scripts/extract_claims.py` produces a **draft** claim map from a
target repo's README / SKILL.md / docs. It is deliberately
conservative: it would rather under-claim than invent capabilities the
repo never promised.

Every extracted claim is marked `needs_review: true` and `status: untested`.
A human is expected to prune, merge, re-title, and rewrite before
committing the result as a real claim map.

## Usage

```bash
# Write a draft to a file
scripts/extract_claims.py /path/to/target-repo -o /tmp/draft-claim-map.yaml

# Stream to stdout for inspection
scripts/extract_claims.py /path/to/target-repo --stdout

# Limit to specific sources
scripts/extract_claims.py /path/to/target-repo --sources README.md,SKILL.md
```

Typical workflow:

```bash
# 1. Generate the draft
scripts/extract_claims.py /tmp/visual-explainer \
    -o repos/nicobailon--visual-explainer/claims/claim-map.yaml.draft

# 2. Review and prune by hand
$EDITOR repos/nicobailon--visual-explainer/claims/claim-map.yaml.draft

# 3. Rename to claim-map.yaml once you're happy
mv repos/nicobailon--visual-explainer/claims/claim-map.yaml{.draft,}

# 4. Check coverage
scripts/coverage_gap_detector.py repos/nicobailon--visual-explainer --md
```

## Sources used

By default, in order of trust:

1. `README.md` (and case variants, deduped by filesystem inode)
2. `SKILL.md`
3. `docs/*.md` (first 5 files, for breadth not depth)

Pass `--sources a.md,b.md` to override.

## Extraction rules

Every extracted claim carries an `extractor_rule` field naming which
rule fired, so you can audit and tune the extractor.

| Rule | Confidence | Source |
|---|---|---|
| `feature_bullet` | `high` | Bullet under a heading matching `features` / `capabilities` / `功能` / etc. |
| `command_table_row` | `high` | Row in a markdown table under a heading matching `commands` / `usage` / `命令` |
| `numeric_claim_regex` | `medium` | `supports N platforms` / `handles up to N X` / `N+ connectors` / `up to N items` |
| `badge_claim` | `medium` | Shields.io-style badge with a numeric value (excluding license badges) |
| `generic_section_bullet` | `low` | Bullet under any other non-excluded section |

Critical-priority promotion: if a high-trust feature bullet contains
a strong verb (`download`, `generate`, `extract`, `render`, etc., or
their Chinese equivalents), it is upgraded from `high` to `critical`
priority.

## Excluded sections

Bullets inside these sections are never turned into claims:

- `Installation` / `Install` / `安装`
- `License` / `Licensing`
- `Contributing` / `Code of Conduct`
- `Changelog`
- `Acknowledgements` / `Credits` / `Sponsors` / `Authors`
- `Table of Contents` / `TOC`

Exclusion is scope-aware: once you enter an excluded section, every
nested subsection is also excluded until the heading level returns
above the excluded section's level.

## Fields produced per claim

```yaml
- id: claim-001
  title: <first 80 chars of the bullet or row>
  source: README.md                # which file it came from
  source_ref: "section 'Features'" # which heading path
  priority: critical | high | medium | low
  area: core | numeric-claims | meta
  statement: <the extracted text>
  business_expectation: <generic wording per rule>
  evidence_needed: <generic wording per rule>
  status: untested
  needs_review: true
  confidence: low | medium | high
  extractor_rule: <rule name>
```

## Dedupe

Claims with the same statement + source are merged. When duplicates
have different confidences, the extractor keeps the higher one. This
prevents the same capability from appearing multiple times when a
README mentions the same thing in both a bullet and a table.

## Known limitations

- **No LLM.** The extractor is pure regex + markdown parsing. It will
  miss paraphrased or narrative claims that do not appear under a
  conventional heading.
- **No cross-file reconciliation.** If README.md and SKILL.md make
  contradictory claims, both are extracted — the reviewer must
  reconcile.
- **No inference.** The extractor will not invent an implicit claim
  from surrounding text. This is a feature: it cannot hallucinate
  capabilities the repo never actually promised.
- **Title language is the bullet's language.** Mixed-language repos
  will produce mixed-language draft titles.
- **Generic `business_expectation` and `evidence_needed`** — these are
  template strings per rule. The reviewer should rewrite them to be
  specific to the capability.

## When to use the extractor

- Starting a new repo eval from scratch
- Picking up a repo that someone else scoped and you want a sanity
  check on what claims they might have missed
- Comparing an existing claim map against the README to surface
  claims that were added to the README but never made it into the
  eval scaffold

## When NOT to use the extractor

- As a replacement for reading the target repo yourself
- On repos whose README is marketing fluff rather than capability
  promises
- As a source of final, commit-ready claim maps (always review)
