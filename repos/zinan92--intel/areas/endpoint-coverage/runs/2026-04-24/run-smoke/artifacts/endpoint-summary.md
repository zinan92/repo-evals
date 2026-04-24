# Endpoint smoke test — 2026-04-24

Live service: `http://localhost:8001` (running from `~/work/trading-co/park-intel`, git 3c6eaa9).

## Documented endpoints → response codes

All tested with `curl -sf`, timeout 10s.

### Core Data (README "API Endpoints → Core Data")

| Endpoint | Status | Size | Notes |
|----------|--------|------|-------|
| `GET /api/health` | 200 | 1.8 KB | 10 active sources, dict keyed by source_type |
| `GET /api/articles/latest?limit=3` | 200 | 2.5 KB | returns list of article dicts |
| `GET /api/articles/digest` | 200 | 52.8 KB | articles grouped by source |
| `GET /api/articles/signals?hours=24` | 200 | 21.7 KB | topic heat + narrative momentum |
| `GET /api/articles/sources` | 200 | 1.8 KB | historical source stats |
| `GET /api/articles/search?q=openai` | — | — | not explicitly smoked, same pattern |

### Frontend Read Model

| Endpoint | Status | Size | Notes |
|----------|--------|------|-------|
| `GET /api/ui/feed?window=24h` | 200 | 19.1 KB | priority-scored feed |
| `GET /api/ui/items/183623` | 200 | (real article) | detail endpoint works with valid id |
| `GET /api/ui/topics` | 200 | 122.8 KB | topic list |
| `GET /api/ui/sources` | 200 | 0.9 KB | 10 active sources |

### Events

| Endpoint | Status | Size | Notes |
|----------|--------|------|-------|
| `GET /api/events/active` | 200 | 627.5 KB | ranked by signal score |
| `GET /api/events/2912` | 200 | (real event) | detail endpoint works |
| `GET /api/events/history?days=30` | 200 | 13.3 KB | closed events archive |

## Error semantics

| Scenario | Expected | Actual | OK? |
|----------|----------|--------|-----|
| `GET /api/events/9999999` (valid int, missing id) | 404 | 404 `{"detail":"Event not found"}` | ✓ |
| `GET /api/ui/items/99999999` (valid int, missing id) | 404 | 404 `{"detail":"Item not found"}` | ✓ |
| `GET /api/articles/latest?limit=abc` (type error) | 422 | 422 with FastAPI detail array | ✓ |
| `GET /api/events/nonexistent-id` (type error in path) | 422 | 422 with FastAPI detail array | ✓ |

## Determinism

`md5(GET /api/ui/topics)` twice → identical hash (`aaab522a...e096`).

## Source health

10 source types registered, status breakdown:
- 8 `ok` (RSS, github_release, github_trending, google_news, hackernews, website_monitor, xueqiu, yahoo_finance)
- 1 `stale` (reddit, last collected 2026-04-13, 266 hours ago)
- 1 `no_data` (social_kol, needs optional `clawfeed` CLI)

The stale+no_data statuses are surfaced honestly, not masked.

## Test suite

```
366 passed, 2 failed in 51s
```

README claims "290+ tests passing". Actual test count is 368, of which 366 pass. The 2 failures are both in source registry migration tests (`test_migration_creates_table`, `test_schedule_hours_from_config`) — not endpoint-surface regressions.
