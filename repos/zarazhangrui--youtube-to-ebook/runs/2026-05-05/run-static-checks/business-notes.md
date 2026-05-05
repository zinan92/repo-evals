# youtube-to-ebook — static-checks run, 2026-05-05

## Findings

### claim-001 ~ 005: pipeline + dashboard + cron all real

| Claim | Status | Note |
|---|---|---|
| 001 5-stage pipeline | passed | get_videos / get_transcripts / write_articles / send_email / video_tracker — 90–400 lines each |
| 002 SKILL.md | passed | 171 lines with frontmatter |
| 003 requirements | passed | All 5 README deps present |
| 004 dashboard.py Streamlit | passed | 890 lines |
| 005 LaunchAgent plists | passed | Valid plist format with Label + ProgramArguments |
| 006 LICENSE | **failed** | HTTP 404 |
| 007 live e2e | untested | needs YouTube + Anthropic keys + 1 channel |

### Real findings

1. **No LICENSE.** Same pattern as `codebase-to-course` and
   `follow-builders` — all of Zara's skills missing this. Three-time
   pattern is worth surfacing as a maintainer-level habit.

2. **README has a templating leak.** The git-clone snippet still
   reads `git clone https://github.com/YOUR_USERNAME/youtube-to-ebook.git`
   — should be `zarazhangrui`. New users following the README copy-paste
   will get a 404. Polish gap, not a bug.

3. **3+ months stale at eval time.** Last push 2026-01-28. YouTube's
   transcript API has historically broken under platform changes;
   without recent maintenance there's a real chance the pipeline is
   already broken on YouTube's current frontend.

4. **dashboard.py is 890 lines** — real Streamlit app, not a stub.
   This is unusual for a "side project skill" — implies serious
   investment.

### Verdict implication

Strong static layer, with one real defect (LICENSE) and one polish
gap (README placeholder). Recently-active=false (last push 105 days
ago) costs +3 maintainer points. Score expected mid-50s.
