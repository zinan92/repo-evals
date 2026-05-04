# tab-out — static-checks run, 2026-05-04

Eval scope: Manifest V3 shape, permission surface, network surface,
storage path, bundle composition. No live install in Chrome.

## Findings

### claim-001: MV3 + newtab override — **passed**

```json
{
  "manifest_version": 3,
  "chrome_url_overrides": { "newtab": "index.html" },
  "background": { "service_worker": "background.js" }
}
```

`extension/index.html`, `extension/app.js`, `extension/background.js`,
`extension/style.css`, and `extension/icons/{icon16.png,icon48.png,icon128.png,icon.svg}`
all exist. Override target is wired and present. Manifest is 612 bytes
of nothing-extra — a tight, honest manifest.

### claim-002: minimal permission scope — **passed**

```json
"permissions": ["tabs", "activeTab", "storage"]
"host_permissions": (absent)
```

No `<all_urls>`, no host permissions at all. The user-facing privilege
list during install will read "read your browsing history" (the `tabs`
permission's user-facing label) and nothing else. This is exactly the
minimum needed for the documented features.

### claim-003: no external API calls — **passed_with_concerns**

`grep -c 'fetch(' app.js` → 0. `grep -c 'XMLHttpRequest' app.js` → 0.
That much matches the README headline.

But `app.js` has 3 sites that build favicon URLs of the form:

```
https://www.google.com/s2/favicons?domain=<DOMAIN>&sz=16
```

And renders them as `<img src=...>`. Every domain in the user's
open-tab list is therefore disclosed to Google's favicon service every
time the new-tab page renders. That's a request to an external server
carrying user data (the domain list) — exactly what "no external API
calls" and "100% local your data never leaves your machine" promise
not to do.

The contradiction is not malicious — favicons need to come from
somewhere — but it is a real DX gap. README would be honest if it
said "your tab/storage data stays in chrome.storage.local; favicons
are fetched from Google's public favicon service".

The `<img onerror="this.style.display='none'">` fallback means an
offline / blocked-Google user will silently lose favicons but
otherwise see a fully working UI — a graceful degraded path already
exists. A privacy-conscious fork could replace the favicon source
with a local drawable / hashed colour chip.

### claim-004: chrome.storage.local — **passed**

`grep -c 'chrome.storage.local' app.js` → 13. `localStorage` and
`IndexedDB` searches are empty — the storage surface is a single API,
honest with the README claim.

### claim-005: synthesized sound, no audio files — **passed**

`grep -c 'AudioContext' app.js` → 1. `extension/icons/` contains only
PNGs + an SVG (no `.mp3` / `.wav` / `.ogg`). Sound is synthesized at
runtime as the README claims; bundle stays small (the whole extension
is ~80 KB minus icons).

## What is still untested (claim-006)

End-to-end install in a real Chrome:

1. Load unpacked from `extension/`.
2. Open new tab — verify the dashboard renders, tabs grouped by
   domain, homepages group at top.
3. Trigger close on a group — verify swoosh sound + confetti.
4. Click a tab title — verify focus jumps to that tab without opening
   a new one.
5. Toggle browser to offline — verify favicon `onerror` makes them
   disappear silently and the rest of the UI keeps working.
6. Log under `runs/<date>/run-live-extension/business-notes.md`.

## Verdict implication

Static layer is clean for everything except the favicon-leak
contradiction. The leak is small and there's a clear graceful-fallback
path, so the right call is `usable` with the privacy claim downgraded
in `watch_out`, not `unusable`.

Recommended bucket: **usable**.
