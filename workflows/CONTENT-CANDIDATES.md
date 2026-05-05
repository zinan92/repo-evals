# Content-related repos from your stars + own — bucketed by Park content pipeline

**Source:** github.com/zinan92 (36 own + 138 starred = 174 scanned).
**Filter:** content production / distribution / scraping / understanding / generation.
**Star count = the *upstream* repo's count, not yours.** Marked **EVAL'D** when already in `repos/`.

---

## 01 信号发现 — Signal scanning

What's spiking, what's worth doing next.

### Your own
| Repo | ★ | Note |
|---|---|---|
| zinan92/intel | 1 | 情报采集; 10+ sources + LLM scoring + cross-source clustering. **Currently un-evaluated** but you've got it. Dual-placement candidate (also Trading 02). |
| zinan92/intelligence | 1 | 社交内容趋势研究引擎 → 趋势信号+方向聚类. **Strong 01 candidate.** |
| zinan92/content-intelligence | 1 | 趋势检测+爆款归因+模式识别+选题建议. **Strong 01/04 candidate** (overlaps curation). |

### Starred (high-leverage)
| Repo | ★ | Note |
|---|---|---|
| Panniantong/Agent-Reach | 18,878 | 让 AI agent 读 Twitter / Reddit / YouTube / GitHub / Bilibili / 小红书. **The clearest signal-scan tool in the corpus.** |
| rohunvora/x-research-skill | 1,109 | X/Twitter research skill: agentic search, thread following, deep-dives. |
| zarazhangrui/follow-builders | 3,722 | AI builders monitor + remix from X / YouTube. **EVAL'D** (placement still pending — currently no workflow). |
| sstklen/trump-code | 745 | AI decoding Trump's posts × stock market — niche but is signal-scanning. |

---

## 02 内容获取 — Content acquisition

Pull the raw thing down.

### Your own
| Repo | ★ | Note |
|---|---|---|
| zinan92/content-downloader | 0 | **EVAL'D 29 / 🛑 Don't use** — broken on Douyin signing. |
| zinan92/douyin-downloader | 1 | 抖音 URL → markdown 文字稿. Adjacent to content-downloader. Probably consolidate. |
| zinan92/MediaCrawler (fork) | 0 | Fork of upstream. |
| zinan92/xiaohongshu-downloader (PRIVATE) | 0 | 小红书 CLI: export/sort/transcribe/incremental. **Strong 02 candidate but private.** |

### Starred (high-leverage)
| Repo | ★ | Note |
|---|---|---|
| NanmiCoder/MediaCrawler | 48,879 | **EVAL'D 75 / 🛠 Available**, primary at 02. |
| Scrapling | 44,851 | Adaptive web scraping framework. **General-purpose 02 candidate**, not CN-specific. |
| putyy/res-downloader | 17,204 | 视频号 / 小程序 / 抖音 / 快手 / 小红书 / 直播流 / m3u8 / 酷狗 / QQ音乐. **Broadest CN downloader** — strong eval candidate. |
| Usagi-org/ai-goofish-monitor | 11,574 | **EVAL'D 69**, currently placed as reference at 02. |
| JoeanAmier/XHS-Downloader | 11,061 | 小红书账号发布 / 收藏 / 点赞 / 专辑 / 搜索 / 用户 — comprehensive. **Eval candidate** to compare with MediaCrawler's xhs path. |
| wechat-article/wechat-article-exporter | 8,930 | 微信公众号文章批量下载,导出阅读量+评论. **No real CN public-corpus alternative.** |
| jiji262/douyin-downloader | 7,533 | Douyin profile-batch + transcribe + sqlite dedupe + browser fallback. |

---

## 03 内容理解 — Content understanding

Turn raw asset into queryable text + structure.

### Your own
| Repo | ★ | Note |
|---|---|---|
| zinan92/content-extractor | 0 | **EVAL'D** (placed primary at 03). Apple Silicon mlx-whisper GPU 加速. |

### Starred (high-leverage)
| Repo | ★ | Note |
|---|---|---|
| zarazhangrui/youtube-to-ebook | — | **EVAL'D** (placed primary at 03, video→text medium). |
| jdepoix/youtube-transcript-api | 7,468 | YouTube transcript Python API. Used as primitive by other tools. |
| mixedbread-ai/mgrep | 4,115 | Semantic grep for code / images / pdfs / etc. Adjacent — searchable but not extracting. |

---

## 04 选题决策 — Topic curation

Pick what to actually make. **This is the gap stage in your current pipeline.**

### Your own
| Repo | ★ | Note |
|---|---|---|
| zinan92/intelligence | 1 | 趋势研究 → 决策报告 + 交互看板. **The closest existing 04 candidate — worth evaluating.** |
| zinan92/content-intelligence | 1 | 选题建议 + 模式识别. **Same family** — likely overlaps with intelligence; pick one as canonical. |

### Starred (high-leverage)
| Repo | ★ | Note |
|---|---|---|
| coreyhaines31/marketingskills | 26,714 | Marketing skills (CRO, copywriting, SEO, analytics, growth). Could play 04 (decide what to write) or 05 (write). |
| dontbesilent2025/dbskill | 4,200 | 商业诊断 Skills. 04-flavoured (decide angle). |

---

## 05 内容生产 — Content production

Write / generate the draft.

### Your own
| Repo | ★ | Note |
|---|---|---|
| zinan92/content-toolkit | 1 | **EVAL'D** (currently placed support at 05). |
| zinan92/content-rewriter | 0 | 抖音转录 → 小红书+公众号草稿. **Cross-platform rewriter, strong 05 candidate.** Worth evaluating. |
| zinan92/seedance-expert | 1 | 视频创意 → Seedance 2.0 prompt. **Production-side prompt-skill specialist** for video. |

### Starred (high-leverage)
| Repo | ★ | Note |
|---|---|---|
| op7418/Humanizer-zh | 6,976 | **EVAL'D 75**, primary at 05. CN cleanup. |
| blader/humanizer | 17,276 | Upstream English version of Humanizer-zh. |
| oaker-io/wewrite | 1,792 | **EVAL'D** (placed alternative at 05). 微信全流程 — bridges 05 + 07. |
| alchaincyf/nuwa-skill | 17,387 | 蒸馏思维方式 — distill how anyone thinks. **Persona/voice production layer.** |
| xixu-me/awesome-persona-distill-skills | 4,152 | Curated list of distill-style skills. Source of more candidates. |
| agenmod/immortal-skill | 682 | 数字永生 — 7 角色模板蒸馏聊天记录. |
| notdog1998/yourself-skill | 2,551 | 蒸馏自己,与其蒸馏别人. |
| FujiwaraChoki/MoneyPrinterV2 | 30,372 | "Automate money making" — content auto-generation + distribution. Spans 05+06+07. |

---

## 06 成品组装 — Asset assembly

Wrap into a publishable medium-specific format.

### Your own
| Repo | ★ | Note |
|---|---|---|
| zinan92/videocut | 14 | AI 口播视频编辑: 去废话+字幕+金句+拆条+封面+变速. **Strong 06 candidate (video medium).** Worth evaluating. |
| zinan92/AI-videos | 4 | AI 虚拟人物换装 + 动作迁移 — PNG + MP4 → 成品 MP4 + JSON. **Strong 06 candidate (video, virtual-character medium).** |

### Starred (high-leverage)
| Repo | ★ | Note |
|---|---|---|
| slidevjs/slidev | 46,211 | The reference deck-generator. Slot at 06 (medium = presentation). |
| zarazhangrui/frontend-slides | 16,438 | **EVAL'D 62**, primary at 06 (presentation). |
| chenglou/pretext | 46,254 | Fast text layout. 06-primitive (pretext under your slides). |
| black-forest-labs/flux | 25,492 | FLUX image-gen models. 06-primitive (image medium). |
| AIDC-AI/Pixelle-Video | 11,493 | AI 全自动短视频引擎. **Direct competitor to videocut + remotion-skills** — eval-worthy. |
| siddharthvaddem/openscreen | 34,828 | Screen-recording (Screen Studio alt). 06 (screencast medium). |
| webadderallorg/Recordly | 12,804 | Polished screen recording (Mac/Win/Linux). 06 (screencast medium). |
| THU-MAIC/OpenMAIC | 16,804 | **EVAL'D 75**, primary at 06 (interactive-classroom). |
| remotion-dev/skills | 3,022 | **EVAL'D 72**, primary at 06 (programmatic video). |
| greensock/gsap-skills | 3,083 | GSAP animation skills. 06-primitive (web animation). |
| pexoai/pexo-skills | 865 | Agent Skills for content creation — images / audio / video. **Multi-medium 06 catalog.** |
| zarazhangrui/personalized-podcast | — | **EVAL'D**, primary at 06 (audio). |
| zarazhangrui/codebase-to-course | — | **EVAL'D**, primary at 06 (course). |
| Jamailar/RedBox | 869 | 小红书 AI 创作工作台. 06+07 hybrid. **EVAL'D** (placement pending). |
| cclank/lanshu-waytovideo | 247 | AGI 视频化路径. Niche. |
| AAAAAAAJ/WaytoAGI-CLI | 38 | WaytoAGI CLI — your team's content channel? |
| NoizAI/skills | 490 | 让 bot 用 human vibe 说话 — TTS / voice production. 06 (audio). |

---

## 07 分发 — Distribution

Push to platforms.

### Your own
| Repo | ★ | Note |
|---|---|---|
| zinan92/content-workbench | 0 | 抖音内容跨平台分发工作台 — 发现 / 筛选 / 下载 / 转录 / 逐平台编辑草稿. **Spans 01-07, but 07 is the headline.** |

### Starred (high-leverage)
| Repo | ★ | Note |
|---|---|---|
| dreammis/social-auto-upload | 10,664 | **EVAL'D 42 / ⚠️ Risky**, primary at 07. |
| geekjourneyx/md2wechat-skill | 2,005 | **EVAL'D 91 / 🏭 Production-ready**, primary at 07 (wechat). |
| autoclaw-cc/xiaohongshu-skills | 1,193 | **EVAL'D**, support at 07 (xhs). |
| white0dew/XiaohongshuSkills | 2,686 | **Different xhs skill** — 自动发布 + 自动评论 + 自动检索. Eval-worthy alternative to autoclaw-cc/xiaohongshu-skills. |
| oaker-io/wewrite | 1,792 | **EVAL'D** at 05; also has 07-flavoured publish step. Could be dual-stage placed. |
| zhjiang22/openclaw-xhs | 95 | OpenClaw-specific xhs MCP integration. |
| larksuite/cli | 9,262 | Lark / Feishu CLI for messengers / docs. 07 (Lark / Feishu medium) for B2B distribution. |

---

## 08 反馈学习 — Feedback learning

Track performance, close the loop.

### Your own
| Repo | ★ | Note |
|---|---|---|
| zinan92/cc-control-tower (PRIVATE) | 0 | 内容生产 pipeline DAG 监控面板 — DAG canvas + SSE status + execute/retry/skip. **08-flavoured pipeline observability.** |

### Starred
- **GAP** — no clean public-corpus 08 candidate yet. The closest: tools that *track* X/Twitter or YouTube performance (none in your stars at scale). Real feedback-learning analytics are usually SaaS (not OSS), so this stage is structurally hard to fill from public-corpus.

---

## Summary — what's worth evaluating next

### Top eval candidates (currently un-evaluated, high impact)
1. **zinan92/intelligence** + **zinan92/content-intelligence** — both fill the 04 curation gap. Eval one of them, decide which is canonical.
2. **zinan92/videocut** + **zinan92/AI-videos** — both are 06 video assembly with different focus. Strong own-corpus 06 reinforcement.
3. **putyy/res-downloader** — 17K stars, broadest CN downloader; eval as alternative to MediaCrawler at 02.
4. **wechat-article/wechat-article-exporter** — 9K stars, fills WeChat-source 02 gap that MediaCrawler doesn't cover.
5. **zinan92/content-rewriter** — 05 cross-platform rewriter; closes the gap between content-toolkit (broad) and Humanizer-zh (CN cleanup).
6. **AIDC-AI/Pixelle-Video** — 11K stars, direct 06 video competitor. Worth comparison.
7. **alchaincyf/nuwa-skill** — 17K stars, persona-distillation production skill. Different angle than Humanizer.
8. **Panniantong/Agent-Reach** — 18K stars, the cleanest 01 signal-scan tool in the corpus.

### Lower priority but on the radar
- **white0dew/XiaohongshuSkills** (2.6K) — xhs auto-publish, alternative to autoclaw-cc/xiaohongshu-skills
- **JoeanAmier/XHS-Downloader** (11K) — xhs downloader specialist, alternative to MediaCrawler's xhs path
- **slidevjs/slidev** (46K) — reference deck-generator, alternative to frontend-slides at 06
- **Recordly + openscreen** — screencast 06 medium, currently no candidate

### Repos that span multiple stages (hard to single-place)
- **zinan92/content-workbench** — 01 → 07 spans the whole pipeline
- **MoneyPrinterV2** (30K) — 05 + 06 + 07 (write / make / publish)
- **Jamailar/RedBox** (869, EVAL'D) — 06 + 07 xhs creator workspace

### Gaps that won't be filled by public corpus (structurally)
- **08 反馈学习** — analytics is mostly SaaS / proprietary, not OSS. You'd build this yourself or use platform analytics directly.
- **04 选题决策** — only your own intelligence / content-intelligence really fit; market is light here.

---

**Total content-related from this scan: ~50-60 repos**.
About **16 already evaluated** (placed in workflow), **8-10 high-priority eval candidates** (above), and **~30 reference / lower-priority** that fit a stage but aren't urgent.
