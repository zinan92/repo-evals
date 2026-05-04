# ai-goofish-monitor — final verdict (2026-05-04)

## Repo

- **Name:** Usagi-org/ai-goofish-monitor
- **Branch evaluated:** master@HEAD (Docker image
  `ghcr.io/usagi-org/ai-goofish:latest`)
- **Archetype:** api-service (reclassified from default `hybrid-skill`)
- **Layer:** **molecule** — predefined LLM-criteria → scrape →
  LLM-analyze → notify pipeline
- **Eval framework:** repo-evals layer model v1 (f9ed1e9)

## Bucket

**`usable`** — clean static layer, popular and well-engineered. Two
soft concerns (admin-password DX + 8000:8000 binding) are foot-shotgun
risks worth disclosing. Compound molecule rule caps `usable` until
a logged live monitoring run.

## What was evaluated

### Atom + molecule level (static, this run)

| Claim | Status | Notes |
|---|---|---|
| 001 docker-compose | passed | Single `app` service, 9 mounts, port 8000:8000 |
| 002 clean DDD layering | passed | src/{api, core, domain, services, infrastructure} |
| 003 6 notification channels | passed | All 6 README-claimed channels have section headers in env.example |
| 004 multi-stage Dockerfile | passed | 3 FROM stages: node frontend-builder + Python venv builder + lean final |
| 005 Chrome extension MV3 | passed | `Xianyu Login State Extractor` v1.1, scoped to `*.goofish.com` only |
| 006 prompt templates | passed | base_prompt 47 lines + macbook_criteria 46 lines |
| 007 admin password DX | passed_with_concerns | Defaults `admin/admin123` noted but not flagged as risky; combined with default 8000:8000 binding = foot-shotgun on public VPS |

### Molecule level (deferred)

| Claim | Status | Required |
|---|---|---|
| 008 live monitoring e2e | untested | Real XianYu cookie + LLM key + ntfy URL; create AI task; verify Playwright + LLM + notification chain |

## Real findings worth surfacing

1. **Foot-shotgun on public deployment.** `WEB_PASSWORD=admin123` +
   `8000:8000` (binds to all interfaces) means a user spinning this
   up on a VPS gets an internet-reachable admin login with the
   default password. README does say "默认 admin/admin123" but
   doesn't strongly warn. Two simple fixes upstream: bind `127.0.0.1:8000`
   by default, and add a `⚠️ change WEB_PASSWORD before exposing` line.

2. **Companion extension is well-scoped.** Unlike
   `xiaohongshu-skills`' XHS Bridge (which uses `debugger`), this
   one is just `cookies + scripting + storage + tabs + webRequest`
   on `*.goofish.com` only. Lower privilege footprint, narrower
   blast radius.

3. **DDD-style src/ is the real deal.** A lot of "Playwright + AI"
   repos ship as a single 3000-line script. This one has a clean
   `api / core / domain / services / infrastructure` split — easier
   to fork, easier to audit.

4. **OPENAI_BASE_URL defaults to modelscope.cn.** China-friendly
   default, but means user prompts and product images go through a
   3rd-party model gateway out of the box. Worth disclosing in
   `watch_out` (already done).

## Why not higher

`usable` because:

- No live monitoring run. Compound molecule rule requires evidence
  the actual user-value chain (notification fires on a real listing
  match) works.
- The two soft concerns (default password, default port binding)
  meaningfully reduce trust for casual users; promotion past
  `usable` should require either upstream fixes or a documented
  hardening playbook.

## Path to `reusable`

1. Run a live monitoring scenario per the deferred plan.
2. Produce a hardening checklist (change WEB_PASSWORD, change
   OPENAI_BASE_URL if needed, set proxy pool if rate-limited).
3. Run an expired-cookie scenario; verify error visibility.
4. Update claims, re-run verdict_calculator.

## Recommended

```yaml
current_bucket: usable
status: evaluated
```
