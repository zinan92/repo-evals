# dreammis/social-auto-upload — final verdict (2026-05-05)

## Repo

- **Name:** dreammis/social-auto-upload · **Stars:** 10,660
- **Archetype:** adapter · **Layer:** **molecule** · **Domain:** content
- **Use cases:** content-publishing
- **License:** **missing** (README has a license section but no LICENSE file at repo root)
- **Pushed:** 2026-04-24 · **Visible history:** 1 commit ("ok") — likely force-pushed

## What was evaluated

| Claim | Status | Notes |
|---|---|---|
| 001 7 platform uploaders exist | passed | douyin / xhs+xiaohongshu / bilibili / kuaishou / 视频号 / 百家号 / TikTok |
| 002 CLI + backend non-trivial | passed | sau_cli.py 745 LoC + sau_backend.py 717 LoC |
| 003 per-platform examples (cookie + upload) | passed | 7 cookie + 8 upload scripts under examples/ |
| 004 tests collect from clean clone | **failed_partial** | `from conf import BASE_DIR` fails — needs conf.py setup first |
| 005 docs comprehensive | passed | install / CLI / agent-bootstrap / skill-distribution / update / legacy-web |
| 006 LICENSE | **failed** | no file at root despite 10K+ stars |
| 007 stealth setup real | passed | puppeteer-extra-stealth file + Chrome flags in browser_hook |
| 008 pyproject + uv.lock + Dockerfile | passed | full distribution metadata |
| 009 live upload e2e | untested | needs real account + real video on at least one platform |
| 010 single canonical xiaohongshu uploader | **failed_partial** | xhs_uploader + xiaohongshu_uploader both exist, no deprecation marker |

## Score

```
base                 +40
static_eval          - 4   (5×5 critical/high passed +20; 1 critical failed -10;
                            2 high failed_partial -8; 1 critical untested -2;
                            net = -4 after clamping)
maintainer_evidence  + 5   (recent_active +5; release_pipeline=1, eval_discipline=1
                            don't reach the +5 threshold)
ecosystem            + 6   (10,660 stars → 5K-15K band)
layer_bonus          + 0   (molecule)
penalties            - 5   (no LICENSE, 10K+ tier)
─────────────────────────
total                42  → ⚠️ Risky · ⚠️ Risky tier
```

## Real findings

1. **The popularity-vs-engineering-hygiene gap is the headline.** 10K
   stars proves the framework solves a real problem (auto-uploading
   to 7 Chinese + international platforms is genuinely useful). But
   three engineering gaps cost the score: no LICENSE, tests fail to
   collect from clean clone, two parallel xiaohongshu uploaders
   without a clear migration marker. The framework correctly
   distinguishes "people star this" from "this is production-ready".

2. **No LICENSE is the load-bearing −10 swing.** README has a "📜
   许可证" section but no LICENSE file at the canonical path. With
   10K+ stars this triggers the larger −5 penalty (10K+ tier) plus
   the failed-critical −10. Single-file fix recovers ~+20.

3. **Tests don't collect on a fresh clone.**
   `python3 -m pytest tests/ --collect-only` errors with
   `ModuleNotFoundError: No module named 'conf'` because
   `uploader/__init__.py` imports `from conf import BASE_DIR` and
   `conf.py` has to be hand-created from `conf.example.py` first.
   This is a real CI / contributor barrier. Either move config out
   of import-time, or auto-bootstrap `conf.py` for tests.

4. **Two parallel xiaohongshu uploaders create migration confusion.**
   `uploader/xhs_uploader/` (with `accounts.ini` +
   `xhs_login_qrcode.py`, more elaborate) and
   `uploader/xiaohongshu_uploader/` (slimmer, just `main.py`) both
   exist. Matching duplicate examples too:
   `upload_video_to_xhs.py` + `upload_video_to_xiaohongshu.py`. No
   deprecation marker, no docs explaining which to pick. New users
   pay the "read both modules + their git history" tax.

5. **Single-commit visible history is unusual.** `git log` shows one
   commit ("ok") for a 2.5-year-old 10K-star project. History was
   force-pushed at some point. Doesn't change function but makes
   provenance auditing impossible.

6. **Stealth setup is the real puppeteer-extra-stealth bundle but
   ~16 months stale.** `utils/stealth.min.js` is auto-generated
   2024-06-10 from
   `berstend/puppeteer-extra/extract-stealth-evasions`. That's real,
   but platforms iterate anti-bot frequently — a refresh would help.

7. **README has prominent paid-sponsor blocks.** ClawPower (LLM
   gateway) + WeChat sponsor block right at the top. The OSS code
   is independent of either, but a casual reader can mistake the
   sponsorship section for project features. Disclosure-heavy
   README style, similar to CLIProxyAPI.

## Why the score lands at 42 (⚠️ Risky)

The framework is intentionally strict on engineering hygiene
relative to popularity. 10K stars buys +6 ecosystem (mid-band);
they don't buy a free pass on missing LICENSE or broken-on-clean-
clone tests. This 42 is the honest read for "popular tool with
real defects an adopter has to absorb".

## Path forward

3 single-commit fixes get this to 🛠 Available (74) without
needing a live e2e:

1. Add LICENSE file → ~+20 (62)
2. Fix `from conf import` → ~+6 (68)
3. Pick canonical xhs uploader + deprecate the other → ~+6 (74)

Live e2e (claim-009) on top → 80+ Production-ready.

## Similar repos in our corpus

- `NanmiCoder/MediaCrawler` (75 / 🛠 Available) — direct peer:
  Playwright + 7 Chinese platforms + cookie auth. Difference:
  pulls (scrape) vs pushes (upload). MediaCrawler has cleaner
  engineering hygiene (tests run from clone) and 4.5× more
  validation (48K stars).
- `Usagi-org/ai-goofish-monitor` (69 / 🛠 Available) —
  single-platform Chinese-platform automation; cleaner setup.
- `zinan92/content-downloader` (29 / 🛑) — different direction
  (downloading), currently broken on Douyin signing.

## Recommended

```yaml
status: evaluated
```
