# Business Notes — live-multi-platform-recheck

## Scenario

让一个内容团队把 `content-downloader` 当成统一入口来下载 4 类 URL：

- 抖音单条视频
- 公众号文章
- X 推文
- 一个明确不支持的平台 URL

再额外验证两件事：

- 同一个抖音 URL 重跑时是否真的去重
- 这个 repo 自己的测试套件当前是不是健康

谁会在意这件事：任何把它接到 `content-toolkit`、`content-extractor`、`content-rewriter` 或其他下游 pipeline 的人。

## What Happened

| 场景 | 结果 | 实际可用性 |
|------|------|-----------|
| Douyin 首次下载 | 成功 | ✅ 真成功。下载出 178MB 视频、封面、完整 metadata、标准化 ContentItem。 |
| Douyin 重跑 | 跳过 | ⚠️ 去重结果对，但时机不对。仍然先做 3 次 API 重试，之后才发现已下载。 |
| WeChat OA #1 | CLI 报 `Downloaded` | ❌ 假成功。`article.html` 0 字节，title/author/publish_time 全空。 |
| WeChat OA #2 | CLI 报 `Downloaded` | ❌ 同样假成功，不是单条偶发。 |
| X 推文 | CLI 报 `Downloaded` | ❌ 仍不可用。没有 `text.txt`、没有媒体、核心字段全空。 |
| Unsupported URL | 正确报错 | ✅ 错得很清楚，支持平台和 URL pattern 都列出来了。 |
| `python3 -m pytest -q` | 294 passed / 9 failed | ⚠️ 技术层不健康，而且和 README badge 不一致。 |

## Was The Result Usable?

**部分可用。**

如果你只拿它下 Douyin，这个仓库现在仍然是能打的，尤其是 API 被拒后自动回退到 Playwright 这一段，是真正解决问题的工程。

但如果你把它当成 README 里宣称的“统一 content downloader”，答案还是**不能放心用**。WeChat 和 X 两条路径都继续出现 `CLI 说成功，但产物是空` 的问题。对 pipeline 来说，这比直接报错更危险，因为下游会把一个看起来合法的 `content_item.json` 当真数据继续处理。

## Anything Surprising?

1. **Douyin 依旧很强。**
API path 连续失败后，fallback 仍然能拿到真实视频、真实作者、真实互动数据。这条线说明 repo 不是“整体都不行”，而是能力分布非常不均衡。

2. **WeChat 的问题不是偶发。**
这次专门跑了两个不同 URL，结果都一样：0 字节 `article.html` + 空 metadata + CLI 仍然说 `Downloaded`。这说明是系统性 bug，不是内容源刚好异常。

3. **X 比旧基线多了一点“看起来像数据”的东西，但仍然不构成成功。**
现在它至少会写出 `metadata.json` 和 `content_item.json`，但实际内容仍然是空 title / 空 author / 无 text / 无 media 的 placeholder。换句话说，它从“完全空壳”变成了“更像真的空壳”。

4. **测试套件比 README 弱。**
这次真实跑到的是 `294 passed / 9 failed / 75% coverage`，不是 README 上那种“全绿高覆盖”。失败都集中在 Douyin adapter 测试，这意味着最强的那条下载路径，测试层反而有债。

5. **本地 checkout 比 GitHub 远端多一个 commit，但这次不影响行为结论。**
多出来的是 capability contract / SKILL 文档文件，不是 runtime 代码，所以这次 eval 仍然能代表公开仓库当前实现。
