# Business Notes — md2wechat-skill smoke test

## Scenario

First-time evaluation of geekjourneyx/md2wechat-skill as a hybrid-skill Go CLI for
Markdown→WeChat conversion. Tested: build, all discovery commands, inspect, preview,
convert, config, humanize, write, Go test suite, SKILL.md quality.

## What Happened

**Build: Clean.** `go build ./cmd/md2wechat/` exit 0. Required Go 1.26.1 toolchain
download but then built without issues.

**Discovery: Exemplary.** All 5 discovery commands return valid JSON with consistent
envelope format (success, code, message, schema_version, status, data). This is the
best agent-facing API design I've seen — agents don't need to parse unstructured text.
capabilities --json shows commands, convert options, prompt archetypes.

**Inspect: Excellent.** `inspect test.md` provides metadata resolution, duplicate H1
detection, image count, readiness checks (convert_ready, upload_ready, draft_ready),
and specific fix suggestions. This command alone is worth the install.

**Core conversion: Blocked by API.** `convert test.md` returns 401 — requires
md2wechat_api_key from md2wechat.cn. Error handling is exemplary: structured JSON
error with clear message, not a crash or stack trace.

**Preview: Degraded but functional.** `preview test.md` exit 0, writes HTML file.
Annotates output as "degraded" fidelity without API. Still produces a viewable file.

**Config: Solid.** Both show and validate work. Secrets are masked in output.

**Tests: Outstanding.** 228/228 pass, 0 failures, 36 test files, 14 packages covered.
This is far above average for any repo, let alone a skill.

**Write: Early.** `--list` shows only Dan Koe as a style. The feature works but
the catalog is minimal.

**Themes: Discrepancy.** CLI shows 15 entries. api.yaml has 38. README says "38+".
Users see 15.

## Was The Result Usable?

**For everything except conversion: yes.** The inspect → preview → config workflow
is genuinely useful even without API access. Discovery commands are best-in-class.

**For conversion: requires API key.** The core feature is gated behind md2wechat.cn
credentials. This is a deliberate architectural choice (SaaS model), not a bug.

## Anything Surprising?

1. **228 passing tests is exceptional.** Most skill repos have zero tests.
   This has 36 test files across 14 packages. Production-grade test discipline.

2. **Discovery-first design is the right pattern.** Instead of hard-coding
   capabilities in SKILL.md, agents query `capabilities --json` for the source
   of truth. This means the skill doesn't go stale when features are added.

3. **Graceful degradation is well-implemented.** Preview works without API (degraded
   note), inspect works fully offline, config validate catches issues early.
   Most tools just crash when credentials are missing.

4. **Theme count inflation is a real issue.** 38+ in README, 15 in CLI. This is
   the kind of discrepancy that erodes trust. Either surface 38 themes or
   update the README to say 15.

5. **SKILL-RULE.md is meta-useful.** A guide for writing good SKILL.md files,
   not just for this repo. Shows thought leadership in the skill ecosystem.
