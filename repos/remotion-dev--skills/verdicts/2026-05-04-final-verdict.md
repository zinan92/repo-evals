# @remotion/skills — final verdict (2026-05-04)

## Repo

- **Name:** remotion-dev/skills (`@remotion/skills`)
- **Branch evaluated:** main@HEAD (4.0.456, private package)
- **Archetype:** prompt-skill
- **Layer:** **atom** — single SKILL.md with reference rules
- **Eval framework:** repo-evals layer model v1 (4acbd5d)

## Bucket

**`usable`** — sparse public README hides high-quality, well-curated
content. Atom rule caps `usable` until a live agent session
demonstrates the skill drives behaviour.

## What was evaluated

### Atom level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 SKILL.md shape | passed | Standard frontmatter (name + description + tags) + "When to use" + 340-line body with code examples |
| 002 rules depth | passed | 35 markdown rules, 30 over 1 KB; covers audio, captions, ffmpeg, lottie, mapbox, fonts, etc. |
| 003 internal-only distribution | passed | `package.json: { private: true }` + npm registry 404, consistent with README's "internal package" |
| 004 studio harness | passed | `src/index.ts` calls registerRoot; Root.tsx imports 3 rule assets that all exist; the maintainers self-test a few rules as live React |

### Atom level (deferred — live)

| Claim | Status | Required |
|---|---|---|
| 005 agent reads SKILL.md and generates Remotion code | untested | Copy SKILL.md + rules/ into a Claude Code session, ask for a Remotion task, verify the agent references the skill |

## Real findings worth surfacing

1. **README dramatically undersells the package.** One sentence
   ("internal package, no documentation") reads as abandonware, but
   the actual content is 110 KB of curated guidance authored by the
   official Remotion team. A maintainer-facing repo with an
   end-user-facing skill — the README is honest about the audience
   but misleading about the value.

2. **The studio harness is a self-test.** `src/Root.tsx` loads three
   rules/assets/*.tsx files as live Remotion compositions. That's a
   structural guarantee that at least three rules survive `npm run
   dev` — better than a "all rules are markdown only" claim.

3. **Internal package = clone-and-copy.** Users wanting this skill
   for their own AI agent need to git clone the repo and copy
   `skills/remotion/` into their skills directory. There's no `npm
   install` path, and the README doesn't tell you that — a small
   discoverability gap.

## Why not higher

`usable` is the right ceiling because:

- No live agent evidence on this machine. The skill's job is to
  influence LLM output; that can only be measured by running an LLM.
- Single-evaluator, single-day pass.

## Path to `reusable`

1. `git clone` and copy `skills/remotion/` to `~/.claude/skills/remotion/`.
2. Open Claude Code, ask: "use Remotion to write a 2-second fade-in
   animation".
3. Verify the agent uses `useCurrentFrame()` + `interpolate()` +
   Easing as the skill prescribes.
4. Repeat for an audio or caption topic; verify the agent loads the
   matching rules/<topic>.md.
5. Log under `runs/<date>/run-live-agent/`.

## Recommended

```yaml
current_bucket: usable
status: evaluated
```
