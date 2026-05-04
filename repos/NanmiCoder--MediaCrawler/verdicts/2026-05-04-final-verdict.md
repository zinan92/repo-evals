# MediaCrawler — final verdict (2026-05-04)

## Repo

- **Name:** NanmiCoder/MediaCrawler
- **Stars:** 48,800+
- **Archetype:** adapter
- **Layer:** **molecule** — predefined per-platform pipelines
  (login → search/detail/creator → store), no LLM-driven routing
- **Eval framework version:** repo-evals layer model v1 (41d9565)

## Bucket

**`usable`** — static layer is clean, but the user-facing value
(actually scraping live data) is molecule-level and not yet logged on
this evaluator's machine.

The repo is a credible install-and-try candidate. It is not yet
`reusable` because:

1. No molecule-level run on any of the 7 platforms has been logged
   here, and platform anti-bot moves fast enough that "the code is
   structurally complete" does not transfer to "it works today".
2. claim-004 ("no encryption reversal needed") is `passed_with_concerns`
   — the user surface is clean, but the framing understates how much
   per-platform plumbing is happening (3 different signing strategies
   live in the repo, all of them break when platforms change).

## What was evaluated

### Atom + molecule level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 platform coverage | passed | `CrawlerFactory.CRAWLERS` has 7 entries, `media_platform/` has 7 dirs, perfect 1:1 with README |
| 002 CLI contract | passed | Code is richer than the English README — `creator` crawl type and `mongodb` / `postgres` storage backends are not surfaced in docs |
| 003 install deps | passed | Python 3.11, Playwright 1.45.0, every storage backend has a real client in `requirements.txt` |
| 004 no encryption reversal | passed_with_concerns | User surface clean, but signing lives in 3 places (`libs/*.js` + `xhshow` pip dep + per-platform `client.py`) — framing oversells simplicity |

### Molecule level (deferred — needs live run)

| Claim | Status | What it takes to clear |
|---|---|---|
| 005 e2e per platform | untested | Real account + Playwright browser + un-broken platform on eval day; record date + commit + row count |
| 006 failure-mode UX | untested | Induce missing-login / empty-keyword / IP-block; verify error visibility and exit codes |
| 007 adapter isolation | untested | Clone repo, break one adapter's `__init__.py`, verify the other six still import |

## Real findings worth surfacing

1. **DX framing oversells the encryption story.** README says "no need
   to reverse complex encryption algorithms"; the repo ships
   `libs/douyin.js`, `libs/zhihu.js`, `libs/stealth.min.js`, depends on
   the third-party `xhshow` package, and keeps additional signing logic
   inside per-platform `client.py` files. The user does not have to do
   the reversing — but the *project* is doing it on three fronts at
   once, and any platform that bumps signing breaks until one of those
   three places is updated.

2. **Hidden capabilities under-documented.** Code exposes a `creator`
   crawl type and `mongodb` + `postgres` storage backends that the
   English README never mentions. Real capability, lost feature
   visibility.

3. **License is non-commercial custom (NOASSERTION).** README disclaimer
   is explicit but the GitHub-detected license is "Other" rather than
   a recognised SPDX ID, which means downstream tooling (Dependabot,
   SBOM scanners, package managers) treats it as unknown — read the
   LICENSE file before any non-research use.

## Why not higher

`usable` is the right ceiling now because:

- No molecule-level live run has been done. Even one passing run on
  one platform — with date + MediaCrawler commit + row count + storage
  evidence — would justify moving claim-005 to `passed` for that
  platform, not the others.
- Even with a clean static layer, anti-bot fragility means
  "recommendable" requires the same evidence on multiple platforms
  *and* multiple evaluation dates separated by weeks, not one heroic
  green snapshot.

## Path to `reusable`

1. Pick the lowest-risk platform (xhs / bili / weibo are usually the
   most stable) and run `uv run main.py --platform <p> --lt qrcode
   --type search --keywords <real_term>`. Log it under
   `runs/<date>/run-<p>-search/business-notes.md`.
2. Repeat for at least one more platform.
3. Induce two failures (no-login, fake keyword) and capture the error
   output under `runs/<date>/run-failures/`.
4. Re-run the verdict calculator.

## Recommended bucket

```yaml
current_bucket: usable
status: evaluated
```
