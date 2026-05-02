#!/usr/bin/env python3
"""
layers.py — atom / molecule / compound layer model for repo-evals.

Layers describe a repo's *composition depth*, orthogonal to archetypes
which describe shape (CLI, adapter, orchestrator, ...).

This module is consumed by:
  - generate_dashboard.py   to render layer-specific eval sections
  - verdict_calculator.py   to apply layer ceiling rules (additive to
                            the existing hybrid-cap rule)
  - tests/test_layers.py    contract tests

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


@dataclass(frozen=True)
class EvalDimension:
    """A single eval dimension that an evaluator should check."""

    key: str
    question: str


@dataclass(frozen=True)
class CompoundExperiment:
    """A scenario template the operator runs by hand and observes."""

    title: str
    system_prompt: str
    watch_for: tuple[str, ...]
    expected_sub_molecules: str  # free-form: "TBD — observe" is valid


# --- Atom ----------------------------------------------------------------

ATOM_DIMENSIONS: tuple[EvalDimension, ...] = (
    EvalDimension(
        key="input_contract",
        question="Does the atom reject malformed input with a clear, actionable error?",
    ),
    EvalDimension(
        key="output_contract",
        question="Does the output shape match what the README/SKILL.md claims?",
    ),
    EvalDimension(
        key="determinism",
        question="Same input → same output within stated tolerance. (LLM atoms: structurally equivalent, not byte-equal.)",
    ),
    EvalDimension(
        key="idempotence",
        question="Re-running with the same input produces the same observable end state.",
    ),
    EvalDimension(
        key="no_skill_callouts",
        question="Does the atom avoid invoking other documented skills? Primitives only (LLM API, stdlib, OS).",
    ),
    EvalDimension(
        key="failure_mode_clarity",
        question="Does each documented failure mode produce a distinct, recognisable error?",
    ),
)


# --- Molecule ------------------------------------------------------------

MOLECULE_DIMENSIONS: tuple[EvalDimension, ...] = (
    EvalDimension(
        key="workflow_correctness",
        question="Does an end-to-end happy path run from initial input to final output?",
    ),
    EvalDimension(
        key="declared_call_graph",
        question="Are the atoms the molecule documents as using actually the ones it calls? No undocumented hidden dependencies.",
    ),
    EvalDimension(
        key="stop_conditions",
        question="Do documented stop conditions (success, max-retries, timeout) trigger and halt cleanly?",
    ),
    EvalDimension(
        key="handoff_points",
        question="When the molecule should hand back to a human, does it do so at the documented trigger?",
    ),
    EvalDimension(
        key="atom_evidence",
        question="Does every declared atom dependency have a passing atom-level eval (referenced or co-located)?",
    ),
    EvalDimension(
        key="error_propagation",
        question="Does a downstream atom failure surface at the molecule boundary with enough info to act?",
    ),
    EvalDimension(
        key="partial_failure_handling",
        question="When one atom fails, does the molecule avoid silently producing an incomplete 'success'?",
    ),
)


# --- Compound ------------------------------------------------------------

COMPOUND_DIMENSIONS: tuple[EvalDimension, ...] = (
    EvalDimension(
        key="goal_achievement",
        question="In N real scenarios, does the system reach a useful end state — not just 'ran without error'?",
    ),
    EvalDimension(
        key="direction_judgment",
        question="When the goal is ambiguous, does the system ask, pick a reasonable default, or wedge?",
    ),
    EvalDimension(
        key="quality_judgment",
        question="Does the system stop when output is good enough, instead of overshooting or stopping too early?",
    ),
    EvalDimension(
        key="meaningful_autonomy",
        question="When left to drive itself, does it actually make progress, or does it spin / loop / hallucinate?",
    ),
    EvalDimension(
        key="handoff_timing",
        question="When the system asks for help, is that the right moment?",
    ),
    EvalDimension(
        key="observed_call_graph",
        question="Was the call graph recorded during each scenario? Does each sub-molecule called have a passing molecule-level eval?",
    ),
    EvalDimension(
        key="failure_recovery",
        question="When a sub-call fails, does the LLM adapt (try alternative, ask user) or wedge?",
    ),
)


# --- Compound experiments (generic; archetype-aware where useful) -------

GENERIC_COMPOUND_EXPERIMENTS: tuple[CompoundExperiment, ...] = (
    CompoundExperiment(
        title="Happy-path multi-step request",
        system_prompt=(
            "Give the system a realistic multi-step request that obviously "
            "needs more than one sub-skill to complete (e.g., 'find X, "
            "summarise it, and post the result'). Do not coach it on which "
            "tool to use."
        ),
        watch_for=(
            "Does it pick the right sub-molecules without prompting?",
            "Does it complete end-to-end with a useful artefact (not just 'done')?",
            "Does it skip steps or invent steps that were not asked for?",
        ),
        expected_sub_molecules="TBD — observe",
    ),
    CompoundExperiment(
        title="Ambiguous goal — does it ask or assume?",
        system_prompt=(
            "Give the system an under-specified request (e.g., 'clean this "
            "up' with no further detail). Wait and see what it does."
        ),
        watch_for=(
            "Does it ask a clarifying question, or silently pick a direction?",
            "If it picks a direction, is the choice reasonable for a default user?",
            "Does it avoid destructive actions until the ambiguity is resolved?",
        ),
        expected_sub_molecules="TBD — observe",
    ),
    CompoundExperiment(
        title="Induced sub-skill failure — does it recover?",
        system_prompt=(
            "Run a normal request, but arrange for one sub-skill to fail "
            "(e.g., revoke a credential, point at a broken URL, fill a "
            "queue). Observe the response."
        ),
        watch_for=(
            "Does the failure surface clearly, or get hidden behind a fake 'success'?",
            "Does the system attempt an alternative path or escalate to the human?",
            "Does it avoid wedging in a retry loop?",
        ),
        expected_sub_molecules="TBD — observe",
    ),
    CompoundExperiment(
        title="Long-horizon autonomy",
        system_prompt=(
            "Give the system a goal that takes 10+ minutes of unattended "
            "work (e.g., 'audit the past week and produce a summary'). "
            "Leave it alone for 15 minutes."
        ),
        watch_for=(
            "Did it produce a real artefact, or did it spin / lose context?",
            "Are the intermediate steps sensible, or did it hallucinate?",
            "Did it know when to stop, or did it over-shoot the goal?",
        ),
        expected_sub_molecules="TBD — observe",
    ),
)

ORCHESTRATOR_COMPOUND_EXPERIMENTS: tuple[CompoundExperiment, ...] = (
    CompoundExperiment(
        title="Routing correctness across all downstreams",
        system_prompt=(
            "Send one request that should fan out to every documented "
            "downstream (one input per area). Observe the routing log."
        ),
        watch_for=(
            "Did each input land at the correct downstream?",
            "Are downstream call traces visible in the orchestrator log?",
            "Do partial failures stop unrelated downstreams from running?",
        ),
        expected_sub_molecules="One per documented downstream area.",
    ),
)


# --- Public API ----------------------------------------------------------


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


def layer_summary(layer: str) -> str:
    """One-line description for a layer."""

    layer = normalise_layer(layer)
    return {
        LAYER_ATOM: "Single responsibility. Same input → same output. No skill-level callouts.",
        LAYER_MOLECULE: "2–10 atoms wired by predefined orchestration. No runtime LLM routing.",
        LAYER_COMPOUND: "Multiple molecules; call graph decided at runtime by an LLM or human.",
        "unknown": "Layer not declared in repo.yaml — falls back to archetype heuristic.",
    }[layer]
