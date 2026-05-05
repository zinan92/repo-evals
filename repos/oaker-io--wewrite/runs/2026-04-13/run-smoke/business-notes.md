# Business Notes — wewrite smoke test

## Scenario

First-time evaluation of oaker-io/wewrite as a hybrid-skill for WeChat article generation.
Tested all support-layer features: installation, CLI tools, converter, hotspot fetching,
themes, image providers, personas, quality scripts, eval specs.

## What Happened

**Installation: Clean.** `pip install -r requirements.txt` in fresh venv, 8 deps, exit 0.

**CLI: All 6 commands work.** preview, publish, themes, image-post, gallery, learn-theme
all respond to --help. themes lists 16 themes with descriptions.

**Converter: The star of the show.** `preview test.md -t professional-clean` produces real
WeChat HTML with: inline CSS (no `<style>` in body), link→footnote conversion with
reference list, dark mode data attributes, CJK formatting. This is serious work.

**Hotspots: Live data.** `fetch_hotspots.py --limit 5` returned trends from all 3 sources
(Weibo, Toutiao, Baidu). Zero failed sources. Structured JSON output with normalized scores.

**Themes: 16 with dark mode.** All verified as YAML with colors, darkmode_colors, base_css.

**Image gen: 9 providers in code.** All 9 have full generate() methods with fallback chain.
Cannot test without API keys but code review confirms implementation.

**Personas: 5 with rich parameters.** Detailed YAML configs including calibrated humanness scores.

**Quality scripts: Working.** SEO keywords returns live Baidu/360 data. Humanness scoring
provides multi-tier quantitative analysis. Diagnose script does full health check.

**Unit tests: None.** Zero test files in the entire repo. This is the one real gap.

## Was The Result Usable?

**For the support layer: exceptionally yes.** Every piece of deterministic code works.
The converter quality is notably better than most WeChat formatting tools.

**For the core workflow: unknown.** The 8-step article generation is the actual product,
and it requires a Claude Code session + WeChat API credentials to test.

## Anything Surprising?

1. **Converter quality is remarkably good.** The footnote conversion, inline CSS, and
   dark mode support show deep WeChat platform knowledge. Not generic markdown-to-html.

2. **9 image providers is ambitious.** Most tools support 1-2. The fallback chain is
   well-designed. Jimeng provider even implements HMAC-SHA256 signing.

3. **No unit tests at all** despite 2,232 lines of toolkit code. The eval specs test
   agent behavior but not code correctness. One converter regression could silently
   break all article output.

4. **Humanness scoring is novel.** Multi-tier analysis with specific dimensions
   (sentence variance, vocabulary richness, emotional markers, banned word detection).
   Shows genuine thinking about the AI detection problem.
