# Final Verdict

## Repo

- **Name**: isjiamu/gzh-design-skill
- **Version tested**: main@HEAD (2026-07-08 push, v1.0.0), commit ba1f417
- **Date**: 2026-07-09
- **Archetype**: hybrid-skill
- **Layer**: molecule
- **Score**: 84 /100  (from `verdict_calculator.py`)
- **Category**: 🏭 Production-ready / 可用于生产
- **Tier**: team (≥80)

## Plain English

- Outcome if adopted: 内容运营者把成稿 Markdown 一句话排成粘贴不掉格式的精致公众号 HTML，6 套主题 + 主题生成器，平台红线由脚本确定性兜底而非模型自觉。
- Regret scenario: 期待它替你写文章（它只排版）；或指望它排得「有品味」（脚本只保证平台合规，审美仍看模型发挥）；或在这个 8 天新、单一 committer 的仓库上建长期对外强依赖。

## Why This Score

核心承诺——「排出可直接粘进公众号、粘完不掉格式的 HTML」——经实测成立：两个校验脚本真能确定性区分合规/不合规，随包产物真含 122 处 `<span leaf>` 且完全合规，且我亲手用摸鱼绿组件库把 sample-article.md 装配成 section，自产物过校验 0 ERROR / 0 WARN。

### Top 3 score drivers

- +29 : 静态 claim —— 4/4 critical 全过（含 live-e2e 验证的 molecule 核心承诺），11/14 通过、0 失败。
- +12 : 维护证据 —— eval 纪律（双关卡 + eval-cases + 可验证循环）+5、近 90 天活跃 +5、双语 README +2。
- +3 / 0 : 生态 1539★ 只给 +3（代码档位 ≥1000→+3）；molecule 无 layer 加成；有真实 AGPL-3.0 → 0 罚分。

### Core outcome
可观测有效：md → 主题化、`<span leaf>` 包裹、编号章节、逐段关键词下划线的合规 section，过产物关校验；带一键复制预览页。
未观测：主题生成器第二条工作流、docx/pdf 真机归一化、跨模型一致性、真机粘进公众号编辑器的落地效果（靠校验脚本作代理指标）。

### Scenario breadth
1 套主题（摸鱼绿）× 1 篇示例文的一节，实测装配 + 校验通过；随包 6 套主题的组件库源头 lint 全过。其余 5 套、其它输入格式、其它模型未逐一实测 → evidence_completeness = portable。

### Repeatability
文件级可复现：校验脚本确定性（同输入同结论，退出码稳定）；组件库固定，合规性可重放。排版「气质」的一致性依赖模型那次发挥，未做多次/多模型重放。

## Verdict

采用。归 Joanna（内容生产）作为**工具**使用，不建新角色；Mark 建 skill card 管理，本 dossier 留作证据库。下一步最小动作：让 Joanna 用一篇真实长文跑完整 pipeline 并真机粘贴验证，把 evidence 从 portable 升到 full。
