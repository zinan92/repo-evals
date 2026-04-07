# repo-evals Platform Roadmap

Date: 2026-04-07
Owner: Wendy
Target Repo: `zinan92/repo-evals`
Status: Proposed roadmap for implementation

## Goal

Upgrade `repo-evals` from a claim-first evaluation template repo into a durable evaluation platform.

The platform should not only store plans and verdicts. It should also:

- preserve trustworthy execution provenance
- keep evidence reviewable from GitHub alone
- reduce evaluator variance
- improve eval-plan coverage quality
- support different repo archetypes
- compare re-evals over time
- surface the state of all evaluated repos in one dashboard

## Product Principles

1. Trust before convenience.
   If provenance and evidence are weak, UI and summaries are not enough.

2. Business-readable on top, technical truth underneath.
   Non-technical readers should understand the plan and verdict.
   Technical reviewers should still be able to audit the evidence.

3. Strong verdicts require strong evidence.
   The platform should make it harder to over-rate a repo.

4. Repo types matter.
   A hybrid skill repo should not be evaluated like a pure CLI.

5. Re-evaluation is a first-class workflow.
   The system should make it easy to see what improved, regressed, or remained unknown.

## Current Gaps

The current repo already has a strong direction, but still has platform-level gaps:

- provenance capture exists only as a schema, not as a full workflow
- evidence portability is policy-driven, not automated
- verdict assignment is still mostly manual
- claim extraction is evaluator-heavy
- coverage gaps are not automatically flagged
- repo archetypes are not encoded into scaffold generation
- there is no cross-run dashboard
- fixtures are scattered and not managed as a reusable asset library
- re-eval diffs are not automatic

## Scope

This roadmap covers items 1-9 below:

1. Session Replay / Provenance Capture
2. Portable Evidence Copier
3. Verdict Calculator
4. Claim Extraction Assistant
5. Coverage Gap Detector
6. Repo Archetype Templates
7. Cross-Run Dashboard
8. Fixture Registry
9. Re-Eval Diff Mode

## Prioritized Roadmap

### Phase 1: Trust Foundation

Priority: Highest

Includes:

- 1. Session Replay / Provenance Capture
- 2. Portable Evidence Copier
- 3. Verdict Calculator

Why this phase first:

- Without provenance, evals are hard to audit
- Without copied evidence, GitHub cannot serve as the review surface
- Without consistent verdict logic, bucket meaning drifts over time

Expected outcome:

- Every new run is traceable
- Evidence is portable and durable
- Verdicts become more consistent and explainable

### Phase 2: Evaluation Quality And Speed

Priority: High

Includes:

- 8. Fixture Registry
- 6. Repo Archetype Templates
- 5. Coverage Gap Detector
- 4. Claim Extraction Assistant

Why in this order:

- Fixtures improve evaluator speed immediately
- Archetypes shape what “good coverage” even means
- Coverage detection depends on a stable archetype model
- Claim extraction becomes more useful once the system knows what structure to aim for

Expected outcome:

- Evaluators stop rebuilding test inputs from scratch
- Plans become more representative of true repo capability
- Claim extraction becomes guided instead of generic

### Phase 3: Longitudinal Intelligence

Priority: High

Includes:

- 9. Re-Eval Diff Mode

Why:

- Once provenance, evidence, and structured verdict inputs exist, re-eval comparison becomes genuinely meaningful
- This converts repo-evals from a one-shot report system into a continuous trust system

Expected outcome:

- “Did this repo actually improve?” becomes easy to answer
- Fixes can be tied to claim-level movement and bucket movement

### Phase 4: Visualization Layer

Priority: Medium-High

Includes:

- 7. Cross-Run Dashboard

Why last:

- The dashboard should be a consumer of structured data, not a substitute for missing structure
- By the time this phase starts, the platform will already have enough reliable data to justify a visual surface

Implementation note:

- Reuse concepts and UI patterns from `https://github.com/nicobailon/visual-explainer`
- Focus on clarity, drill-down, and “what changed?” over decorative charts

Expected outcome:

- One place to see repo status, bucket, coverage gaps, and re-eval movement

## Feature Specs

## 1. Session Replay / Provenance Capture

### Problem

Today, some evaluations can be read, but not fully replayed or traced to the original execution environment.

### Objectives

- Capture evaluation provenance automatically when possible
- Preserve enough metadata to reconstruct “what happened”
- Distinguish between fully captured and partial legacy runs

### Requirements

- Every `run-summary.yaml` should support:
  - `repo_evals_commit`
  - `target_repo_path`
  - `target_repo_ref`
  - `target_repo_commit`
  - `runner`
  - `agent`
  - `model`
  - `terminal_session_id`
  - `agent_session_id`
  - `evaluated_at`
- Add support for:
  - `provenance_source`
  - `transcript_path`
  - `command_log_path`
  - `session_replay_notes`
- Provide a helper that can append provenance after a run if it was initially missing
- Add a “partial provenance” flag for legacy runs

### Deliverables

- Updated schema
- Provenance capture helper
- Legacy migration support

### Acceptance Criteria

- A new run created with environment variables auto-populates provenance
- A legacy run can be marked partial instead of pretending to be complete
- A reviewer can tell which commit and which session produced a result

## 2. Portable Evidence Copier

### Problem

Evidence often originates in `/tmp` or target repo folders and is not guaranteed to survive.

### Objectives

- Copy representative evidence into the run folder
- Make GitHub alone sufficient for review of important cases

### Requirements

- Provide a script that:
  - copies selected files into `runs/.../artifacts/`
  - copies logs into `runs/.../logs/`
  - writes a manifest of copied files
  - records file sizes and hashes
- Support:
  - direct file copy
  - directory snapshot for small trees
  - safe skip for very large files with stub metadata
- Add an evidence-manifest file in each run

### Deliverables

- `copy-evidence.sh` or equivalent
- `artifacts/manifest.yaml`
- docs on when to copy full files vs metadata stubs

### Acceptance Criteria

- A run can be reviewed from GitHub without relying on `/tmp`
- The run tells a reviewer exactly what was copied and what was omitted

## 3. Verdict Calculator

### Problem

Verdicts are currently thoughtful, but still evaluator-dependent.

### Objectives

- Provide a rule-guided verdict recommendation
- Keep human override, but make it explicit

### Requirements

- Inputs:
  - claim statuses
  - coverage summary
  - archetype
  - core layer tested or not
  - evidence completeness
- Outputs:
  - recommended bucket
  - ceiling reason
  - blocking issues
  - confidence level
- Must support hybrid repo rule:
  - untested core layer caps overall verdict at `usable`
- Human override should require:
  - `override: true`
  - `override_reason`

### Deliverables

- bucket scoring logic
- explanation renderer
- verdict template update

### Acceptance Criteria

- Given the same structured inputs, two evaluators get the same recommended bucket
- Override path is explicit and auditable

## 4. Claim Extraction Assistant

### Problem

Claim extraction is currently high-value but labor-intensive.

### Objectives

- Generate a useful first draft of claim maps
- Reduce evaluator toil without removing judgment

### Requirements

- Parse and suggest claims from:
  - README
  - SKILL.md
  - examples
  - error docs
  - badges and numeric claims
- Proposed claim attributes:
  - title
  - source
  - source_ref
  - priority
  - area
  - statement
  - business_expectation
  - evidence_needed
- Output as a reviewable draft, not final truth

### Deliverables

- claim extraction command
- “needs review” markers
- confidence annotations per proposed claim

### Acceptance Criteria

- A new repo can get a useful draft claim map in one command
- Numeric claims and README promises are not silently missed

## 5. Coverage Gap Detector

### Problem

An eval plan can look solid while still missing critical claims.

### Objectives

- Detect missing or weakly covered claims before verdict time

### Requirements

- Compare:
  - `claim-map.yaml`
  - `eval-plan.md`
  - run coverage
- Flag:
  - critical claims not in plan
  - plan scenarios with no technical evidence
  - only-static validation for inherently dynamic claims
  - claims still marked untested at verdict time

### Deliverables

- gap report generator
- severity levels
- summary for plan reviewers

### Acceptance Criteria

- A repo with major uncovered claims is visibly flagged before a strong verdict is assigned

## 6. Repo Archetype Templates

### Problem

Different repo types need different evaluation shapes, but the current scaffold is generic.

### Objectives

- Make evaluation scaffolding repo-type aware

### Archetypes To Support Initially

- pure-cli
- prompt-skill
- hybrid-skill
- adapter
- orchestrator
- api-service

### Requirements

- Archetype-specific:
  - claim prompts
  - plan sections
  - verdict ceilings
  - recommended scenario matrix
  - recommended evidence expectations

### Deliverables

- archetype registry
- scaffold generation by archetype
- docs that explain when to use each archetype

### Acceptance Criteria

- `frontend-slides`-type hybrid repos and `content-downloader`-type adapters no longer need the same default scaffold

## 7. Cross-Run Dashboard

### Problem

The repo contains information, but not a fast way to see platform-level state.

### Objectives

- Surface the whole evaluation portfolio in one place
- Make trust state easy to scan

### Requirements

- Dashboard views:
  - all repos
  - single repo detail
  - claim coverage
  - latest verdict
  - unresolved gaps
  - recent changes
- Integrate a visual comparison style inspired by:
  - `nicobailon/visual-explainer`

### Deliverables

- static or app-based dashboard
- data ingestion layer from repo files
- drill-down links into raw artifacts and verdict docs

### Acceptance Criteria

- A reviewer can answer “What is the current state of all evaluated repos?” in under 2 minutes

## 8. Fixture Registry

### Problem

Evaluators repeatedly spend time finding or recreating realistic fixtures.

### Objectives

- Treat fixtures as a shared productivity asset
- Reuse realistic inputs across repos and re-evals

### Requirements

- Create a fixture catalog with:
  - fixture id
  - business description
  - media type
  - language
  - complexity
  - applicable archetypes
  - privacy sensitivity
  - known caveats
- Support both:
  - global fixture registry
  - repo-local fixture references

### Deliverables

- `fixtures/registry.yaml` or equivalent
- fixture metadata schema
- docs on naming and privacy rules

### Acceptance Criteria

- Evaluators can select a fixture from a known catalog instead of hunting manually

## 9. Re-Eval Diff Mode

### Problem

After a repo changes, there is no standardized way to show what improved or regressed.

### Objectives

- Make re-evaluation a first-class workflow
- Compare claim-level and bucket-level movement over time

### Requirements

- Compare two runs or two verdict points
- Show:
  - claim status changes
  - coverage changes
  - bucket changes
  - newly closed gaps
  - newly opened regressions
- Produce:
  - machine-readable diff
  - business-readable summary

### Deliverables

- re-eval diff generator
- per-repo history view
- optional dashboard integration

### Acceptance Criteria

- A reviewer can answer “Did this repo really get better?” without manual diff reading

## Data Model Changes

At minimum, implementation should evolve the data model to support:

- provenance
- evidence manifests
- archetype
- coverage summary
- verdict recommendation
- override metadata
- run history linkage
- fixture references

## Suggested Milestones

### Milestone 1

- 1 Provenance
- 2 Evidence copier
- 3 Verdict calculator

### Milestone 2

- 8 Fixture registry
- 6 Archetype templates
- 5 Coverage gap detector
- 4 Claim extraction assistant

### Milestone 3

- 9 Re-eval diff mode

### Milestone 4

- 7 Cross-run dashboard

## Out Of Scope For This Cycle

- Full autonomous repo evaluation engine
- Cloud execution farm
- Multi-user auth and permissions
- Hosted SaaS version

## Implementation Guidance

- Prefer incremental, file-based architecture first
- Keep Git as the source of truth
- Avoid over-abstracting before archetypes are proven in real use
- Make every stage auditable from raw files
- Add migrations for existing runs where possible

## Definition Of Done

This roadmap is complete when:

- new runs capture provenance by default
- evidence is portable by default
- verdicts have a rule-guided recommendation path
- archetypes shape scaffolding and ceilings
- fixture reuse is real, not just aspirational
- re-evals can be compared systematically
- dashboard gives a trustworthy overview of portfolio state
