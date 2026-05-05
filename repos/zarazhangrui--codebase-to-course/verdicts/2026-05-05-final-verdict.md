# codebase-to-course — final verdict (2026-05-05)

## Repo

- **Name:** zarazhangrui/codebase-to-course
- **Branch:** main@HEAD
- **Archetype:** hybrid-skill
- **Layer:** molecule
- **Stars:** 4,224

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 SKILL.md frontmatter + triggers | passed | 7+ trigger phrases in description; auto-discovery should work |
| 002 real shipped assets | passed | styles.css 1195 lines + main.js 498 lines + build.sh + 2 HTML templates |
| 003 reference docs depth | passed | 5 docs all > 2 KB; interactive-elements.md = 32 KB (deepest) |
| 004 build.sh is real assembler | passed | `set -e` + cat _base + modules + _footer → index.html |
| 005 directory matches README | passed | structure 1:1 with documented layout |
| 006 LICENSE present | **failed** | HTTP 404 — no LICENSE file at root |

| 007 live agent end-to-end | untested | needs Claude Code session on a real codebase |

## Real findings

1. **No LICENSE file.** A 4.2K-star skill users copy into their
   personal `~/.claude/skills/` should have one. Without it, anyone
   modifying / forking / commercially distributing the generated
   courses has no legal cover. **Easy fix upstream:** add MIT or
   Apache-2.0.

2. **Genuinely hybrid, not "markdown with hopes".** Many skills label
   themselves "hybrid" but ship only SKILL.md. This one ships 1,200
   lines of CSS, 500 lines of JS, an assembler script, and 5
   substantive reference docs (totaling ~57 KB). The LLM has real
   building blocks to work from.

3. **`build.sh` is minimal but correct.** 6 lines. Could be done
   inline in SKILL.md as a code block, but having it as a script
   means users can re-run `bash build.sh` after editing modules.

4. **interactive-elements.md is the deepest spec (32 KB).** Sensible
   prioritization — quizzes / animations / visualizations are the
   most variable surface; design system + content philosophy are
   shorter because they need fewer worked examples.

## Why not higher

- Single live run not yet logged (molecule layer cap).
- LICENSE missing — small but real legal gap that pulls the score.

## Path forward

1. Add LICENSE (MIT or Apache-2.0) → claim-006 → passed → +5 score.
2. Run on a real codebase in Claude Code → claim-007 → passed → live
   evidence raises confidence to high.
3. Multiple logged runs across codebase shapes → score 80+.

## Recommended

```yaml
status: evaluated
```

The score model will assign the bucket; this dossier is the
evidence trail behind it.
