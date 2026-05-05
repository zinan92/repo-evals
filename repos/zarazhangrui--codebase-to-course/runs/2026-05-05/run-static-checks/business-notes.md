# codebase-to-course — static-checks run, 2026-05-05

## Findings

### claim-001: SKILL.md frontmatter — **passed**

SKILL.md is 221 lines. Frontmatter declares `name + description`,
where the description is a single long line packed with trigger
phrases (`'turn this into a course'`, `'explain this codebase
interactively'`, `'teach this code'`, `'interactive tutorial from
code'`, `'codebase walkthrough'`, `'learn from this codebase'`,
`'make a course from this project'`). Claude Code's skill loader
should auto-discover on any of these.

### claim-002: real shipped assets — **passed**

| Asset | Size |
|---|---|
| references/styles.css | 1,195 lines / 34 KB |
| references/main.js | 498 lines / 19 KB |
| references/build.sh | 6 lines / 210 B |
| references/_base.html | 55 lines / 2.2 KB |
| references/_footer.html | 4 lines / 27 B |

This is a hybrid skill in the real sense — not just markdown
prompting; the LLM emits per-module HTML and `build.sh` cats
templates + modules into a final `index.html`. Browser opens it
directly with no setup.

### claim-003: reference doc depth — **passed**

| Doc | Size |
|---|---|
| interactive-elements.md | 32 KB (biggest — matches hypothesis) |
| design-system.md | 12 KB |
| content-philosophy.md | 9 KB |
| gotchas.md | 3 KB |
| module-brief-template.md | 2.5 KB |

All 5 substantively sized. The biggest is the interactive-elements
spec (quizzes, animations, visualizations) — that's the right place
for the LLM to lean on at generation time.

### claim-004: build.sh assembler — **passed**

```bash
#!/bin/bash
# Assembles the course from parts.
# Run from the course directory: bash build.sh
set -e
cat _base.html modules/*.html _footer.html > index.html
echo "Built index.html — open it in your browser."
```

Minimal and correct. `set -e` so any cat failure bubbles up.

### claim-005: directory structure — **passed**

Repo has `README.md`, `SKILL.md`, `references/`. README's "Skill
structure" diagram shows the same layout. No drift between docs and
code.

### claim-006: LICENSE — **FAILED**

```
curl https://raw.githubusercontent.com/zarazhangrui/codebase-to-course/main/LICENSE
→ HTTP 404
```

No LICENSE file at repo root. For a 4.2K-star skill that users will
copy into their `~/.claude/skills/`, this is a real gap — anyone
forking, modifying, or shipping the generated courses commercially
has no legal cover. Easy fix upstream (add MIT or Apache-2.0).

## What is still untested (claim-007)

Live agent session generating a course from a real codebase.
Ideal scenarios:

1. Small Next.js or Flask app (< 5,000 lines) — verify happy path:
   the skill produces 5-7 modules + a working `index.html` that
   opens in the browser.
2. Multi-language monorepo — does the skill scope sensibly or wedge?
3. Very small repo (< 500 lines) — does the 5-7 module structure
   degrade gracefully or feel padded?

## Verdict implication

Strong static layer (5/6 claims passed) with one real defect
(missing LICENSE). The skill is structurally complete: real assets,
real assembler, real reference docs. The molecule layer cap holds
until at least one logged live run.

Penalty: -5 for missing license. Score expected in the 60-69 (Try)
range, possibly higher with multi-platform / popular skill.
