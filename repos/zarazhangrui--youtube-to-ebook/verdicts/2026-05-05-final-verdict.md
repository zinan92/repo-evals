# youtube-to-ebook — final verdict (2026-05-05)

## Repo

- **Name:** zarazhangrui/youtube-to-ebook · **Stars:** 440
- **Archetype:** hybrid-skill · **Layer:** molecule
- **Branch:** main@HEAD · **Last push:** 2026-01-28 (3+ months stale)

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 5-stage pipeline | passed | Real .py files for each stage |
| 002 SKILL.md | passed | 171 lines with frontmatter |
| 003 requirements coverage | passed | All 5 README-claimed deps |
| 004 Streamlit dashboard | passed | 890 lines (substantial) |
| 005 LaunchAgent plists | passed | Valid format with Label + ProgramArguments |
| 006 LICENSE | **failed** | HTTP 404 |
| 007 live e2e | untested | needs YouTube + Anthropic keys + 1 channel |

## Real findings

1. **README templating leak.** Git-clone command reads
   `git clone https://github.com/YOUR_USERNAME/youtube-to-ebook.git`
   — never edited to `zarazhangrui`. Copy-paste users will get a
   404 on the clone step.

2. **No LICENSE** — third Zara repo in this batch missing one. Pattern.

3. **3+ months stale.** Last push 2026-01-28. YouTube's transcript
   API breaks under YouTube frontend changes; without recent
   maintenance there's real risk the pipeline is already broken.
   Costs `recently_active=false` → no maintainer-active bonus.

4. **Mac-only automation.** LaunchAgent plists are Mac-specific.
   README's "Automation" section doesn't mention Linux / cron, even
   though many users would want it.

## Path forward

1. Fix README's `YOUR_USERNAME` placeholder → `zarazhangrui`.
2. Add LICENSE.
3. Push a fresh commit (even just a doc fix) to mark recently-active.
4. Run a real YouTube → EPUB pipeline; log under run-live-e2e/.
5. Add a Linux cron snippet for non-Mac users.
