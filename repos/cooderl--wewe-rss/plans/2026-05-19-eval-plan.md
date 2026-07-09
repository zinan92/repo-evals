# Eval Plan — api-service

This is a starter plan for a repo exposing an HTTP API.

## What This Repo Claims

- Endpoint 1:
- Endpoint 2:
- Endpoint 3:
- Auth model:
- Error classes:
- Rate limits:

## What We Will Validate

- Every documented endpoint responds (not 404)
- Response shapes match the documented schema
- Protected endpoints reject unauthenticated requests with the documented code
- Every documented error class is reachable with a crafted request
- Rate limits surface the documented code, not 500 or silent drop
- Repeatability: same input, two calls, compare response body

## Real Inputs We Will Use

- Input A:
- Input B:

Prefer fixtures from `fixtures/registry.yaml` with archetype filter
set to `api-service`.

## How Many Times We Will Test

- Happy path per endpoint: at least once
- Auth rejection: at least once per protected endpoint
- Error codes: at least once per documented class
- Rate limit: at least one triggered burst
- Repeatability: 2 calls per endpoint

## What Counts As Passing

- Every endpoint returns the documented status + schema
- Auth rejection returns the documented code, not 200 or 500
- Every error class is reachable with the documented status
- Rate limits produce the documented code with Retry-After if documented
- Repeated calls return identical bodies (modulo known volatile fields)

## If Everything Passes, What We Can Trust

- Minimum trust level: `usable` — happy path on every endpoint works
- Stretch trust level: `reusable` — error semantics and auth are verified
- Remaining risk: concurrency bugs, long-running load behavior, downstream dependencies
