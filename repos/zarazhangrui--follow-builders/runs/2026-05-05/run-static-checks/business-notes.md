# follow-builders — static-checks run, 2026-05-05

## Findings

### claim-001: SKILL.md complete — **passed**

466-line SKILL.md with standard frontmatter:

```
name: follow-builders
description: AI builders digest — monitors top AI builders on X and
  YouTube podcasts, remixes their content into digestible summaries.
  Use when the user wants AI industry insights, builder updates, or
  invokes /ai. No API keys or dependencies required — all content is
  fetched from a central feed.
```

The 466-line body is unusually thorough for a skill — implies serious
work behind it.

### claim-002: 5 prompt files — **passed**

| Prompt | Size |
|---|---|
| digest-intro.md | 2.6 KB |
| summarize-podcast.md | 1.4 KB |
| summarize-tweets.md | 1.2 KB |
| summarize-blogs.md | 1.1 KB |
| translate.md | 1.0 KB |

All 5 README-listed prompt files present; sizes suggest real content.

### claim-003: source list matches README — **passed**

The README claim of "25 builders + 6 podcasts + 2 blogs" lives in
`config/default-sources.json`:

```json
{
  "x_accounts":  25 entries,
  "podcasts":    6 entries,
  "blogs":       2 entries
}
```

Exact match. (Initial probe of `feed-*.json` was misleading — those
are pre-fetched recent-content snapshots, not the source list. The
source list is the config file.)

### claim-004: Node.js pipeline — **passed**

| Script | Size | Role |
|---|---|---|
| generate-feed.js | 38 KB | central pipeline that builds `feed-*.json` |
| prepare-digest.js | 5 KB | per-user digest assembly |
| deliver.js | 7 KB | dispatch to Telegram / email / in-chat |

generate-feed.js being 38 KB suggests substantial logic — scraping +
summarization orchestration. The "no API keys needed" promise is
real because the maintainer runs this central pipeline; users only
consume the JSON output.

### claim-005: bilingual — **passed**

README.zh-CN.md exists (HTTP 200); `prompts/translate.md` is a real
translation prompt. Skill genuinely supports EN / ZH / bilingual.

### claim-006: LICENSE — **FAILED**

```
HTTP 404
```

No LICENSE at repo root — same gap as `codebase-to-course`. Pattern:
both of Zara's recent skills ship without LICENSE. Easy fix upstream.

## What is still untested (claim-007)

End-to-end:

1. In Claude Code, say "set up follow builders".
2. Walk through the conversational setup (frequency / language /
   delivery channel).
3. Verify a digest arrives within minutes via the chosen channel.
4. Run a "central server unreachable" scenario (block the feed URL)
   and verify the failure surfaces.

## Real findings

1. **No LICENSE.** Same as `codebase-to-course`. Pattern in this
   author's skills.
2. **Central pipeline is a single point of failure.** "No API keys"
   sounds like a feature; in dependency-graph terms, every user is
   tightly coupled to Zara's server. If she stops maintaining or her
   server goes offline, every install stops working with no
   documented fallback.
3. **`generate-feed.js` is not a stub.** 38 KB of real logic — the
   project has done the engineering even though the user-facing
   skill is light.

## Verdict implication

5/6 static claims passed; LICENSE missing; molecule cap holds. Score
expected mid-60s — strong static layer, plus ecosystem points (3.7K
stars), minus LICENSE penalty.
