# CLIProxyAPI — final verdict (2026-05-04)

## Repo

- **Name:** router-for-me/CLIProxyAPI
- **Branch evaluated:** main@HEAD (release v6.10.4)
- **Archetype:** api-service
- **Layer:** **molecule** — config-driven routing across predefined
  translators
- **Eval framework:** repo-evals layer model v1 (f9ed1e9)

## Bucket

**`usable`** — structurally mature OSS proxy, strong static
evidence on all 6 audit dimensions. Molecule rule caps `usable`
without a logged live API round-trip.

## What was evaluated

### Atom + molecule level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 7 translators | passed | antigravity / claude / codex / common / gemini-cli / gemini / openai under internal/translator/ |
| 002 8 release binaries | passed | darwin/freebsd/linux/windows × aarch64+amd64 + checksums.txt |
| 003 7 OAuth flows | passed | internal/auth/: 6 real providers + `empty` placeholder; includes Kimi + Vertex not headlined in EN README |
| 004 multi-account config | passed_with_concerns | 406-line config.example.yaml; concept exists; deeper schema read recommended |
| 005 Reusable Go SDK | passed | docs/sdk-usage.md 163 lines + 9 sdk/ packages + 4 docs in EN+CN |
| 007 sponsor disclosure | passed_with_concerns | 5+ sponsors front-load README; Overview section cleanly separates OSS features from sponsor offerings |

### Molecule level (deferred)

| Claim | Status | Required |
|---|---|---|
| 006 live OpenAI-compatible call | untested | Start binary, do one OAuth login, curl `/v1/chat/completions`, log response |

## Real findings worth surfacing

1. **Cross-platform release pipeline is mature.** 8 OS/arch
   combinations + checksums shipped consistently. FreeBSD coverage
   is unusual and signals goreleaser-style automation.

2. **Code is richer than docs.** Two OAuth providers (Kimi, Vertex)
   in `internal/auth/` not headlined in the English README; the
   community probably knows but a search would miss them.

3. **SDK story is unusually strong.** Most OSS proxies stop at "run
   the binary". This one ships a 9-package Go SDK with 4 doc files
   in EN+CN — implies the project expects to be embedded into other
   Go services, not just run standalone.

4. **README sponsorship section is heavy.** ~50 lines of sponsor
   tables before the "Overview" — honest disclosure but front-loaded.
   A casual reader skimming the top might mistake the sponsors for
   official providers; the Overview cleanly separates the OSS feature
   set from sponsor offerings, but a reader who stops at the top
   misses that.

## Why not higher

`usable` is the right ceiling because:

- No live API round-trip logged on this evaluator's machine. (Wendy
  already runs CLIProxyAPI per memory record, but the eval is
  independent static-only.)
- claim-004 needs a deeper config-schema audit to confirm the
  multi-account / round-robin claim is fully wired (not just keyword-
  level present).

## Path to `reusable`

1. Start binary, perform one OAuth login (claude / gemini / codex —
   pick one).
2. Send a `/v1/chat/completions` request, verify the structured
   response.
3. Run an OAuth-expired scenario; verify clear error.
4. Read config.example.yaml end-to-end and confirm multi-account
   list semantics.
5. Update claim-006 → `passed`, claim-004 → `passed` if the schema
   is fully wired. Re-run verdict_calculator.

## Recommended

```yaml
current_bucket: usable
status: evaluated
```
