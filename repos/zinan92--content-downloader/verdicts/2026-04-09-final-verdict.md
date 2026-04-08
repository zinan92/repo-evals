# Final Verdict — content-downloader

## Repo

- **Name:** zinan92/content-downloader
- **Date:** 2026-04-09
- **Evaluated target commit:** `e86ed97` (local `main`, docs-only ahead of `origin/main`)
- **Final bucket:** `unusable`
- **Rule-guided recommendation:** `unusable` (see `2026-04-09-recommendation.yaml`)

## Why This Bucket

### Core outcome — still split, and the failures are on critical claims

| 平台 / 场景 | 结果 |
|------|------|
| Douyin | ✅ 真成功。178 MB 视频 + 封面 + 完整 metadata + 标准化 ContentItem。 |
| Douyin dedup | ⚠️ 结果正确，但先浪费 3 次 API 重试后才 skip。 |
| WeChat OA | ❌ 两个真实 URL 都是 silent failure：CLI 报 `Downloaded`，但 `article.html` 0 字节、title/author/publish_time 全空。 |
| X / Twitter | ❌ 仍然不构成成功：CLI 报 `Downloaded`，但没有 `text.txt`、没有 media、核心字段为空，还写出不一致目录结构。 |
| Unsupported URL | ✅ 清晰报错，支持列表和 URL patterns 都齐。 |

### 为什么这次不是 `usable`

这次我接受了 verdict calculator 的更严格结论：**repo 级别应该评 `unusable`**。

原因不是“完全不能用”，而是这个仓库最核心的产品承诺是“统一 content downloader”，而不是“一个很好用的 Douyin downloader”。在 fresh live re-eval 里：

- `claim-003` 公众号下载继续失败
- `claim-004` X 下载继续失败
- 而且两条都还是 **CLI 说成功、产物却是空** 的 failure mode

按照我们现在的 bucket 定义，这已经越过了“基础可用性”的底线。  
如果一个 repo 会在 critical path 上无声地产出脏数据，就不应该让用户在没有额外防御逻辑的前提下直接依赖它。

### 技术层也没有给它加分

本次真实跑 `python3 -m pytest -q` 的结果是：

- `294 passed`
- `9 failed`
- `75% coverage`

失败集中在 Douyin adapter tests。  
这和 README 里暗示的“高通过率 / 高覆盖率”并不一致，所以我们不能用“测试看起来很多”来抵消 live eval 里的 critical failures。

## What I Would Say In Plain English

> “如果你只想下载 Douyin，这个仓库依然有一条很强的成功路径，Playwright fallback 是真本事。
>
> 但如果你把它当成 README 宣称的统一多平台下载器，当前还不能放心用。WeChat 和 X 两条 critical path 会假装成功并写出空结果，这对任何下游 pipeline 都是高风险。现在最准确的 bucket 不是 usable，而是 unusable。” 

## What Improved vs The Previous Eval

1. 这次 run 有完整 provenance，知道是谁、何时、对哪个 commit 跑的。
2. 旧结论被 fresh live run 复现了，不是偶发。
3. X 这次比旧基线多写出了一点 metadata / placeholder，但仍然不满足 claim。
4. 额外拿到了技术层结论：测试套件当前并非全绿。

## Remaining Risks

1. **Silent failure 仍然是最大风险。** WeChat 和 X 会污染下游 pipeline。
2. **Dedup 仍然太晚。** 先网络重试再 skip，浪费请求与时间。
3. **README 与当前现实仍不对齐。** 平台支持面和测试健康度都被写得比实际强。
4. **XHS 仍未做 live eval。** README 的 sidecar 自管理 claim 还没有被真实验证。

## Recommended Next Actions

按优先级：

1. **修 WeChat 和 X 的 false-success / silent-failure**  
   任何空 HTML、空 metadata、空 tweet placeholder 都必须显式 fail，而不是打印 `Downloaded`。
2. **把 dedup 前移到网络请求之前**  
   先查 manifest，命中就直接 skip。
3. **给每个 adapter 加 live-ish non-empty assertions**  
   至少断言 `content_item.json` 关键字段非空、关键产物大小 > 0。
4. **修 README / badge / contract 描述**  
   文档必须和真实支持面同步。
5. **补一次 XHS 的真实 eval**  
   这条高优先级 claim 现在仍然是未知数。

修完 1-3 之后，这个 repo 很有机会重新回到 `usable`，甚至继续往上走；但在当前状态下，不应该给更高 bucket。
