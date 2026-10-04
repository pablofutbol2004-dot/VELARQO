"""Strategy gear, slice 1 — draft one content experiment from a bet.

Strategy's job is to choose what to make and why it should win. The *choice* of
which bet to test stays with the planner/operator; this slice turns one chosen
bet (a content pillar + a pain it targets) into a typed ``ContentExperimentSpec``.
The model drafts the persuasive framing (objective + hypothesis); deterministic
code validates it into the typed contract and never fabricates fields it cannot
parse. Unknown stays unknown.
"""

from __future__ import annotations

from collections.abc import Callable

from kleos import data_policy
from kleos.jsoncalls import call_json
from kleos.prompts import PromptRegistry, PromptTemplate

from .contracts import ContentExperimentSpec, ExperimentTier, Hypothesis

TASK_CLASS = "normal"

_PROMPT_ID = "strategy/draft-experiment"
_PROMPT_TEXT = """You are a content strategist. Turn one bet into a single clear
content experiment. The bet targets one recurring business problem through one
content pillar.

Return ONLY a JSON object with exactly these fields:
- objective: the strategic job of this piece, one sentence
- hypothesis_statement: a falsifiable expectation, one sentence, in the form
  "If we publish [what] to [audience], then [signal]."
- hypothesis_reasoning: why you expect that, one or two sentences
- funnel_role: one of awareness, education, pain_discovery, mechanism,
  objection_handling, proof, conversion, or null if unclear
- awareness: the audience stage this targets: unaware, problem_aware,
  solution_aware, or null
- notes: anything the gear should remember, or null

Rules: only ground on the provided bet; no invented facts or numbers.

CRAFT GUIDANCE (apply these rules when choosing the angle and framing):
{craft_guidance}

CONTENT PILLAR:
{pillar}

PROBLEM BEING TESTED:
{problem}
"""


class _PromptHolder:
    def __init__(self) -> None:
        self._registry: PromptRegistry | None = None

    def registry(self) -> PromptRegistry:
        if self._registry is None:
            self._registry = PromptRegistry()
            self._registry.register(
                PromptTemplate(
                    id=_PROMPT_ID,
                    text=_PROMPT_TEXT,
                    description="Strategy: draft one content experiment spec",
                    version=1,
                    task_class=TASK_CLASS,
                )
            )
        return self._registry


_PROMPTS = _PromptHolder()


def _pillar_blurb(pillar) -> str:
    name = getattr(pillar, "name", "?")
    description = getattr(pillar, "description", "")
    angles = "; ".join(getattr(pillar, "starter_angles", []))
    return f"{name}: {description} Starter angles: {angles or 'none yet'}"


def _icp_blurb(icp) -> str:
    name = getattr(icp, "name", "?")
    role = getattr(getattr(icp, "role", None), "value", "?")
    description = getattr(icp, "description", "")
    return f"{name} ({role}): {description}"


def draft_experiment(
    *,
    business_id: str,
    problem: str,
    model: Callable[[str, str], str],
    pillar=None,
    pillar_id: str | None = None,
    icp=None,
    icp_id: str | None = None,
    source_claim_id: str | None = None,
    tier: ExperimentTier = ExperimentTier.LAB,
    craft_brief: str | None = None,
) -> ContentExperimentSpec:
    """Draft a typed experiment spec from one bet (pillar + audience + problem).

    ``pillar`` may be a ``ContentPillar`` object (preferred) or a bare
    ``pillar_id``. ``icp`` may be an ``Icp`` object (preferred) or a bare
    ``icp_id``; it names the single audience this piece is for, so different
    audiences are never treated as one. ``model`` is the Zeus-style callable. If
    the model returns unusable JSON the call fails loudly — a spec is never built
    from half-parsed output.

    ``craft_brief``: when omitted, the strategy-phase craft is composed
    automatically (``ideation_angles``, so choosing the angle follows the craft
    rules); pass an explicit empty string to opt out.
    """
    pillar_id = pillar_id or (getattr(pillar, "id", None) if pillar else None)
    blurb = _pillar_blurb(pillar) if pillar is not None else (pillar_id or "not specified")
    icp_id = icp_id or (getattr(icp, "id", None) if icp else None)
    guidance = craft_brief
    if guidance is None:
        from kleos.craft import compose_phase_bundle

        bundle, _ = compose_phase_bundle("strategy")
        guidance = bundle or ""
    prompt_text = _PROMPTS.registry().render(
        _PROMPT_ID,
        {
            "craft_guidance": guidance or "(none supplied — apply sound strategy craft)",
            "pillar": blurb,
            "problem": problem,
        },
    ).text
    audience = _icp_blurb(icp) if icp is not None else (icp_id or None)
    if audience:
        prompt_text = f"{prompt_text}\n\nTARGET AUDIENCE (the single ICP this piece is for):\n{audience}"
    data = call_json(
        model, TASK_CLASS, prompt_text, data_class=data_policy.for_area("strategy")
    )
    if not isinstance(data, dict):
        raise TypeError("experiment draft did not return a JSON object")

    objective = str(data.get("objective") or "").strip()
    hypothesis_statement = str(data.get("hypothesis_statement") or "").strip()
    if not objective or not hypothesis_statement:
        raise RuntimeError("experiment draft missing objective or hypothesis")
    reasoning = str(data.get("hypothesis_reasoning") or "").strip() or None
    funnel_role = str(data.get("funnel_role") or "").strip() or None
    awareness = str(data.get("awareness") or "").strip() or None
    notes = str(data.get("notes") or "").strip() or None
    return ContentExperimentSpec(
        pack=business_id,
        objective=objective,
        problem=problem,
        funnel_role=funnel_role,
        awareness=awareness,
        hypothesis=Hypothesis(statement=hypothesis_statement, reasoning=reasoning),
        tier=tier,
        pillar_id=pillar_id,
        icp_id=icp_id,
        source_claim_id=source_claim_id,
        notes=notes,
    )
