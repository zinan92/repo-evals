# Business Notes — smoke-multi-platform

## Scenario

让一个非技术评测者把 4 个平台的 URL 喂给 `python3 -m content_downloader download`，看下游 pipeline 拿到的"标准化 ContentItem"到底能不能用。

## What Happened

| 平台 | URL | CLI 报告 | 实际产物 | 可用？ |
|------|-----|---------|---------|-------|
| **抖音** | `/video/76210...` | Downloaded | 178MB MP4 + 封面 + 完整 metadata（title / author / likes / comments / shares） | ✅ 完全可用 |
| **公众号 #1** | `/s/Bo3K6P...` | Downloaded | `article.html` **0 字节** + `content_item.json` 字段全空 + 无 `text.txt` | ❌ 假成功 |
| **公众号 #2** | `/s/uvJzYU...` | Downloaded | 同上：0 字节 HTML，空 metadata | ❌ 假成功 |
| **X** | `elonmusk/.../1849...` | Downloaded | 无 `metadata.json`、无 `media/*`、无 `text.txt`、`content_item.json` 全空 | ❌ 假成功 |
| **不支持 URL** | `example.com/foo` | Error: No adapter found | （正确报错）列出全部 supported platforms + URL patterns | ✅ 错得漂亮 |
| **抖音 重跑** | 同首次 | Skipped (already downloaded) | manifest 没新增行 | ✅ 但有效率问题 |

## Was The Result Usable?

**对单一 Douyin 用例 → 是。** Playwright fallback 是这个仓库最亮的工程：API 签名被拒后自动切换到浏览器抓取，下游拿到的是真数据，不是占位。

**对 wechat_oa / x → 否。** 这是评测里最严重的发现：CLI 打印 "Downloaded" 但磁盘上是空文件 + 空字段。下游消费者（content-rewriter / content-intelligence）会读到一个看似正常的 `content_item.json`，但所有字段都空，必然踩雷。这违反了 README 自己列出的 "fail" 契约 —— 失败应该 → "skip + report in result"，而不是无声地写 0 字节文件。

**对错误处理 → 是。** Bad URL 路径处理得非常好。

## Anything Surprising?

1. **Douyin 比预期强很多。** 在没有 cookies 的情况下，API 路径必然失败，但 Playwright fallback 让它仍然能产出完整数据 + 178MB 视频。fallback 是真正的工程，不是装饰。

2. **WeChat OA "成功" 写 0 字节文件。** 这是最危险的失败模式。adapter 大概率写完空 HTML 后没检查响应，也没在 content_item 里把状态设成失败。下游脚本读这个文件不会立刻崩，会带着脏数据继续往下走 —— 这是 pipeline 里最难调的那种 bug。

3. **X 适配器看起来根本没接 yt-dlp。** README 说 "X/Twitter | yt-dlp | 媒体下载"，但实际跑出来连 metadata.json 都没有。怀疑是 yt-dlp 调用失败但 except 全吞了。

4. **Dedup 检查发生在 API 调用之后。** 第二次跑 Douyin 时仍然做了 3 次 API 重试 + 失败后才发现 "已下载"。应该先查 `manifest.jsonl`，命中就 short-circuit。

5. **README 写得比代码好。** 文档详尽、capability contract 清晰、test badge 写 "303 passed / 85% coverage" —— 但实际跑出来 2/4 平台 silent fail。说明现有测试套件没有覆盖端到端的"产物非空"断言。
