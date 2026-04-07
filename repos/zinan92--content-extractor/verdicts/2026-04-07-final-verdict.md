# Final Verdict — content-extractor

## Repo

- **Name:** zinan92/content-extractor
- **Date:** 2026-04-07
- **Final bucket:** `usable`

## Why This Bucket

### Core outcome — 强（视频路径）

| 检查 | 结果 |
|------|------|
| 30s 中文 Douyin clip → transcript + analysis + structured_text | ✅ 全部真实可用 |
| Whisper 中英混读识别 | ✅ |
| Claude LLM 分析（topics/viewpoints/sentiment/takeaways） | ✅ |
| structured_text.md 是真正的研究简报 | ✅ |
| Article 边界（空 HTML 输入）不崩 | ✅ |

### Scenario breadth — 中等

视频 ✅、article 边界 ✅、batch 幂等 ✅、失败模式 ✅。
**完全没碰：** image adapter、gallery adapter、长视频稳定性、不同语言、hallucination 检测的真实触发。

### Repeatability — 通过

Batch 二次跑同目录，1/1 skipped。无浪费。

### Failure transparency — 强

不存在路径 / 无效 JSON / 不支持 content_type 三个场景都给清晰错误 + 退出码 1。
跟 content-downloader 的 silent fail 形成强对比 —— **唯一的瑕疵**：empty article 的 extraction_status 报 "ok"，应该是 "empty" / "degraded"。

## Why Not `reusable`

三个文档↔代码硬不对齐，按"weak plan all-pass 不能给强 verdict"原则，最高只能 `usable`：

### 1. Bare audio file 是假承诺（最严重）

README 明确列了：
> `bare_file_support: extensions: [.mp4, .mov, ..., .mp3, .wav, .m4a, .aac, .ogg, .flac]`

实测 `.mp3`：
> `Detected bare media file. Wrapping as ContentItem...`
> `Error: No extractor registered for content_type='audio'. Supported: ['article', 'gallery', 'image', 'video']`

`cli.py` 的 auto-wrap 逻辑明确把音频文件设成 `content_type='audio'`，但 `router.py` 里只注册了 4 个 adapter，没 audio。**这是承诺前置 bug** —— README 写了功能但代码只实现了一半。

跟 content-downloader 的 silent fail 是同一类病（README ↔ 代码不对齐），但程度低一档：这里至少 CLI 报错了，而不是无声写脏数据。

### 2. README 的 test badge 撒谎

> "221 tests passing / 96% coverage"

实测：
- `pytest --collect-only` 阶段就 ImportError：`tests/test_llm.py` 引用不存在的 `LLMRateLimitError`
- 整个测试套件 collection 直接 fail，连 pytest 都跑不起来
- ignore 掉这个文件后剩 207 tests，比 README 少 14

`llm.py` 里只有 `LLMError / LLMConfigError / LLMAPIError`，`LLMRateLimitError` 大概率是某次重构删了 class 但 test 没同步。**修起来 5 分钟，但放着不管让 README badge 撒谎是 trust 杀手**。

### 3. Mac 性能是架构选择失误

`src/content_extractor/video/transcribe.py:78-82`：

```python
WhisperModel(model_size_or_path=..., device="auto", compute_type="int8")
```

`faster-whisper` 的 CTranslate2 后端**不支持 Apple Silicon GPU/MPS**，所以 `device="auto"` 在 Mac 上永远 fallback 到 CPU。

实测：
- 30 秒中文 audio → 25.8 秒 wall time（≈ 实时，CPU 跑了 60s）
- 170MB / ~10 分钟 Douyin 视频 → 28 分钟还没跑完

`mlx-whisper`（Apple 官方 MLX 框架）在同样硬件上快 **5-10x**。README 的"技术栈"段落完全没提这个 trade-off，新 Mac 用户跑第一个长视频会以为脚本卡死。

不是 bug，是架构选择 —— 但对 Mac 用户来说体验是灾难，而 Mac 是这个 repo 的主要开发/使用环境。

## What I Would Say In Plain English

> "视频核心路径很强：给一段中文短 clip，能拿到真实可用的研究简报。失败模式处理也比 content-downloader 强一档，不会无声写脏数据。
>
> 但有三个 README ↔ 代码不对齐的硬伤：(1) 说支持音频文件其实没 audio adapter；(2) 说有 221 tests 但测试套件 collection 都跑不起来；(3) 在 Mac 上用 faster-whisper 走 CPU，30 秒音频要跑 25 秒，长视频几乎不可用 —— mlx-whisper 同样输入快 5-10x，README 没提。
>
> 修这三个 + 让 article 的 status 字段诚实一点，可以直接晋级 reusable。"

定位 = `usable`：核心路径真的能跑通且产出有质量，但 README 至少 3 处承诺没兑现 —— 评测原则说弱 plan 不能给强 verdict，README 撒谎更不能给强 verdict。

## 三 repo 横向对比

| Repo | Bucket | 核心路径 | 文档 ↔ 代码 | Failure transparency | Mac 性能 |
|------|--------|---------|-------------|---------------------|----------|
| content-downloader | `usable` | 1/4 平台 | ❌ silent fail | ❌ wechat/x 假装成功 | n/a |
| frontend-slides | `reusable` | A 层全过 | ✅ 100% 对齐 | ✅ 优秀 | ✅ |
| **content-extractor** | **`usable`** | **视频强、audio 假** | **❌ 3 处不对齐** | **✅ 优秀** | **❌ CPU-only** |

content-extractor 的 failure transparency 比 content-downloader 强一档，但 README 不诚实程度也更明显（3 处 vs 主要是 silent fail）。

## Remaining Risks

1. **Image / gallery adapter 完全没测。** 占了 4/4 adapter 中的 50%，本次 eval 没碰。
2. **长视频实战未验证。** 170MB 视频被 Mac CPU 卡死，没拿到实际行为数据；hallucination 检测能否真的触发也没验证。
3. **多语言 / 多口音稳定性未知。** 只测了中文（含部分英文混读）。
4. **Test_llm.py 不修，CI/CD 完全没用。** 任何 contributor 第一步 `pytest` 就 fail。
5. **Pipeline 集成时的脏数据扩散。** 上游 content-downloader 写 0 字节文件 + 这里 status="ok" → 下游消费者不知道这条 item 是空的。

## Recommended Next Actions

按优先级：

1. **修 audio adapter（或从 README 删掉）**（最高）：
   - 选项 A（推荐）：在 cli.py auto-wrap 时把音频文件直接当 video 处理（faster-whisper 接受 audio 文件），content_type 设成 'video'
   - 选项 B：加一个真正的 audio adapter，复用 video pipeline
   - 选项 C：从 README `bare_file_support` 删掉所有音频扩展名 —— 但这是缩水
2. **修 tests/test_llm.py 的 ImportError**：删掉对 `LLMRateLimitError` 的引用，或在 llm.py 里加回这个 class（取决于历史意图）。
3. **加 mlx-whisper 作为 Mac 默认 backend**：通过 `--whisper-backend mlx|faster-whisper` flag 让 Mac 用户能用 GPU。或者至少在 README 加一段 "Mac users: install `mlx-whisper` separately for 5-10x speedup"。
4. **让 extraction_status 诚实**：empty input → status="empty"；LLM 失败 → status="degraded"；现在的 "ok" 在 0-byte 输入上有歧义。
5. **测 image / gallery adapter** —— 本次 eval 完全没碰。
6. **修完后重跑此 eval，目标晋级 `reusable`**。
