#!/usr/bin/env python3
"""
layers.py — atom / molecule / compound layer model for repo-evals.

Layers describe a repo's *composition depth*, orthogonal to archetypes
which describe shape (CLI, adapter, orchestrator, ...).

This module is consumed by:
  - generate_dashboard.py     to render layer-specific eval sections
                              in the operator dashboard (English only —
                              picks .en off bilingual fields).
  - render_verdict_html.py    to render the bilingual editorial dossier
                              with the full {en, zh} content.
  - verdict_calculator.py     to apply layer ceiling rules (additive to
                              the existing hybrid-cap rule).
  - tests/test_layers.py      contract tests.

Bilingual content uses ``{"en": "...", "zh": "..."}`` dicts everywhere.
The render_verdict_html.py i18n helper picks the right half at runtime
via the language toggle; the dashboard picks .en.

See docs/LAYERS.md for the framework definition.
"""

from __future__ import annotations

from dataclasses import dataclass


LAYER_ATOM = "atom"
LAYER_MOLECULE = "molecule"
LAYER_COMPOUND = "compound"

LAYERS: tuple[str, ...] = (LAYER_ATOM, LAYER_MOLECULE, LAYER_COMPOUND)

# Default layer suggested by archetype. Authors override in repo.yaml.
ARCHETYPE_DEFAULT_LAYER: dict[str, str] = {
    "pure-cli": LAYER_ATOM,
    "adapter": LAYER_ATOM,
    "api-service": LAYER_MOLECULE,
    "prompt-skill": LAYER_ATOM,
    "hybrid-skill": LAYER_MOLECULE,
    "orchestrator": LAYER_COMPOUND,
    # Sequences multiple MCP tool calls with documented order/rules — molecule.
    "mcp-enhancement": LAYER_MOLECULE,
}


# --- Bilingual helpers ---------------------------------------------------


# Human-readable layer labels used in chrome (badges, headings).
LAYER_LABELS: dict[str, dict[str, str]] = {
    LAYER_ATOM: {"en": "Atom", "zh": "原子"},
    LAYER_MOLECULE: {"en": "Molecule", "zh": "分子"},
    LAYER_COMPOUND: {"en": "Compound", "zh": "复合物"},
    "unknown": {"en": "Unknown", "zh": "未声明"},
}

LAYER_SUMMARIES: dict[str, dict[str, str]] = {
    LAYER_ATOM: {
        "en": "Single responsibility. Same input → same output. No skill-level callouts.",
        "zh": "单一职责。同样输入产出同样输出。不调用其他 skill 级单元。",
    },
    LAYER_MOLECULE: {
        "en": "2–10 atoms wired by predefined orchestration. No runtime LLM routing.",
        "zh": "2–10 个原子，按预定义编排串起来。运行时不让 LLM 临时决定路由。",
    },
    LAYER_COMPOUND: {
        "en": "Multiple molecules; call graph decided at runtime by an LLM or human.",
        "zh": "多个分子；调用图在运行时由 LLM 或人决定。",
    },
    "unknown": {
        "en": "Layer not declared in repo.yaml — falls back to archetype heuristic.",
        "zh": "repo.yaml 未声明 layer — 用 archetype 启发式默认值兜底。",
    },
}


@dataclass(frozen=True)
class EvalDimension:
    """A single eval dimension that an evaluator should check."""

    key: str
    question_en: str
    question_zh: str

    @property
    def question(self) -> dict[str, str]:
        return {"en": self.question_en, "zh": self.question_zh}


@dataclass(frozen=True)
class CompoundExperiment:
    """A scenario template the operator runs by hand and observes."""

    title_en: str
    title_zh: str
    system_prompt_en: str
    system_prompt_zh: str
    watch_for_en: tuple[str, ...]
    watch_for_zh: tuple[str, ...]
    expected_sub_molecules_en: str
    expected_sub_molecules_zh: str

    @property
    def title(self) -> dict[str, str]:
        return {"en": self.title_en, "zh": self.title_zh}

    @property
    def system_prompt(self) -> dict[str, str]:
        return {"en": self.system_prompt_en, "zh": self.system_prompt_zh}

    @property
    def watch_for(self) -> tuple[dict[str, str], ...]:
        # Pad shorter list to the longer one; zip only as many as both have.
        return tuple(
            {"en": en, "zh": zh}
            for en, zh in zip(self.watch_for_en, self.watch_for_zh)
        )

    @property
    def expected_sub_molecules(self) -> dict[str, str]:
        return {
            "en": self.expected_sub_molecules_en,
            "zh": self.expected_sub_molecules_zh,
        }


# --- Atom dimensions ----------------------------------------------------

ATOM_DIMENSIONS: tuple[EvalDimension, ...] = (
    EvalDimension(
        key="input_contract",
        question_en="Does the atom reject malformed input with a clear, actionable error?",
        question_zh="原子在收到非法输入时，是否抛出一个清晰、可操作的错误？",
    ),
    EvalDimension(
        key="output_contract",
        question_en="Does the output shape match what the README/SKILL.md claims?",
        question_zh="输出的结构是否与 README/SKILL.md 的承诺一致？",
    ),
    EvalDimension(
        key="determinism",
        question_en="Same input → same output within stated tolerance. (LLM atoms: structurally equivalent, not byte-equal.)",
        question_zh="同样输入产出同样输出（容差内）。LLM 原子的容差是「结构等价」，不是字节相等。",
    ),
    EvalDimension(
        key="idempotence",
        question_en="Re-running with the same input produces the same observable end state.",
        question_zh="同样输入重复运行，最终可观察状态保持一致。",
    ),
    EvalDimension(
        key="no_skill_callouts",
        question_en="Does the atom avoid invoking other documented skills? Primitives only (LLM API, stdlib, OS).",
        question_zh="原子是否避免调用其他 skill？只能调用 primitive（LLM API、stdlib、OS）。",
    ),
    EvalDimension(
        key="failure_mode_clarity",
        question_en="Does each documented failure mode produce a distinct, recognisable error?",
        question_zh="每一种文档化的失败模式，是否都对应一个独特且可识别的错误？",
    ),
)


# --- Molecule dimensions ------------------------------------------------

MOLECULE_DIMENSIONS: tuple[EvalDimension, ...] = (
    EvalDimension(
        key="workflow_correctness",
        question_en="Does an end-to-end happy path run from initial input to final output?",
        question_zh="从初始输入到最终输出，端到端 happy path 能跑通吗？",
    ),
    EvalDimension(
        key="declared_call_graph",
        question_en="Are the atoms the molecule documents as using actually the ones it calls? No undocumented hidden dependencies.",
        question_zh="分子文档里声明依赖的原子，是否就是它实际调用的原子？没有未文档化的隐藏依赖？",
    ),
    EvalDimension(
        key="stop_conditions",
        question_en="Do documented stop conditions (success, max-retries, timeout) trigger and halt cleanly?",
        question_zh="文档化的停止条件（成功 / 重试上限 / 超时）是否真的触发并干净退出？",
    ),
    EvalDimension(
        key="handoff_points",
        question_en="When the molecule should hand back to a human, does it do so at the documented trigger?",
        question_zh="分子需要把控制权交还给人时，是否按文档化的触发点执行？",
    ),
    EvalDimension(
        key="atom_evidence",
        question_en="Does every declared atom dependency have a passing atom-level eval (referenced or co-located)?",
        question_zh="每一个声明依赖的原子，是否都有对应的、通过的 atom 级评测（引用或同仓）？",
    ),
    EvalDimension(
        key="error_propagation",
        question_en="Does a downstream atom failure surface at the molecule boundary with enough info to act?",
        question_zh="下游原子失败时，错误是否在分子边界处响亮地冒泡出来，并带足够信息让人定位？",
    ),
    EvalDimension(
        key="partial_failure_handling",
        question_en="When one atom fails, does the molecule avoid silently producing an incomplete 'success'?",
        question_zh="某个原子失败时，分子是否避免静默输出一个看似「成功」其实不完整的产物？",
    ),
)


# --- Compound dimensions ------------------------------------------------

COMPOUND_DIMENSIONS: tuple[EvalDimension, ...] = (
    EvalDimension(
        key="goal_achievement",
        question_en="In N real scenarios, does the system reach a useful end state — not just 'ran without error'?",
        question_zh="在 N 个真实场景里，系统是否真的达到了有用的终态 —— 而不仅仅是「跑完没报错」？",
    ),
    EvalDimension(
        key="direction_judgment",
        question_en="When the goal is ambiguous, does the system ask, pick a reasonable default, or wedge?",
        question_zh="目标不明确时，系统是会反问、合理默认，还是卡死？",
    ),
    EvalDimension(
        key="quality_judgment",
        question_en="Does the system stop when output is good enough, instead of overshooting or stopping too early?",
        question_zh="输出「足够好」时系统是否会停下来？还是会过度生产或过早停下？",
    ),
    EvalDimension(
        key="meaningful_autonomy",
        question_en="When left to drive itself, does it actually make progress, or does it spin / loop / hallucinate?",
        question_zh="放手让它自己跑，是真有进展，还是空转 / 死循环 / 幻觉？",
    ),
    EvalDimension(
        key="handoff_timing",
        question_en="When the system asks for help, is that the right moment?",
        question_zh="系统找人介入时，时机是不是恰到好处？",
    ),
    EvalDimension(
        key="observed_call_graph",
        question_en="Was the call graph recorded during each scenario? Does each sub-molecule called have a passing molecule-level eval?",
        question_zh="每个场景跑完，调用图是否被记录下来？被调用到的每个子分子，是否都有通过的 molecule 级评测？",
    ),
    EvalDimension(
        key="failure_recovery",
        question_en="When a sub-call fails, does the LLM adapt (try alternative, ask user) or wedge?",
        question_zh="子调用失败时，LLM 是会调整路径（换方案 / 问用户），还是卡死？",
    ),
)


# --- Compound experiments ----------------------------------------------

GENERIC_COMPOUND_EXPERIMENTS: tuple[CompoundExperiment, ...] = (
    CompoundExperiment(
        title_en="Happy-path multi-step request",
        title_zh="多步骤 happy path 请求",
        system_prompt_en=(
            "Give the system a realistic multi-step request that obviously "
            "needs more than one sub-skill to complete (e.g., 'find X, "
            "summarise it, and post the result'). Do not coach it on which "
            "tool to use."
        ),
        system_prompt_zh=(
            "给系统一个真实的多步骤请求，明显需要不止一个子技能才能完成"
            "（比如「找到 X，总结它，把结果发出来」）。不要提示它该用哪个工具。"
        ),
        watch_for_en=(
            "Does it pick the right sub-molecules without prompting?",
            "Does it complete end-to-end with a useful artefact (not just 'done')?",
            "Does it skip steps or invent steps that were not asked for?",
        ),
        watch_for_zh=(
            "不提示的情况下，它是否选对了子分子？",
            "是否端到端完成，并产出有用的成果（不是只回一个「完成」）？",
            "是否漏步骤、或自己加上没被要求的步骤？",
        ),
        expected_sub_molecules_en="TBD — observe",
        expected_sub_molecules_zh="待定 —— 观察",
    ),
    CompoundExperiment(
        title_en="Ambiguous goal — does it ask or assume?",
        title_zh="目标模糊 —— 反问还是默认？",
        system_prompt_en=(
            "Give the system an under-specified request (e.g., 'clean this "
            "up' with no further detail). Wait and see what it does."
        ),
        system_prompt_zh=(
            "给系统一个非常模糊的请求（比如「清理一下这个」，不给任何细节），"
            "然后等着看它怎么做。"
        ),
        watch_for_en=(
            "Does it ask a clarifying question, or silently pick a direction?",
            "If it picks a direction, is the choice reasonable for a default user?",
            "Does it avoid destructive actions until the ambiguity is resolved?",
        ),
        watch_for_zh=(
            "它会反问澄清，还是默默选一条路？",
            "如果它默认选了方向，对一个普通用户来说这个默认是不是合理？",
            "在模糊解除前，它是否避免了破坏性操作？",
        ),
        expected_sub_molecules_en="TBD — observe",
        expected_sub_molecules_zh="待定 —— 观察",
    ),
    CompoundExperiment(
        title_en="Induced sub-skill failure — does it recover?",
        title_zh="人为制造子技能失败 —— 它会恢复吗？",
        system_prompt_en=(
            "Run a normal request, but arrange for one sub-skill to fail "
            "(e.g., revoke a credential, point at a broken URL, fill a "
            "queue). Observe the response."
        ),
        system_prompt_zh=(
            "跑一个正常请求，但人为让某个子技能失败（比如撤销凭据、指向坏链接、"
            "塞满队列），观察系统反应。"
        ),
        watch_for_en=(
            "Does the failure surface clearly, or get hidden behind a fake 'success'?",
            "Does the system attempt an alternative path or escalate to the human?",
            "Does it avoid wedging in a retry loop?",
        ),
        watch_for_zh=(
            "失败是否被清楚地暴露出来？还是被一个假的「成功」盖住？",
            "系统是会换条路走，还是把问题升级给人？",
            "它是否避免陷入死循环式的重试？",
        ),
        expected_sub_molecules_en="TBD — observe",
        expected_sub_molecules_zh="待定 —— 观察",
    ),
    CompoundExperiment(
        title_en="Long-horizon autonomy",
        title_zh="长时间自主运行",
        system_prompt_en=(
            "Give the system a goal that takes 10+ minutes of unattended "
            "work (e.g., 'audit the past week and produce a summary'). "
            "Leave it alone for 15 minutes."
        ),
        system_prompt_zh=(
            "给系统一个需要 10 分钟以上无人值守工作的目标（比如「审计过去一周"
            "并产出一份总结」），然后离开 15 分钟。"
        ),
        watch_for_en=(
            "Did it produce a real artefact, or did it spin / lose context?",
            "Are the intermediate steps sensible, or did it hallucinate?",
            "Did it know when to stop, or did it over-shoot the goal?",
        ),
        watch_for_zh=(
            "回来时是否产出了真实成果？还是空转 / 丢失上下文？",
            "中间步骤是否合理？有没有幻觉？",
            "它是否知道什么时候该停？还是越过了目标？",
        ),
        expected_sub_molecules_en="TBD — observe",
        expected_sub_molecules_zh="待定 —— 观察",
    ),
)

ORCHESTRATOR_COMPOUND_EXPERIMENTS: tuple[CompoundExperiment, ...] = (
    CompoundExperiment(
        title_en="Routing correctness across all downstreams",
        title_zh="所有下游的路由正确性",
        system_prompt_en=(
            "Send one request that should fan out to every documented "
            "downstream (one input per area). Observe the routing log."
        ),
        system_prompt_zh=(
            "发起一个请求，让它分发到每一个文档化的下游（每个 area 一个输入），"
            "观察路由日志。"
        ),
        watch_for_en=(
            "Did each input land at the correct downstream?",
            "Are downstream call traces visible in the orchestrator log?",
            "Do partial failures stop unrelated downstreams from running?",
        ),
        watch_for_zh=(
            "每一个输入是否都被路由到正确的下游？",
            "在 orchestrator 日志里，下游调用是否可追踪？",
            "部分失败时，是否影响到了不相关的下游？",
        ),
        expected_sub_molecules_en="One per documented downstream area.",
        expected_sub_molecules_zh="每个文档化的下游 area 一个。",
    ),
)


# --- Public API ---------------------------------------------------------


def normalise_layer(value: str | None) -> str:
    """Return a known layer string, or 'unknown' if the value is missing/invalid."""

    if value is None:
        return "unknown"
    canonical = value.strip().lower()
    if canonical in LAYERS:
        return canonical
    return "unknown"


def default_layer_for_archetype(archetype: str | None) -> str:
    """Suggest a layer for a given archetype. Returns 'unknown' if none."""

    if archetype is None:
        return "unknown"
    return ARCHETYPE_DEFAULT_LAYER.get(archetype.strip().lower(), "unknown")


def applicable_levels(layer: str) -> tuple[str, ...]:
    """Levels whose dimensions apply to this layer.

    atom     -> (atom,)
    molecule -> (atom, molecule)
    compound -> (atom, molecule, compound)
    unknown  -> ()
    """

    layer = normalise_layer(layer)
    if layer == LAYER_ATOM:
        return (LAYER_ATOM,)
    if layer == LAYER_MOLECULE:
        return (LAYER_ATOM, LAYER_MOLECULE)
    if layer == LAYER_COMPOUND:
        return (LAYER_ATOM, LAYER_MOLECULE, LAYER_COMPOUND)
    return ()


def dimensions_for_level(level: str) -> tuple[EvalDimension, ...]:
    if level == LAYER_ATOM:
        return ATOM_DIMENSIONS
    if level == LAYER_MOLECULE:
        return MOLECULE_DIMENSIONS
    if level == LAYER_COMPOUND:
        return COMPOUND_DIMENSIONS
    return ()


def experiments_for(layer: str, archetype: str | None) -> tuple[CompoundExperiment, ...]:
    """Compound experiments for a repo. Empty for non-compound layers."""

    if normalise_layer(layer) != LAYER_COMPOUND:
        return ()
    extra: tuple[CompoundExperiment, ...] = ()
    if archetype and archetype.strip().lower() == "orchestrator":
        extra = ORCHESTRATOR_COMPOUND_EXPERIMENTS
    return GENERIC_COMPOUND_EXPERIMENTS + extra


def layer_label(layer: str) -> dict[str, str]:
    """Bilingual label for a layer (e.g., {'en': 'Compound', 'zh': '复合物'})."""

    layer = normalise_layer(layer)
    return LAYER_LABELS[layer]


def layer_summary(layer: str) -> dict[str, str]:
    """Bilingual one-line description for a layer."""

    layer = normalise_layer(layer)
    return LAYER_SUMMARIES[layer]
