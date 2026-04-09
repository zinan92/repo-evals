# Business Notes

## Scenario

- 对 `zinan92/intel` 做 fresh clone 级别的 live eval，目标是判断这个 repo
  到底是不是一个“装上就能跑起来的自托管情报服务”，而不是只会本地 demo 的
  skeleton。
- 本次测试覆盖 Python 安装、pytest、真实服务启动、核心 API、前端 build 后的
  一体化 serving，以及无可选密钥时的降级表现。

## What Happened

- Python 依赖在新 virtualenv 里安装成功，前端 `npm install` 和 `npm run build`
  也都成功。
- README 默认端口 `8001` 在这台机器上已被占用，所以第一次 `python main.py`
  是环境冲突，不是应用本身崩了；相同应用切到 `8013` 后稳定启动。
- 服务启动后，`/api/health`、`/api/articles/latest`、`/api/ui/feed` 都返回了
  真实数据，不是空 schema。说明 scheduler、数据库和读取接口这条主路径是真通的。
- build 完前端后，`/` 和 `/health` 都成功返回前端 HTML，证明“后端统一提供 UI”
  这个 claim 成立。
- 但两件事让这次结果没法直接升到推荐级：
  1. `pytest` 不是全绿，而是 `366 passed / 2 failed`
  2. 详细 health 语义仍然不够可信，有些 source 的状态和计数会让人误判

## Was The Result Usable?

- 是，而且不只是“能用”，我会把它归到 `reusable`。
- 理由是核心用户价值已经成立：fresh clone 之后确实能得到正在采集、能查询、
  能看前端的完整系统。
- 但我不会给 `recommendable`，因为测试套件还没完全恢复健康，而且 health 细节
  对运维判断还不够稳。

## Anything Surprising?

- 最正面的惊喜是：这个 repo 的核心价值是真落地的。很多类似 repo 会卡在
  “服务能起，但接口没数据”这一步，这个没有。
- 最不舒服的点是 detailed health 视图里的很多 per-source `articles_24h`
  显然像是 source-type 级别的总量复用到了每个 source 实例上，这会让 dashboard
  看起来很强，但不够诚实。
- `/api/events/active` 返回空数组不算 bug，但也说明“事件层”现在还不能算这次
  eval 的主要加分项。
