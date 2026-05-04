# Awesome-finance-skills — final verdict (2026-05-04)

## Repo

- **Name:** RKiding/Awesome-finance-skills
- **Branch evaluated:** main@HEAD
- **Archetype:** hybrid-skill (reclassified from default `prompt-skill`)
- **Layer:** **molecule** at the repo level — catalog of 10 individually-
  hybrid skills
- **Eval framework:** repo-evals layer model v1 (f9ed1e9)

## Bucket

**`usable`** — clean static layer; all 8 README-listed skills exist
and are non-trivial; install paths cover three agent frameworks. The
multi-skill agentic value (the catalog's promise) is unverified
without a real session.

## What was evaluated

### Atom + molecule level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 8 skills present | passed | All 8 alphaear-* SKILL.md files (HTTP 200) |
| 002 hybrid shape | passed | Sampled alphaear-news has SKILL.md + 4 scripts + references + tests |
| 003 catalog ≥ docs | passed | 10 skill dirs, 8 listed in README + 2 extras (deepear-lite, skill-creator) |
| 004 multi-agent install paths | passed | README Integration Guide covers Antigravity / OpenCode / OpenClaw with workspace + global paths |
| 005 SKILL.md frontmatter | passed | Sampled SKILL.md has standard `name + description` with "Use when..." trigger phrase |

### Molecule level (deferred)

| Claim | Status | Required |
|---|---|---|
| 006 multi-skill chain agent run | untested | Real Claude Code / OpenCode / OpenClaw session running "analyze gold crash impact on A-shares" through news → visualizer → reporter chain |

## Real findings worth surfacing

1. **Each skill is genuinely hybrid.** Not a markdown-only catalog —
   alphaear-news ships 4 Python helpers (content_extractor,
   database_manager, news_tools, plus __init__). README's "use
   `scripts/news_tools.py` via NewsNowTools" claim has real code
   behind it.

2. **Catalog under-promises.** README headlines 8 skills; the
   directory has 10. Extra: `alphaear-deepear-lite` (mentioned in
   README's "New" badge) and `skill-creator` (a 371-line utility for
   authoring more skills). User won't be misled, but the table could
   include them for discoverability.

3. **Frontmatter is rigorous.** Sampled SKILL.md ends its
   description with a clear "Use when..." trigger phrase — that's
   the discriminator that lets LLM auto-discovery pick the right
   skill out of a packed registry. Suggests intentional skill-loader
   compatibility.

4. **3-framework install paths are concrete.** Workspace + global
   path pairs for Antigravity / OpenCode / OpenClaw — concrete enough
   that a new user can copy-paste-edit without reading source. Few
   skill catalogs in this space provide this.

## Why not higher

`usable` because:

- No live multi-skill chain logged. The catalog's "Wall Street
  analyst" promise is the joint behavior of multiple skills cooperating;
  static verification can show each skill exists, not that they
  cooperate well.
- Each skill's analytical accuracy (sentiment, prediction, logic
  chain quality) is independent and unverified. A `reusable` bucket
  would imply both the chain runs and the outputs are useful.

## Path to `reusable`

1. Install full catalog into Claude Code or OpenCode.
2. Ask a multi-skill question (the README example: "Analyze how the
   gold crash affects A-shares").
3. Capture: which skills got called, in what order, with what inputs.
4. Run a "data source down" failure scenario (e.g., Polymarket
   unreachable) and verify error visibility.
5. Update claim-006 to `passed` if the chain produces a useful
   artefact (text + draw.io XML transmission diagram).

## Recommended

```yaml
current_bucket: usable
status: evaluated
```
