# @remotion/skills — static-checks run, 2026-05-04

Eval scope: SKILL.md frontmatter, rules depth, distribution status,
in-repo studio harness. No live agent session.

## Findings

### claim-001: SKILL.md shape — **passed**

```
---
name: remotion-best-practices
description: Best practices for Remotion - Video creation in React
metadata:
  tags: remotion, video, react, animation, composition
---

## When to use
…
```

Standard Claude Skills frontmatter (name + description + tags) plus a
"When to use" section. SKILL.md is 340 lines with code examples
(`useCurrentFrame()`, `interpolate()`, Easing, etc.).

### claim-002: rules depth — **passed**

35 markdown files in `skills/remotion/rules/`:
- 30 are over 1 KB (substantive content, not stubs)
- topics include 3d, audio, audio-visualization, captions,
  compositions, ffmpeg, fonts, lottie, mapbox, light-leaks, gifs, etc.
- mapbox.md is 11.3 KB (deepest single rule)

Tail of "is the project mature": yes.

### claim-003: distribution — **passed**

```
package.json: { "private": true }
npm registry @remotion/skills/latest: HTTP 404
```

Consistent. README's one-line "internal package, no documentation"
matches the npm reality.

### claim-004: studio harness — **passed**

`src/index.ts`:
```ts
import {registerRoot} from 'remotion';
import {RemotionRoot} from './Root';
registerRoot(RemotionRoot);
```

`src/Root.tsx` declares 3 `<Composition>` entries (BarChart,
Typewriter, WordHighlight) and imports each from
`../skills/remotion/rules/assets/<name>.tsx`. All 3 imports resolve
(verified by HTTP 200 on the raw URL). `npm run dev` would launch the
Remotion studio on these compositions — the rules aren't just
markdown, the maintainers self-test a few of them as live React.

## What is still untested (claim-005)

End-to-end skill execution:

1. Copy `skills/remotion/SKILL.md` + `skills/remotion/rules/` into a
   Claude Code skills directory (`~/.claude/skills/remotion/`).
2. In a Claude Code session, ask "use Remotion to write a fade-in
   animation".
3. Verify the agent references SKILL.md, follows
   `useCurrentFrame()` + `interpolate()` + Easing patterns from the
   skill, rather than improvising.
4. Repeat for one rule-specific topic (e.g. captions, audio) and
   verify the agent reads the corresponding rules/<topic>.md.
5. Log under `runs/<date>/run-live-agent/business-notes.md`.

## Verdict implication

Sparse README hides high-quality content. Distribution is internal,
which limits reach but is honest. Static layer is clean — every
documented surface is real. Per the atom rule, the bucket is `usable`
until at least one logged agent session shows the skill drives
behavior.

Recommended bucket: **usable**.
