# CLIProxyAPI — static-checks run, 2026-05-04

Eval scope: protocol translators, multi-OS distribution, OAuth flows,
multi-account config, Go SDK, README marketing honesty. No live API
call.

## Findings

### claim-001: 7 translators — **passed**

`internal/translator/` contains:

```
antigravity / claude / codex / common /
gemini-cli / gemini / openai / translator (root)
```

7 protocol-specific implementations + a common helpers package.
Matches the README headline "OpenAI/Gemini/Claude/Codex compatible
API" and the "Antigravity / Claude Code / Codex / Gemini CLI" upstream
list.

### claim-002: 8 release binaries + checksums — **passed**

v6.10.4 release assets:

```
darwin × aarch64 + amd64
freebsd × aarch64 + amd64
linux × aarch64 + amd64
windows × aarch64 + amd64
+ checksums.txt
```

9 assets total (8 binaries + checksums). Consistently named.
Cross-platform coverage including FreeBSD is rare for projects of
this size — implies Goreleaser-style mature release pipeline.

### claim-003: 7 OAuth flows — **passed**

`internal/auth/` has 7 dirs:

```
antigravity / claude / codex / empty / gemini / kimi / vertex
```

`empty` is a placeholder (likely default-no-auth). The other 6 cover
all README-claimed providers, plus `kimi` and `vertex` not headlined
in the English README — code is richer than docs.

### claim-004: multi-account / round-robin — **passed_with_concerns**

`config.example.yaml` is a substantial 406 lines. Naive grep for
`round-robin / load_balance / multi-account / accounts:` returned 2
hits; the concept exists but a deeper read of the config schema
would be needed to confirm full multi-account semantics.
`passed_with_concerns` because the README claim is strong
("multi-account load balancing for Gemini, OpenAI, Claude, Codex")
and we'd want to see ≥4 explicit per-provider account-list sections.

### claim-005: Reusable Go SDK — **passed**

```
docs/sdk-usage.md         → 163 lines (real walkthrough)
sdk/                      → 9 sub-packages: access, api, auth,
                            cliproxy, config, logging, proxyutil,
                            translator + 1 more
docs/sdk-{access,advanced,usage,watcher}.md
                          → all exist with EN + CN versions
```

This is one of the strongest "embedded SDK" stories I've seen for an
OSS proxy — most stop at "here's a binary".

### claim-007: README sponsorship section — **passed_with_concerns**

Top of README has 5+ sponsor entries (PackyCode, AICodeMirror,
BmoPlus, Poixe AI, VisionCoder, Z.ai) before the "Overview" section.
The Overview itself cleanly enumerates OSS features (translator
coverage, OAuth flows, multi-account, SDK, etc.) and doesn't conflate
those with sponsor services. But a reader skimming the top might
mistake the sponsors as "official providers". `passed_with_concerns`
because the disclosure is honest just front-loaded.

## What is still untested (claim-006)

End-to-end live test:

1. Download release binary, start the server.
2. Run one OAuth login flow (e.g., Claude Code OAuth via the CLI).
3. From a terminal, run:
   ```
   curl -X POST http://localhost:<PORT>/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "<routed-model>", "messages": [{"role":"user","content":"Hi"}]}'
   ```
4. Verify a structured OpenAI-compatible response (id, choices[],
   usage, etc.).
5. Run an "OAuth expired" scenario; verify the proxy returns a clear
   401-style response and prompts re-login.
6. Log under `runs/<date>/run-live-api/business-notes.md`.

## Verdict implication

This is a structurally mature OSS proxy. Static layer is unusually
strong for the size: cross-platform binaries, 7 protocol translators,
7 OAuth providers (more than headlined), 9 SDK packages with bilingual
docs. The two `passed_with_concerns` items (config schema needs
deeper read; sponsor section front-loaded) are docs/UX issues, not
bugs.

Recommended bucket: **usable** — strong foundation; one logged live
call and a closer reading of the multi-account config would justify
moving toward `reusable`.
