# Final Verdict — zinan92/intel (park-intel)

## Repo

- **Name**: zinan92/intel
- **Version tested**: commit 3c6eaa9 (cloned + live 2026-04-24)
- **Date**: 2026-04-24
- **Archetype**: api-service
- **Final bucket**: 🟡 reusable
- **Confidence**: medium

## Plain English

- **Outcome if adopted**: 自建一个 FastAPI + React 的情报采集管道，10 个文档化 REST 接口挨个调全部 200 + 真实 JSON；6 个免密钥源立即开始采集（RSS 已积累 26K 文章，GitHub Trending 14K，Google News 8.9K）；/health 老老实实标记哪些源挂了、哪些没配。
- **Regret scenario**: 这是要你自己跑自己维护的服务。测评时就发现 reddit 采集已经悄悄挂了 11 天，/health 显示 `stale` 但不会替你修。想用 LLM 打相关性分必须自己配 ANTHROPIC_API_KEY。跑 pytest 还有 2 个 migration 测试挂着没处理。

## Why This Bucket

- **Ceiling reason**: `evidence_completeness='portable'` → 最高到 `reusable`（没在第二个环境独立复跑，也没有 CI 证明每次 push 都是绿的）
- **Not higher** (`recommendable`): 只在一台机器、一个时刻跑过；2 个测试 failing；reddit 采集坏了 11 天没人修
- **Not lower** (`usable`): 10 个文档化端点全部返回 200；错误语义（404/422）正确；响应确定；测试套件 99.5% 过；health 接口诚实披露问题

## Evidence

| claim | priority | status | 说明 |
|-------|----------|--------|------|
| claim-001 核心无密钥源能采集 | critical | passed | 6 个 keyless 源全部 status=ok，总计 ~55K 文章 |
| claim-002 所有文档化端点都响应 | critical | passed | 10 文档端点 + 2 详情端点 全部 HTTP 200 |
| claim-003 错误语义正确 | critical | passed | 404 missing-int-id / 422 type-error，无隐藏 500 |
| claim-004 响应确定 | high | passed | /api/ui/topics 连调两次 md5 一致 |
| claim-005 可选源优雅降级 | high | passed | social_kol no_data 不崩，xueqiu 配好即 ok |
| claim-006 测试套件健康 | high | passed_with_concerns | 366 pass / 2 fail，失败在 migration 而非接口 |
| claim-007 /health 如实披露 | high | passed | reddit stale 266h、social_kol no_data — 不伪装 |
| claim-008 事件聚合真能出结果 | medium | passed | 627 KB 排序事件列表 + 详情 schema 完整 |

## What Would Take This to 🟢 Recommendable

1. **修 2 个 failing migration 测试** —
   `test_source_registry_model.py::test_migration_creates_table` 和
   `test_source_registry_seed.py::test_schedule_hours_from_config`
2. **修 reddit 采集器**（11 天没采，或者设置自动 alert）或者对 stale 源做自愈逻辑
3. **加 CI**（GitHub Actions 跑 pytest）证明每次 push 绿
4. **在第二台机器独立复跑**一遍（Linux / Docker），验证 fresh install 路径确实是 README 描述的那样
5. **给 /api/users 写接口加一次 POST/PUT/GET 的端到端测试**（本次 eval 只覆盖了 read-only surface）

## Artifacts

- `claims/claim-map.yaml` — 8 claims, 3 critical, all passed (1 high 为 passed_with_concerns)
- `areas/endpoint-coverage/runs/2026-04-24/run-smoke/` — 10 endpoint JSON captures + pytest log + summary
- `verdicts/2026-04-24-verdict.html` — product page
- `verdicts/2026-04-24-verdict-input.yaml` — calculator input
