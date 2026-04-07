# Business Notes — end-to-end-multimodal

## Scenario

把 content-extractor 当成 trading-co content pipeline 的"原始素材 → 研究简报"环节，喂给它真实的视频/文章/音频，看下游能不能直接读 structured_text.md 当作研究素材。

## What Happened

| 输入 | 期望 | 实际 | 可用？ |
|------|------|------|-------|
| **30s 中文 Douyin clip**（content_item dir） | 转录 + 分析 + structured_text | ✅ 7 segments、131 词、7 个 topics、5 个 takeaways、完整 markdown 简报 | ✅ 完美 |
| **0 字节 article.html**（来自上游 wechat_oa silent fail） | 不崩 + 标记空 | ⚠️ 输出三件套但全空，extraction_status 报 "ok" | ⚠️ 不死但状态不诚实 |
| **裸 .mp3 音频文件** | README 说支持 → 跑通 | ❌ "No extractor registered for content_type='audio'" | ❌ 假承诺 |
| **不存在路径** | 清晰报错 + exit 1 | ✅ "Path does not exist" + exit 1 | ✅ |
| **无效 JSON** | 清晰报错 + exit 1 | ✅ "Invalid JSON in ..." + exit 1 | ✅ |
| **batch 二次跑同目录** | 全部 skip | ✅ "1 skipped" | ✅ |
| **`pytest --collect-only`**（验证 README 221 tests） | 收集到 221 | ❌ tests/test_llm.py ImportError，整个 collect 直接 fail | ❌ README 撒谎 |
| **transcribe.py 配置审查** | 在 Mac 上能用 GPU | ❌ device="auto" 永远 fallback 到 CPU（CTranslate2 不支持 MPS） | ❌ Mac 用户被坑 |

## Was The Result Usable?

**视频核心路径 → 完全可用。** 30s 中文片段（含中英混读）→ 真实 transcript → Claude 分析出 "复利思维 / Elon Musk / 自然天赋 vs 努力" 这种有价值的话题 → structured_text.md 是真正可以丢给写作 pipeline 当素材的研究简报。这个核心路径比 content-downloader 强。

**文章降级 → 凑合可用。** 给空 HTML 不会崩，但 extraction_status 报 "ok" 而不是 "empty" 或 "skipped"，下游如果只看 status 不看 Words 会以为有内容。

**音频路径 → 不能用。** README 明确列了 `.mp3 / .wav / .m4a / .aac / .ogg / .flac`，但代码里没 audio adapter。如果我是个新用户，看到 README 跑 `content-extractor extract ./podcast.mp3`，会立即吃个错误。**这跟 content-downloader 的 silent fail 是同一个家族的问题（README ↔ 代码不对齐），但严重程度低一档**：这里至少 CLI 报错了，而不是无声地写 0 字节文件。

**测试 badge → 撒谎。** 221 tests / 96% coverage 这种数字写在 README 是有责任的 —— 任何想 contribute 或评估代码质量的人都会直接 `pytest` 复现一次。实测：测试套件 collection 阶段就 ImportError，连 207 tests 都跑不起来。

## Anything Surprising?

1. **Mac 性能这一点最 ouch。** 用户是 Mac mini，repo 里默认的 `faster-whisper + device="auto"` 在 Mac 上永远走 CPU —— CTranslate2 后端不支持 Apple Silicon。30 秒中文音频 25.8 秒 wall time（≈ 实时），170MB / 10 分钟 Douyin 视频跑了 28 分钟还没跑完。`mlx-whisper`（Apple 官方）同样输入快 5-10x。README 完全没提这个 trade-off，新 Mac 用户跑第一个长视频就会以为脚本卡住了。

2. **failure transparency 比想象中好。** 三个失败场景的错误信息都很清晰，退出码都 1。这比 content-downloader 强一档。

3. **audio adapter 的缺失是"承诺前置"。** cli.py 里 auto-wrap 逻辑明确把 mp3 设成 `content_type='audio'`，README 也明确列了 6 个音频扩展名。但 router 里只注册了 video / image / article / gallery 四个 adapter。这是典型的"先在 README 写承诺再实现，结果只实现了一半"。修起来不难（要么加 audio adapter 把它路由到 video pipeline 做 audio-only 转录，要么 auto-wrap 时就把 audio 文件当 video 处理）。

4. **extraction_status="ok" on empty input.** 0 字节 article.html → 走完 trafilatura → 空字符串 → 空 LLM 分析 → status:ok。技术上没崩 = ok，但下游用 status 当 health check 会被骗。建议加 status="empty" 或 status="degraded"。

5. **structured_text.md 的质量比预期高很多。** 30 秒 clip 拿到的 markdown 简报在 header 里带了原视频的 title / author / platform / publish_time / engagement 数字，summary 段落也是 LLM 生成的真句子，不是模板填空。这是真的能扔进研究 pipeline 的产出。

6. **跟 content-downloader 是一对的。** 上游 silent fail（wechat_oa 0 字节）和下游 honest degradation（words=0 但 status=ok）合在一起就是 pipeline-level 的脏数据扩散源。修这两个的话要从 content-downloader 的 wechat adapter 开始，content-extractor 这边只需要把 status 字段做诚实就够了。

7. **test_llm.py 的 ImportError 是 5 行就能修的。** llm.py 里有 LLMError / LLMConfigError / LLMAPIError，没有 LLMRateLimitError —— 大概率是某次重构删了这个 class 但 test 没同步。`grep -rn LLMRateLimitError` 一下就能找到。
