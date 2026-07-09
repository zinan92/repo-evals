# Final Verdict

## Repo

- **Name**: op7418/guizang-material-illustration
- **Version tested**: main@cf26e19 (2026-07-07, depth-1 isolated clone)
- **Date**: 2026-07-09
- **Archetype**: prompt-skill
- **Layer**: molecule
- **Score**: 53 /100  (from `verdict_calculator.py`)
- **Category**: 🛠 Available / 可使用
- **Tier**: try (≥50) 🧪 试一下

## Plain English

- Outcome if adopted: 内容团队(Vera)得到一套写得很扎实的"配图层"提示词系统——把文章/数据/丑图表变成带中文标签的归藏材质解释图、逐值保真的材质化图表、参考辅助图,再交给排版 skill 拼成成品。
- Regret scenario: 它的核心产物是外部图像模型出的图,本次**无凭证、出图质量未实测**;加上**无 LICENSE(默认保留所有权利)**且仓库**才 2 天新、单一作者**——把它当成"已验证、可长期依赖"的生产资产,而不是"先隔离试用"的候选,就会后悔。

## Why This Score

用户可见价值:一套让 agent 稳定产出"能讲清楚意思的中心配图"的提示词与协议库。静态支撑层实测很强——SKILL.md 引用的 6 个 reference + 提示词模板全部解析得到、彼此一致;chart-beautify 有逐值 Required-accuracy 的"不编数据"协议;qa-checklist 覆盖真实翻车点;配图层×排版层边界清楚。但真正交给用户的是一张**外部图像模型**渲染的图,本次无凭证无法验证其质量,所以分数被"核心未测 + evidence=partial + molecule"三重上限压在 available,并因无许可证扣分。

### Top 3 score drivers

- **+10 静态 claim**:支撑层强——结构关(critical)通过 +5、3 个 high 通过 +6、触发设计 passed_with_concerns +1;但核心"可用图片"claim 是 critical 且 untested −2 → 净 +10(占满一半正分)。
- **+5 维护证据**:只有"近 90 天活跃"给分(+5);release_pipeline=0、eval_discipline=1(仅 ad-hoc QA)、无双语 README 均不给分 —— 这正是"极新 + 单作者"的真实画像。
- **0 生态 / −2 无许可证**:385 stars 差一点没够 ≥1000 档 → 生态 +0;NO LICENSE → −2 罚分;molecule 无 layer 加成。这三项把它稳稳压在 Available/Risky 交界。

### Core outcome
可观测(静态)有效:skill 结构完整、references 一致、提示词外壳可直接填空、图表数据协议严格、QA 清单齐备、边界清晰 —— 即"能产出一份约束齐全的出图计划"这件事成立。
未观测(核心):外部图像模型是否真能出可用、on-brand 的图;图内中文标签是否清晰不乱码(图像模型公认难点);图表是否逐值保真;参考图是否事实准确;缩到卡片尺寸是否仍可读。五项核心 claim 全部 untested —— 本次无图像模型凭证。

### Scenario breadth
0 个真实出图题材被实测(无凭证)。静态覆盖面很广(工作/教育/人文/图表/参考五大类、10 种图型、5 种主题色),但都停在"文档承诺"层。→ evidence_completeness = partial。

### Repeatability
文档层可复现:引用完整性、references 一致性、模板/协议存在性,同样检查同样结论。出图层不可复现性未知:图像模型本身非确定性,且无凭证未跑,连一次 baseline 都没有。

### Failure transparency
skill 自带失败处理设计(标签错→label-repair 重生、数据错→拒收重生、参考只补事实),但这些都依赖人真去执行 qa-checklist;没有确定性校验兜底,错的中文字或错的数字若无人抓出就会静默交付。

## What Would Move The Score Up

1. (~+3 并解锁 available 上限的证据基础) 带真实图像模型凭证跑一组题材(机制图/图表美化/带中文标签图),按 qa-checklist 打分:标签正确率、数据保真、裁切 → core_layer_tested 从 false 抬起、evidence partial→portable。
2. (~+2) 上游补 LICENSE(或团队书面接受"仅内部自用"的 all-rights-reserved 结论)→ 去掉 −2 罚分、清掉采用阻断旗标。
3. (~+3 生态) 观察是否越过 1000 stars / 是否出现第二个 committer —— 生态与 bus-factor 同时改善再谈对外依赖(时间验证,非我方可控)。

## Remaining Risks

| Risk | Severity | Impact | Mitigation |
|---|---|---|---|
| NO LICENSE(默认保留所有权利) | 高 | 采用/修改/再分发无法律授权,内部试用也是灰区 | 促上游补证;在此之前仅隔离试用 + 书面记录内部自用结论 |
| 核心出图质量未实测(image-model-dependent) | 高 | "可用/on-brand/标签正确"全未验证,非技术读者易把"文档好"当"产物好" | 用真实凭证跑 qa-checklist 实测,再决定是否主用 |
| 图内中文标签乱码风险 | 中高 | 招牌功能恰是图像模型的已知弱点,真实成功率未知 | 实测正确率;label-repair 重生是否收敛 |
| 仓库极新 + 单作者(bus-factor 1) | 中 | 2 天新、约 5 commits、单日推送,长期维护未验 | 观察 2-4 周维护度,先别对外强依赖 |
| 数据"不编"无确定性兜底 | 中 | 图表数字靠提示词纪律 + 人工 QA,漏检即交付错数 | 强制人过 chart QA;高风险数据图人工核对 |

## Verdict

采用为 **Vera(视觉/配图 Manager)的隔离试用工具**,归入其 **解释图 / 图表美化 / 参考辅助配图** 主线(park-content-v1 的 05_production 主、06_assembly 衔接)。作为该 lane 的 **primary 试用工具**,但**暂不授予正式 owner 身份**:两道闸门必须先过 ——(a) 上游补 LICENSE,或团队书面接受 all-rights-reserved 的"仅内部自用"结论;(b) 用真实图像模型凭证按 qa-checklist 实测出图质量(尤其图内中文标签正确率)。在此之前,它是 Vera 手里一件"先装上、按 QA 把关、别放进对外强依赖"的候选工具,不是新角色、也不是已验证的生产资产。与同作者的 guizang-social-card-skill 组合使用(本 repo 出中心图 → social-card 排整卡)。
