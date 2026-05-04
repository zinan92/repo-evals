# MediaCrawler — static-checks run, 2026-05-04

Eval scope: source layout, CLI surface, install dependencies, encryption
helpers. No live browser run. Per-platform end-to-end flows deferred to
molecule-level scenario runs.

## Findings

### claim-001: platform coverage — **passed**

`main.py::CrawlerFactory.CRAWLERS` lists 7 entries (xhs / dy / ks / bili
/ wb / tieba / zhihu) and `media_platform/` has exactly the 7 matching
sub-packages (xhs, douyin, kuaishou, bilibili, weibo, tieba, zhihu). No
ghost entries, no orphan modules.

### claim-002: CLI contract — **passed (code richer than docs)**

`cmd_arg/arg.py` declares:

| Enum | Values |
|---|---|
| `PlatformEnum` | xhs / dy / ks / bili / wb / tieba / zhihu |
| `LoginTypeEnum` | qrcode / phone / cookie |
| `CrawlerTypeEnum` | search / detail / **creator** |
| `SaveDataOptionEnum` | csv / db / json / jsonl / sqlite / **mongodb** / excel / **postgres** |
| `InitDbOptionEnum` | sqlite / mysql / postgres |

The English README mentions search/detail and 6 storage backends; the
code ships **creator** as a third crawl type and **MongoDB +
PostgreSQL** as additional backends. README understates capability —
no false promise. (Worth a docs PR upstream so users know about
creator-mode and mongodb/postgres.)

### claim-003: install deps — **passed**

`.python-version` says `3.11`, README and CI agree. `requirements.txt`
carries:

```
playwright==1.45.0     ← matches README
aiomysql==0.2.0        ← MySQL async
asyncmy>=0.2.10        ← MySQL async (alt)
aiosqlite==0.21.0      ← SQLite async
motor>=3.3.0           ← MongoDB async
sqlalchemy>=2.0.43     ← ORM (used for postgres + mysql + sqlite)
openpyxl>=3.1.2        ← Excel writer
xhshow>=0.1.9          ← xhs signing helper (third-party)
```

Every storage backend the CLI exposes has a real client in deps. No
"download this driver yourself" gaps.

### claim-004: "no encryption reversal needed" — **passed with concerns**

The README's headline promise is real *at the user surface*: there are
no `--a-bogus`, `--x-s-common`, or signing-token flags. But framing
glosses over how much platform-specific code ships:

| Platform | Signing strategy in repo |
|---|---|
| Douyin | `libs/douyin.js` (vendored JS, executed via pyexecjs) |
| Zhihu | `libs/zhihu.js` (vendored JS) |
| Xhs | `xhshow>=0.1.9` (separate maintained package; signing lives in pip dep) |
| All | `libs/stealth.min.js` (Playwright stealth plugin, evades bot detection) |
| Kuaishou / Bilibili / Weibo / Tieba | inside `media_platform/<x>/client.py` (no top-level helper) |

So "no need to reverse encryption" should be read as "we already did
the reverse-engineering for you, in three different places (vendored
JS files, a separate pip package, and per-platform client modules)".
That's a real value prop for the end user — but it also means
**every platform that bumps its signing scheme breaks until one of
those three places is updated**.

`pyexecjs==1.5.1` in requirements confirms vendored JS gets executed
via Node-bridge at runtime, which is part of why Node.js is a hard
prerequisite.

## What is still untested

| Claim | Why static eval cannot confirm | What the operator needs to do |
|---|---|---|
| 005 e2e per platform | Needs real account + Playwright browser + un-broken platform on eval day | Run `uv run main.py --platform xhs --lt qrcode --type search`, scan QR, confirm CSV/DB output and row count |
| 006 failure-mode UX | Needs induced failures (no login, empty keyword, IP block) | Run search without login, with nonsense keyword, behind a known-blocked proxy; verify error visibility and exit codes |
| 007 adapter isolation | Needs repo clone + import probe | `git clone`, intentionally break `media_platform/xhs/__init__.py`, `python -c 'from media_platform.bilibili import BilibiliCrawler'` should still succeed |

## Risk note (anti-bot fragility)

Even if a future molecule-level run confirms claim-005 on every
platform, that is a **snapshot of the day**. Anti-bot teams at xhs / dy
/ ks ship breaking changes routinely. A `passed` claim-005 should
include the date and the commit hash of MediaCrawler tested, and not
imply long-term stability.

## Verdict implication

Static layer is clean. Claim-004 is `passed_with_concerns` because the
DX framing oversells the simplicity. Claims 005–007 are the real
trust-determining checks and have not been run.

Recommended bucket: `usable` — credible enough to install and try, not
enough evidence to recommend for repeated use until at least one
platform has a logged molecule-level run with date + commit + row
count.
