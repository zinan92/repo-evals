# RedBox — static-checks run, 2026-05-04

Eval scope: release assets, browser-extension manifest, desktop
package.json. No live install yet. Compound flows deferred to user
scenarios.

## Findings

### claim-001: distribution — **passed**

All 7 release assets for v1.11.0 resolve (HTTP 302 → S3) and report
real sizes:

| Asset | Size |
|---|---|
| RedBox_1.11.0_aarch64.dmg | 21.9 MB |
| RedBox_1.11.0_amd64.deb | 24.4 MB |
| RedBox_1.11.0_arm64-setup.exe | 14.2 MB |
| RedBox_1.11.0_x64-setup.exe | 15.6 MB |
| RedBox_1.11.0_x64.dmg | 23.4 MB |
| RedBox_1.11.0_x86-setup.exe | 14.8 MB |
| RedBox_Browser_Extension_1.9.7.zip | 0.29 MB |

The Electron app installers are notably small (14–24 MB vs the typical
80–150 MB for an Electron app). The build script
(`prepare:private-runtime`, `prepare:plugin-runtime`,
`prepare:ffmpeg`) suggests heavy assets are downloaded post-install,
which would explain the small installer footprint but means the
"binary downloads and runs without further network activity" claim
needs explicit verification in claim-004.

### claim-002: capture coverage — **passed_with_concerns**

The browser-extension manifest description (Chinese) lists:
小红书 / 抖音 / Bilibili / 快手 / TikTok / Reddit / X / Instagram /
YouTube. host_permissions match all of them **except YouTube**:

```
$ grep -i youtube logs/host-permissions.txt
(no match — exit 1)
```

So if a user tries to capture from `youtube.com`, the extension's
content scripts will not be injected and capture will likely fail.
This is a real claim/code mismatch, not a documentation typo:

- The product is shipped as v1.9.7 of the extension (matches release).
- The README in English does not list YouTube; the manifest's own
  description does.

Recommendation: either add `*.youtube.com` host_permissions or remove
YouTube from the manifest description.

### claim-003: ai providers — **passed**

`desktop/package.json` carries:

```
@ai-sdk/anthropic       ^3.0.18
@ai-sdk/openai          ^3.0.14
@ai-sdk/openai-compatible ^2.0.16   ← supports custom endpoints
@google/genai           ^1.45.0
ai                      ^6.0.45
openai                  ^6.26.0
```

That covers Anthropic, OpenAI, Google, plus an explicit
`openai-compatible` SDK so users who want to point at e.g. their own
proxy or a self-hosted vLLM endpoint can. Electron 39.6.0. README's
"endpoint / API key / model" promise is structurally credible.

## Side note: version mismatch (non-blocking)

`desktop/package.json` declares `version: 1.9.0` while the release tag
is `v1.11.0`. The browser-extension manifest is `1.9.7` and matches
the asset filename. The desktop-package version is not user-visible
during install, so this is cosmetic — but a release pipeline that
forgets to bump `package.json` is a smell to keep an eye on.

## What is still untested

| Claim | Why static eval cannot confirm | What the user needs to do |
|---|---|---|
| 004 end-to-end creation flow | Needs install + provider key + content capture + editor + image gen | Install DMG, configure key, run a real article through the workspace |
| 005 RedClaw autonomy | Needs live LLM-driven RedClaw session | Run a multi-step task through the RedClaw console, log call graph |
| 006 background scheduling | Needs a real scheduled task that survives window-close | Schedule a task 5 min out, close window, verify execution |
| 007 user-friendly failure modes | Needs deliberately broken inputs (bad key, dead model, broken DOM) | Misconfigure each layer in turn, screenshot the error UI |

These are compound-layer scenarios — see the per-repo dashboard page
for runnable templates.

## Verdict implication

Static layer is clean except for the YouTube host_permission gap
(passed_with_concerns) and a cosmetic version mismatch. Per the
compound-layer ceiling rule, the repo cannot exceed `usable` until at
least one logged compound scenario passes, and cannot exceed
`reusable` until at least three. Recommended initial bucket: `usable`.
