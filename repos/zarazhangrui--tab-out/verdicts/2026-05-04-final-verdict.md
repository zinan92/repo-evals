# tab-out — final verdict (2026-05-04)

## Repo

- **Name:** zarazhangrui/tab-out
- **Branch evaluated:** main@HEAD (manifest 1.0.0)
- **Archetype:** adapter (Chrome tabs API)
- **Layer:** **atom** — single-purpose, no internal multi-skill composition
- **Eval framework:** repo-evals layer model v1 (fe256e5)

## Bucket

**`usable`** — small, focused, MV3-conformant. One real
privacy-claim contradiction (favicons leak the user's open-tab domain
list to Google) prevents `reusable` until either the README is
softened or the favicon source is changed.

## What was evaluated

### Atom level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 MV3 + newtab override | passed | Manifest is real and tight; override target exists |
| 002 minimal permission scope | passed | Only `tabs / activeTab / storage`, no host_permissions |
| 003 no external API calls | passed_with_concerns | No fetch/XHR — but every tab's domain is sent to `https://www.google.com/s2/favicons` (3 sites in app.js); contradicts README's "100% local" claim |
| 004 chrome.storage.local only | passed | 13 storage references in app.js; no localStorage / IndexedDB competing path |
| 005 synthesized sound | passed | AudioContext used; no audio files in bundle |

### Atom level (deferred — live)

| Claim | Status | Required |
|---|---|---|
| 006 e2e in Chrome | untested | Load unpacked, open new tab, verify dashboard renders + sound + confetti + offline favicon fallback |

## Real findings

1. **Privacy headline is overstated.** README says "no external API
   calls" and "100% local your data never leaves your machine".
   Strictly true for **saved-tab data** (chrome.storage.local) but
   false for **favicon rendering** — Google's favicon endpoint is
   contacted with the domain of every open tab, every render. This is
   a documentation issue, not malice. Either:
   - Drop those headlines and replace with "user data stays local;
     favicons are fetched from Google's public favicon service", or
   - Replace the favicon source with a generated colour chip / hashed
     drawable so the headline becomes accurate.

2. **Graceful degradation already exists.** Each `<img>` has
   `onerror="this.style.display='none'"`, so an offline / Google-blocked
   user gets a working extension minus icons. The infrastructure to
   make the favicon source pluggable is essentially in place.

3. **Permission scope is honest and minimal.** No `<all_urls>`, no
   host_permissions, only the 3 documented permissions. This part of
   the security story holds without caveats.

## Why not higher

- Single-evaluator, no live-install evidence on this machine.
- claim-003's contradiction is small but real — promoting past
  `usable` would imply the privacy claim has been audited and is
  trustworthy, which it isn't yet.

## Path to `reusable`

1. Either fix the favicon source or update the README to disclose it.
2. Run a live-install verification (claim-006) and log it.
3. Promote claim-006 to `passed`, claim-003 to either `passed`
   (if README updated) or stay `passed_with_concerns` (favicon
   continues, just disclosed).
4. Re-run verdict_calculator.

## Recommended

```yaml
current_bucket: usable
status: evaluated
```
