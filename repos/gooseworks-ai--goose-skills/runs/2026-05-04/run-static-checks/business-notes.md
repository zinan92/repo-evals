# goose-skills — static-checks run, 2026-05-04

Eval scope: catalog manifest, taxonomy, metadata contract, npm
publish, packs, cross-platform support. No live skill execution.

## Findings

### claim-001: catalog count vs README — **passed_with_concerns**

README header still advertises **"108 skills"** with a sub-header
breakdown of 51 Cap + 52 Comp + 5 Play. `skills-index.json` (version
1.2.0, generated 2026-04-29) actually carries **204 skills** with
breakdown 143 + 56 + 5. README is stale; catalog is bigger.

This isn't a false promise (under-promise + over-deliver), but it is a
real DX gap: a user searching the README to know if a topic is
covered will see a smaller surface than what they'd actually get.

### claim-002: three-category taxonomy — **passed**

| Category | Count | Per repo-evals layer model |
|---|---|---|
| capabilities | 143 | atom (single-purpose) |
| composites | 56 | molecule (multi-skill chains) |
| playbooks | 5 | compound (end-to-end workflows) |

The Cap/Comp/Play taxonomy is a near-perfect parallel to repo-evals'
own atom/molecule/compound layer model — same insight, formalized
independently. Worth noting in the meta-reflection.

### claim-003: per-skill metadata contract — **passed**

Sampled 3 skills, each carries:

```
slug, name, category, description, tags, path,
files: [SKILL.md, skill.meta.json],
metadata: { slug, category, tags, installation: { base_command, supports } }
```

Uniform shape across the sample. Not a guarantee that all 204 are
identical, but the manifest enforcement looks systematic.

### claim-004: npm install path — **passed_with_concerns**

`package.json` declares `bin: { goose-skills: ./bin/goose-skills.js }`.
The bin file exists (12.5 KB, real script). npm registry shows
**`goose-skills@1.1.0`** as the latest published version. But
`package.json` on `main` declares **`1.0.1`**.

Two reads are possible:
- (a) Releases happen on a different branch and `main` is the dev
  HEAD, so users get 1.1.0 from npm and the repo just hasn't merged
  the bump.
- (b) The bump was done in CI/automation but the source isn't pushed
  back to `main`.

Either way, a contributor reading `main` will see code that doesn't
match what `npx gooseworks install` actually pulls. Worth a docs note
or a release-process explanation.

### claim-005: skill packs — **passed**

`packs` array has 2 entries:

| Pack | Skills | Shared files |
|---|---|---|
| lead-gen-devtools | 7 | 2 (.env.example, requirements.txt) |
| video-production | 5 | 4 |

`lead-gen-devtools` matches the README's "7-skill lead generation
toolkit" exactly. Packs ship `shared_files` so a user configures env
vars / pip deps once and uses the whole pack.

### claim-006: cross-platform support — **passed**

Every one of the 204 skills declares
`metadata.installation.supports = ["claude", "cursor", "codex"]`.
100% uniform — no skill is platform-locked. This is a strong
signal: README's headline ("Works with Claude Code · Cursor · Codex")
is enforced through the manifest, not just marketing.

## What is still untested (claim-007)

Whether a skill, once installed, actually drives the agent to do the
documented work. To clear this, run:

1. `npx gooseworks install --claude` in a fresh Claude Code session.
2. Ask the agent to use one capability (e.g. `brand-voice-extractor`)
   on a test input. Capture session output.
3. Same for one composite (e.g. `competitor-intel`) and one playbook
   (e.g. `competitor-monitoring-system`).
4. Log under `runs/<date>/run-live-execution/business-notes.md` with
   token usage, output quality (subjective rating + rationale), and
   any external API hits the skill triggered.

## Verdict implication

Static layer is strong: 204 skills, uniform contract, three real
categories matching the documented taxonomy, real packs, real npm
package. Two soft concerns — README count is stale and npm-vs-repo
version mismatch — neither blocks `usable` but both should be
disclosed.

The molecule rule caps `usable` until at least one logged live skill
execution proves the catalog's actual instructional content drives
agents correctly. That bar is per-skill, so any "the catalog as a
whole is good" claim needs sampling discipline.

Recommended bucket: **usable**.
