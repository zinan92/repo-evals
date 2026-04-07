<div align="center">

# repo-evals

**Claim-first 仓库评测框架 — 不只是测命令是否能跑，而是测仓库是否兑现了自己的承诺。**

[![Bash](https://img.shields.io/badge/bash-5.0+-89e051.svg)](https://www.gnu.org/software/bash/)
[![Framework](https://img.shields.io/badge/framework-claim--first-blue.svg)](docs/FRAMEWORK.md)
[![Verdicts](https://img.shields.io/badge/verdicts-4_buckets-orange.svg)](docs/VERDICT-BUCKETS.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

```
in  target repo (owner/repo) + repo_type (skill | capability | orchestration)
out eval scaffold (claims + plan + runs + verdict)
    final reliability bucket: unusable | usable | reusable | recommendable

fail target not <owner/repo>     → exit + usage hint
fail scaffold already exists     → keep existing files (idempotent)
fail support layer passes but core layer untested → overall verdict capped at "usable"
```

评测分两层：

- **业务层** — 非技术人员也能读懂的 `eval-plan.md`，定义"测什么场景、跑几次、过线标准"
- **技术层** — `runs/` 下保存每一次执行的输入、命令、产物、失败、重试，以及 provenance

每个被评测的 repo 最终落入且只落入**一个**可靠性桶。

## 四个可靠性桶

| 桶 | 含义 | 适用场景 |
|----|------|---------|
| `unusable` | 核心承诺都跑不通，或只是偶然成功 | 不要用 |
| `usable` | 主任务能跑通至少一次，但信心有限 | 实验性使用 |
| `reusable` | 多个真实场景下稳定可用 | 内部重复使用 |
| `recommendable` | 边界清晰、稳定、敢推荐给别人 | 对外推荐 |

> **决策规则**：强 verdict 必须配强 plan。尤其是 hybrid repo，如果真正的核心用户价值层没测到，整体 verdict 最高只能是 `usable`。

## 示例输出

一次 `scripts/new-repo-eval.sh owner/repo skill` 之后生成的目录结构：

```
repos/owner--repo/
├── repo.yaml                          # 元数据 (owner, repo, repo_type)
├── claims/
│   └── claim-map.yaml                 # 从 README/SKILL.md 抽出的 claim
├── plans/
│   └── 2026-04-07-eval-plan.md        # 业务可读的评测计划
├── fixtures/                          # 测试输入
├── runs/                              # 每次执行的技术证据
│   └── 2026-04-07/run-<slug>/
│       ├── run-summary.yaml
│       ├── business-notes.md
│       ├── logs/
│       ├── artifacts/
│       └── screenshots/
├── areas/                             # 复杂 repo 的能力分区 (可选)
└── verdicts/
    └── 2026-04-07-final-verdict.md    # 最终判定 + 桶
```

实际样例：[`repos/zinan92--content-toolkit/`](repos/zinan92--content-toolkit/)

## 标准流程

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 1. new-repo  │───▶│ 2. claims    │───▶│ 3. eval-plan │───▶│ 4. runs      │
│    scaffold  │    │  (从文档抽取) │    │  (业务可读)   │    │  (技术证据)   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                     │
                                                                     ▼
                                                            ┌──────────────┐
                                                            │ 5. verdict   │
                                                            │  → 桶        │
                                                            └──────────────┘
```

1. 在 `repos/` 下建仓库文件夹
2. 在 `repo.yaml` 里写 metadata
3. 在 `claims/claim-map.yaml` 里抽 claim
4. 在 `plans/YYYY-MM-DD-eval-plan.md` 里写业务可读 plan
5. 在 `runs/` 下保存每次执行的证据和 provenance
6. 在 `verdicts/` 下写最终 verdict + 桶

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/zinan92/repo-evals.git
cd repo-evals

# 2. 新建一个 repo 评测脚手架
scripts/new-repo-eval.sh owner/repo skill

# 3. 给复杂 repo 添加一个能力分区 (可选)
scripts/new-area.sh owner--repo area-slug

# 4. 创建一次新的执行记录
scripts/new-run.sh owner--repo run-slug
scripts/new-run.sh owner--repo run-slug area-slug
scripts/new-run.sh owner--repo run-slug area-slug /path/to/target-repo
```

## 评测维度（针对 skill 类 repo）

| 维度 | 问题 |
|------|------|
| **Core Outcome** | 能不能完成它声称的核心任务？ |
| **Scenario Breadth** | 能不能处理多种真实输入，而不是只有一个幸运 case？ |
| **Repeatability** | 同一个 workflow 跑多次结果是否一致？ |
| **Failure Transparency** | 失败的时候是不是清晰报错，而不是假装成功？ |

## Evidence Rules

- 证据应当尽量放进 repo 自己的 `runs/.../artifacts/`
- `run-summary.yaml` 里的 artifact 路径默认使用相对路径
- 每次 run 尽量记录 target repo commit、runner、session id、model
- 只写 `/tmp/...` 不算完整证据链
- 用 `scripts/copy-evidence.sh` 把外部证据拷进 run 文件夹，自动生成
  `artifacts/manifest.yaml`（size + sha256 + source）

## Phase 1 Platform Tools

Trust foundation — 让每次 eval 都可审计、可复现、可比较。详见各自的 doc：

| 工具 | 作用 | Doc |
|------|------|-----|
| `scripts/new-run.sh` | 创建 run 脚手架 + 自动捕获 provenance (EVAL_* env vars) | [PROVENANCE.md](docs/PROVENANCE.md) |
| `scripts/append-provenance.sh` | 往 legacy / partial run 补 provenance，不覆盖已有字段 | [PROVENANCE.md](docs/PROVENANCE.md) |
| `scripts/copy-evidence.sh` | 把 `/tmp` / 外部证据拷进 `runs/.../artifacts`，生成 manifest | [EVIDENCE-COPIER.md](docs/EVIDENCE-COPIER.md) |
| `scripts/verdict_calculator.py` | 规则驱动的 verdict 推荐（含 hybrid-cap rule），支持 override | [VERDICT-CALCULATOR.md](docs/VERDICT-CALCULATOR.md) |

```bash
# Typical Phase-1 flow
export EVAL_RUNNER=cc EVAL_AGENT="Claude Code" EVAL_MODEL=claude-opus-4-6
scripts/new-run.sh owner--repo smoke-run "" /path/to/target-repo

# After running the actual eval
scripts/copy-evidence.sh repos/owner--repo/runs/$(date +%F)/run-smoke-run \
    /tmp/result.json --note "happy path"

# Once claim-map.yaml statuses are filled in
python3 scripts/verdict_calculator.py verdicts/verdict-input.yaml --md
```

## 项目结构

```
repo-evals/
├── docs/
│   ├── FRAMEWORK.md           # 评测框架定义
│   ├── NAMING-CONVENTIONS.md  # 命名规范
│   └── VERDICT-BUCKETS.md     # 四个桶的判定标准
├── templates/
│   ├── repo/                  # repo 评测脚手架模板
│   ├── area/                  # 能力分区模板
│   └── run/                   # 单次 run 模板
├── scripts/
│   ├── new-repo-eval.sh       # 新建 repo 评测
│   ├── new-area.sh            # 新建能力分区
│   └── new-run.sh             # 新建一次 run
└── repos/                     # 所有被评测的 repo
    └── <owner>--<repo>/
```

## 文件夹经验法则

- 单一目的的 repo：只用 `repos/<slug>/` 根目录
- 多个独立能力的 repo：在 `areas/` 下分区
- Orchestration repo：一个 area 给编排本身，每个下游能力一个 area

## For AI Agents

本节面向需要把 repo-evals 当作工具调用的 Agent。

### Capability Contract

```yaml
name: repo-evals
capability:
  summary: Claim-first repository evaluation harness with business + technical layers
  in: target repo (owner/repo) + repo_type
  out: eval scaffold + final reliability bucket
  fail:
    - "target not in owner/repo form → exit with usage"
    - "scaffold exists → idempotent, preserves existing files"
    - "untested core layer → overall verdict capped at 'usable'"
  buckets: [unusable, usable, reusable, recommendable]
cli_commands:
  - cmd: scripts/new-repo-eval.sh
    args: ["<owner/repo>", "[repo_type]"]
    description: Bootstrap a new repo evaluation scaffold
  - cmd: scripts/new-area.sh
    args: ["<owner--repo>", "<area-slug>"]
    description: Add a capability area to a complex repo
  - cmd: scripts/new-run.sh
    args: ["<owner--repo>", "<run-slug>", "[area-slug]", "[target-repo-path]"]
    description: Create a run folder for one concrete test pass
artifacts:
  plan: plans/YYYY-MM-DD-eval-plan.md
  run: runs/YYYY-MM-DD/run-<slug>/
  verdict: verdicts/YYYY-MM-DD-final-verdict.md
```

### Agent 调用示例

```python
import subprocess
from datetime import date

# 评测一个新 repo
subprocess.run(
    ["scripts/new-repo-eval.sh", "owner/some-skill", "skill"],
    cwd="/path/to/repo-evals", check=True,
)

# 跑一次执行
slug = "owner--some-skill"
subprocess.run(
    ["scripts/new-run.sh", slug, "smoke-test"],
    cwd="/path/to/repo-evals", check=True,
)

# Agent 接下来：填 claims/claim-map.yaml + plans/*.md，
# 执行测试，把证据写进 runs/，最后在 verdicts/ 里给桶。
```

## 文档

- [FRAMEWORK.md](docs/FRAMEWORK.md) — 评测框架完整定义
- [NAMING-CONVENTIONS.md](docs/NAMING-CONVENTIONS.md) — 命名规范
- [VERDICT-BUCKETS.md](docs/VERDICT-BUCKETS.md) — 四个桶的判定标准
- [PROVENANCE.md](docs/PROVENANCE.md) — Phase 1: provenance 捕获与 legacy 迁移
- [EVIDENCE-COPIER.md](docs/EVIDENCE-COPIER.md) — Phase 1: 把外部证据拷进 run
- [VERDICT-CALCULATOR.md](docs/VERDICT-CALCULATOR.md) — Phase 1: 规则驱动的 verdict 推荐

## License

MIT
