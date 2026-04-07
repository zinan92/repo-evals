# Final Verdict — content-downloader

## Repo

- **Name:** zinan92/content-downloader
- **Date:** 2026-04-07
- **Final bucket:** `usable`

## Why This Bucket

### Core outcome — Mixed (1 / 4 平台真实可用)

| 平台 | 结果 |
|------|------|
| Douyin | ✅ 强健（Playwright fallback 在 API 失败时真的接管） |
| WeChat OA | ❌ Silent failure（0-byte article.html，空 metadata） |
| X / Twitter | ❌ Silent failure（无 media，无 metadata） |
| Xiaohongshu | ⚪ 未测 |

### Scenario breadth — 弱

只有 1 个平台跑通核心路径。Douyin profile 批量、cookies 采集、xhs sidecar 自管理这些"加分项"都没验证。

### Repeatability — 部分通过

Dedup 工作（重跑 Douyin 被正确跳过、manifest 不重复追加），但 dedup 检查时机不对：发生在 3 次 API 重试之后而不是之前，浪费请求。

### Failure transparency — 严重不达标

- ✅ 不支持平台路径处理得很好：清晰列出 supported list + URL patterns
- ❌ WeChat 和 X adapter 都违反了 README 自己写的 fail 契约：失败时应该 "skip + report in result"，实际是无声地写 0 字节文件并报告 "Downloaded"
- 这是评测中最严重的发现 —— 下游 pipeline 拿到一个看似正常的 `content_item.json` 但所有字段都空，会带着脏数据继续

## What I Would Say In Plain English

> "如果你只用 Douyin，这个仓库现在就能上生产，Playwright fallback 是一段真正的好工程。
> 但如果你打算让它当下游 pipeline 的统一入口，**先别**：WeChat 和 X 两个 adapter 现在会无声地产出空文件而 CLI 仍然报 'Downloaded'，这种 silent failure 在 pipeline 里最难调。"

定位 = `usable`：核心路径之一可用，但 4 个平台中 2 个 silent fail，违反了仓库自己定义的 failure transparency 契约。**不能**评 `reusable`，因为下游消费者必须先在每次读 `content_item.json` 之后手动校验字段非空 —— 这正是 ContentItem 标准化想消除的工作。

## Remaining Risks

1. **Silent failure 是污染源。** 任何下游 pipeline 用这个仓库的输出都需要在每次读 ContentItem 后做防御性校验，否则脏数据会扩散。
2. **README ↔ 代码对不齐。** README 说 "tests 303 passed / coverage 85%"，但端到端跑下来 50% 平台 silent fail —— 现有测试套件没有"产物非空"断言。
3. **Cookie 路径未验证。** 没测过 Douyin 走 cookies 的快路径（评测时 cookies 文件不存在，强制走 fallback）。Cookie 过期时的体验未知。
4. **Xhs sidecar 自管理未验证。** 这是 README 重点宣传的特性，本次未覆盖。
5. **Adapter API 漂移风险。** 全平台依赖逆向 API，平台一改，adapter 就坏 —— 对 Douyin 来说至少有 Playwright fallback 兜底，其它平台没有。

## Recommended Next Actions

按优先级：

1. **修 wechat_oa 和 x adapter 的 silent failure**：response 为空时必须 raise，而不是写 0 字节文件。
2. **加端到端"产物非空"测试**：每个 adapter 至少一个真实 fixture 跑完后断言 `content_item.json` 关键字段非空、media 文件大小 > 0。
3. **dedup 提前**：先查 manifest，命中就 short-circuit，避免无效 API 重试。
4. **加一个 `--strict` flag**：任何 silent fail 直接 exit 非 0，方便 pipeline 集成。
5. 修完后重跑此 eval，目标晋级到 `reusable`。
