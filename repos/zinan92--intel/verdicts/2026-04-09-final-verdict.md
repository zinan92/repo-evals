# Final Verdict — intel

## Repo

- **Name:** zinan92/intel
- **Date:** 2026-04-09
- **Evaluated target commit:** `3c6eaa9` (`main`, matches `origin/main`)
- **Final bucket:** `reusable`
- **Rule-guided recommendation:** `reusable` (see `2026-04-09-recommendation.yaml`)

## Why This Bucket

### Core outcome — strong

| 检查 | 结果 |
|------|------|
| Fresh clone Python setup | ✅ 成功 |
| Real scheduler + database + ingestion | ✅ 成功，多个 core sources 有真实数据 |
| Core API (`/api/health`, `/api/articles/latest`, `/api/ui/feed`) | ✅ 都返回真实结构化内容 |
| Frontend build + backend serving | ✅ `npm run build` 后 `/` 与 `/health` 都返回前端 HTML |
| Optional-source degradation | ✅ 服务不崩，缺凭据时能继续工作 |
| Events endpoint | ⚠️ schema 正常，但本次返回空数组 |

### Why This Is `reusable`, Not `recommendable`

这个 repo 已经不只是“能起服务”，而是 **fresh clone 后能得到一个真正工作的 self-hosted intelligence pipeline**。
这让它明显高于 `usable`。

但它现在还不该到 `recommendable`，主要有两条原因：

1. **测试套件不是全绿。**
   实测 `pytest tests/` 结果是 `366 passed / 2 failed`。这说明工程面很强，但还不是一个我会放心推荐别人直接拿来二开或部署的状态。

2. **Health 语义还不够可信。**
   `/api/health` 和 `/api/health/sources` 在 optional source 的状态语义上并不总是一致；更明显的是，详细 source 视图里很多 `articles_24h` 像是 source-type 级别的聚合数字被复用到了每一个具体 source 上。
   这会让运维判断“这个具体源到底健康不健康”变得不够可靠。

### Repeatability — good enough for this stage

- fresh-clone setup 跑通
- 服务启动路径跑通
- 前后端一体化 serving 跑通
- 核心 API 都拿到真实数据

这已经足够支持 `reusable`。
但 launchd 背景服务脚本没有在本次 live eval 中真实安装验证，所以长期运维层还没有被完全吃透。

### Failure transparency — mostly good

- 默认端口 `8001` 被占用时，应用不是 silent fail，而是明确报 bind 失败
- 无可选凭据时，系统仍返回可解释的 health 输出
- 空事件列表不会把接口打崩

这里最大的问题不是“失败不透明”，而是“health 细节有点过度乐观”，这属于语义可信度问题，不是硬 crash 问题。

## What I Would Say In Plain English

> “如果你想要一个本地自托管的 market / tech intelligence 服务，这个 repo 已经是真能用、也能反复用的。
>
> 它不是 README 式的空壳：fresh clone 后，scheduler 会真正拉数据，API 会回真实内容，build 完前端后 UI 也能由后端一起提供。
>
> 但我还不会直接把它推荐给别人当成‘放心上生产的模板’，因为测试套件还没完全恢复全绿，health dashboard 里的某些 per-source 计数和状态语义也还不够诚实。”

## Remaining Risks

1. **测试套件还有 2 个真实失败。** 这会拖低对后续改动的信任度。
2. **Detailed health 的 per-source volume 可能误导运维判断。**
3. **Optional source 的状态语义仍需统一。** `disabled`、`no_data`、`ok` 之间界线还不够稳定。
4. **launchd 背景服务脚本本次未真实验证。**
5. **事件层只验证了接口 shape，没有验证“事件洞察质量”。**

## Recommended Next Actions

1. 修掉当前 pytest 的 2 个失败用例，让测试面回到全绿。
2. 重新梳理 `/api/health` 与 `/api/health/sources` 的状态模型，统一 `disabled / no_data / ok` 的含义。
3. 把 detailed source 视图里的 volume 统计改成真实 per-source 计数，而不是 source-type 聚合数复用。
4. 补一次 launchd 脚本的真实安装 / 卸载 smoke test。
5. 等 1-4 做完后，再做一次 clean re-eval，目标有机会升到 `recommendable`。
