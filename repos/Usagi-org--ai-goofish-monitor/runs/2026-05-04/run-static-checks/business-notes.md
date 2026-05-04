# ai-goofish-monitor — static-checks run, 2026-05-04

Eval scope: docker-compose stack, source layering, notification
channels, multi-stage Dockerfile, companion Chrome extension, AI
prompt templates, and admin-password disclosure. No live install /
e2e run.

## Findings

### claim-001: docker-compose minimal — **passed**

Single `app` service. Image `ghcr.io/usagi-org/ai-goofish:latest`,
`pull_policy: always`, port 8000:8000, init: true. 9 volume mounts
including SQLite DB (`./data:/app/data`), login state
(`./state:/app/state`), prompts, logs, images, and legacy
`config.json` + `jsonl/` + `price_history/`. README's "git clone +
docker compose up" path is the actual install path — no manual
manifest editing required to start.

### claim-002: clean DDD layering — **passed**

Source structure under `src/`:

```
api / core / domain / services / infrastructure
```

Verified 4/5 directories return HTTP 200 on raw `/__init__.py` fetch
or `gh api contents`; `src/core` returned 403 (likely GitHub rate
limit during this run, but it's listed in the directory listing). A
proper DDD-style separation, not a shoehorned monolith.

### claim-003: 6 notification channels — **passed**

`.env.example` has explicit section headers for all 6 README-claimed
channels:

```
# --- ntfy (推荐) ---
# --- Bark (iOS 推荐) ---
# --- 企业微信机器人 ---
# --- Telegram 机器人 ---
# --- Gotify ---
# --- 通用 Webhook ---
```

Plus 3 supporting sections (failure protection, log cleanup, proxy
pool). The grep counts on raw env-var prefixes underreported because
each channel uses a unique prefix (e.g., `WX_BOT_KEY=`,
`TG_BOT_TOKEN=`); the section headers are the canonical structural
proof and they all match.

### claim-004: multi-stage Dockerfile — **passed**

3 `FROM` stages:

1. `node:22-alpine AS frontend-builder` — Vue UI build
2. `python:3.11-slim-bookworm AS builder` — Python venv build
3. `python:3.11-slim-bookworm` — final lean image

This is the right pattern: final image inherits the venv and
prebuilt frontend, no node/build-essential left over.

### claim-005: companion Chrome extension — **passed**

`chrome-extension/manifest.json` is MV3:

```json
{
  "manifest_version": 3,
  "name": "Xianyu Login State Extractor",
  "version": "1.1",
  "permissions": ["activeTab", "cookies", "scripting", "storage", "tabs", "webRequest"],
  "host_permissions": ["*://*.goofish.com/*"]
}
```

XianYu's English domain is `goofish.com` — host_permissions are
appropriately scoped (no `<all_urls>`, no fanout to other sites).
Does NOT include `debugger` (unlike xiaohongshu-skills' XHS Bridge),
so the privilege footprint is meaningfully smaller. README references
the Chrome Web Store listing; even if the listing gets removed, the
extension can be loaded unpacked from the repo.

### claim-006: prompt templates substantive — **passed**

```
prompts/base_prompt.txt       → 47 lines
prompts/macbook_criteria.txt  → 46 lines
```

Both are real multi-line templates, not 1-line stubs. README's "AI
驱动" promise is structurally credible.

### claim-007: admin password defaults — **passed_with_concerns**

`.env.example` does note `WEB_USERNAME=admin` and
`WEB_PASSWORD=admin123` as the defaults with `(默认 admin / admin123)`
inline. But there's no explicit "CHANGE BEFORE EXPOSING TO THE
INTERNET" warning. README's table also lists the defaults but doesn't
flag them as risky. Combined with `8000:8000` (binds to all
interfaces by default in docker-compose), this is a real
foot-shotgun: a user starting the stack on a public VPS gets a
reachable admin login with the default password.

A simple fix: bind to `127.0.0.1:8000` by default, add a
"⚠️ change WEB_PASSWORD before exposing port 8000" line in README.

## What is still untested (claim-008)

End-to-end monitoring scenario:

1. `docker compose up`, fill `.env` with OPENAI_API_KEY, OPENAI_BASE_URL,
   ntfy.sh URL.
2. Use the Chrome extension to export an XHS login cookie, paste into
   the Web UI account manager.
3. Create an "AI 判断" task with a natural-language criterion
   ("MacBook M2 13", under 6000 RMB, package included").
4. Run the task, observe Playwright fetching results, LLM scoring,
   ntfy notification firing on a hit.
5. Run an "expired login" scenario: invalidate the cookie, verify the
   error path is visible (UI + log) and doesn't silently produce 0
   matches.
6. Log under `runs/<date>/run-live-monitor/business-notes.md`.

## Verdict implication

Static layer is strong — clean DDD layout, multi-stage image, real
prompt content, well-scoped companion extension. Two soft concerns:
admin-password DX, and the usual XHS anti-bot risk (covered in
`watch_out`). Per the molecule rule, `usable` is the ceiling without
a logged live run.

Recommended bucket: **usable**.
