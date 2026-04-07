# Claude Implementation Prompt — repo-evals Platform

You are implementing the next version of `zinan92/repo-evals`.

Read this roadmap first:

- `/Users/wendy/work/repo-evals/docs/2026-04-07-repo-evals-platform-roadmap.md`

Your job is to implement the roadmap in phases, with strong attention to:

- trustworthiness
- auditability
- backward compatibility
- incremental shipping

Do not jump straight to the dashboard.
The platform must earn the dashboard by first making the underlying evaluation data trustworthy.

## High-Level Goal

Upgrade `repo-evals` from a claim-first evaluation template repo into a durable evaluation platform that can:

- preserve provenance
- preserve portable evidence
- recommend verdict buckets consistently
- improve claim coverage quality
- support multiple repo archetypes
- compare re-evals over time
- surface status across many repos

## Delivery Order

Implement in this exact order unless blocked:

1. Session Replay / Provenance Capture
2. Portable Evidence Copier
3. Verdict Calculator
4. Fixture Registry
5. Repo Archetype Templates
6. Coverage Gap Detector
7. Claim Extraction Assistant
8. Re-Eval Diff Mode
9. Cross-Run Dashboard

## Non-Negotiable Rules

1. Preserve file-based auditability.
   Git remains the source of truth.

2. Do not break existing repo folders.
   Existing evaluations must continue to load.

3. If a new schema is introduced, provide a migration path.

4. Make strong verdict ceilings explicit in code and docs.
   In particular:
   - untested core layer must cap overall verdict at `usable`

5. Prefer structured YAML/JSON outputs over opaque prose when the platform needs to reason over data later.

6. Keep every step reviewable from GitHub alone whenever possible.

## Phase 1 Requirements

### A. Provenance Capture

Implement a durable provenance model for runs.

At minimum, support:

- repo_evals_commit
- target_repo_path
- target_repo_ref
- target_repo_commit
- runner
- agent
- model
- terminal_session_id
- agent_session_id
- evaluated_at
- provenance_source
- transcript_path
- command_log_path
- session_replay_notes

Tasks:

- update schema/templates
- update scaffolding scripts
- add helper(s) to append provenance after a run
- support partial legacy provenance explicitly

### B. Portable Evidence Copier

Implement a standardized way to copy evidence into:

- `runs/.../artifacts/`
- `runs/.../logs/`

Requirements:

- file copy support
- directory snapshot support for small trees
- metadata-only stubs for large artifacts
- generated evidence manifest with size + hash

### C. Verdict Calculator

Implement a rule-guided verdict recommendation system.

Inputs should include:

- claim status map
- archetype
- evidence completeness
- coverage summary
- core layer tested or not

Outputs should include:

- recommended bucket
- ceiling reason
- confidence
- blocking issues
- override support

## Phase 2 Requirements

### D. Fixture Registry

Create a reusable fixture registry with metadata, not just loose files.

### E. Repo Archetype Templates

Support at least:

- pure-cli
- prompt-skill
- hybrid-skill
- adapter
- orchestrator
- api-service

### F. Coverage Gap Detector

Identify critical claims not covered by plan or evidence.

### G. Claim Extraction Assistant

Generate draft claim maps from README/SKILL/docs/examples.
Mark extracted claims as review-required.

## Phase 3 Requirements

### H. Re-Eval Diff Mode

Compare two evaluation points and summarize:

- claim deltas
- bucket delta
- newly closed gaps
- regressions

## Phase 4 Requirements

### I. Cross-Run Dashboard

Build a dashboard that consumes the structured data created in earlier phases.

UI guidance:

- draw inspiration from `nicobailon/visual-explainer`
- optimize for clarity, repo drill-down, and “what changed?”
- do not prioritize flashy charts over reliable information architecture

## Expected Artifacts

By the end of implementation, the repo should contain:

- updated schemas/templates
- new scripts/commands
- any migration helpers needed for existing runs
- updated docs
- tests for the new logic
- if applicable, a dashboard app or static dashboard generator

## Working Style

1. Start by inspecting the current repo structure.
2. Create a short implementation plan before coding.
3. Ship in small commits by phase.
4. Add tests wherever behavior becomes rule-driven.
5. Update docs as you go, not at the very end.

## Success Criteria

The implementation is successful when:

- provenance is captured by default
- evidence is portable by default
- verdict logic is partly machine-guided and auditable
- archetypes affect scaffolding
- fixture reuse is built into the system
- re-evals can be compared directly
- the dashboard shows trustworthy data, not guessed summaries

## First Step

Begin with Phase 1 only.

Before writing code:

1. inspect the current repo
2. write a concise implementation plan for Phase 1
3. then implement Phase 1 end to end

Do not begin Phase 2 until Phase 1 is complete and documented.
