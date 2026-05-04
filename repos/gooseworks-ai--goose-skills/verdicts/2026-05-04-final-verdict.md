# goose-skills — final verdict (2026-05-04)

## Repo

- **Name:** gooseworks-ai/goose-skills
- **Branch evaluated:** main@HEAD (skills-index 1.2.0, generated 2026-04-29)
- **Archetype:** prompt-skill (catalog of prompt skills)
- **Layer:** **molecule** at the repo level (catalog wired by
  manifest + npm installer); individual skills have their own layer
  (capabilities ≈ atom, composites ≈ molecule, playbooks ≈ compound)
- **Eval framework:** repo-evals layer model v1 (fe256e5)

## Bucket

**`usable`** — strong static layer; capped by the molecule rule
because no live skill execution has been logged on this evaluator's
machine.

## What was evaluated

### Atom + molecule level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 catalog count | passed_with_concerns | 204 skills in manifest vs 108 in README — docs stale |
| 002 three categories | passed | 143 capabilities + 56 composites + 5 playbooks, all non-empty |
| 003 metadata contract | passed | Sampled 3 skills — uniform shape with `installation.{base_command, supports}` |
| 004 npm + bin | passed_with_concerns | bin/goose-skills.js exists (12.5 KB); npm@1.1.0 is ahead of repo@1.0.1 |
| 005 packs | passed | 2 real packs (lead-gen-devtools=7 skills, video-production=5 skills); README's "7-skill" claim matches |
| 006 cross-platform | passed | All 204 skills declare `supports = [claude, cursor, codex]` (100% uniform) |

### Molecule level (deferred)

| Claim | Status | Required |
|---|---|---|
| 007 live skill execution | untested | install via `npx`, run 1 capability + 1 composite + 1 playbook in a real agent session, log token + output evidence |

## Real findings worth surfacing

1. **Cap/Comp/Play taxonomy ≈ atom/molecule/compound.** Goose's
   internal classification (capabilities → composites → playbooks) is
   functionally identical to repo-evals' atom/molecule/compound layer
   model. We didn't invent the insight; we formalized it. This is
   worth surfacing in the meta-reflection on framework neutrality.

2. **README is meaningfully out of date.** "108 skills" is the
   headline, "204" is the reality. Not a false claim, but it
   under-sells the catalog and could send users to the npm package
   thinking the surface is half what it is.

3. **npm is one minor version ahead of repo.** A user reading the
   source on `main` (v1.0.1) sees something different from what
   `npx goose-skills install` ships (v1.1.0 on the registry). Not
   broken, but a maintainer / contributor will be confused.

4. **Pack contract is real, not marketing.** Both packs ship genuine
   `shared_files` (.env.example + requirements.txt + more), so
   "configure once, use whole pack" is structurally enforced, not
   just suggested.

## Why not higher

`usable` is the right ceiling because:

- No live skill execution evidence on this machine. The catalog could
  have 204 manifest entries and still ship low-signal SKILL.md content
  inside any one of them. Per-skill quality is the trust-determining
  variable, and we sampled only the manifest, not the prompt content.
- Skill quality is heterogeneous by definition (different authors,
  different review depth) — we'd need to sample, not assume.

## Path to `reusable`

1. `npx gooseworks install --claude` in fresh Claude Code.
2. Pick 1 skill per category (suggested: `brand-voice-extractor` /
   `competitor-intel` / `competitor-monitoring-system`).
3. Run each on a representative input. Capture the agent's
   intermediate plan, final output, and token usage.
4. Log under `runs/<date>/run-live-execution/` with one business-notes
   per skill.
5. Update claim-007 status. If all three pass with a useful artefact
   and the `lead-gen-devtools` pack also runs end-to-end, candidate
   for `reusable` (still not `recommendable` until 2nd evaluator).

## Recommended

```yaml
current_bucket: usable
status: evaluated
```
