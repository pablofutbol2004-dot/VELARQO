"""Strategy Loop A — propose one decision from the evidence, or ask for more.

This is decision-specific reasoning, not one giant "rethink the business" prompt.
It retrieves the findings and the artifacts behind them, records a
``RetrievalManifest`` of exactly what it used, and then either

- proposes a Decision — drafted and stored at ``draft``, which a person must
  approve before anything runs against it; or
- raises a **ResearchRequest** when the evidence is too thin to decide
  responsibly, rather than inventing certainty.

The threshold is explicit and deterministic. There is no model in it.
"""

from __future__ import annotations

from collections.abc import Callable

from kleos import data_policy
from kleos.artifacts import independent_support, load_artifact
from kleos.core.intelligence.study import SiteFeature
from kleos.decisions import DecisionType, create_decision
from kleos.intel import ClaimStrength, ItemStatus, ItemType, list_items, request_research
from kleos.jsoncalls import call_json
from kleos.prompts import PromptRegistry, PromptTemplate
from kleos.retrieval import build_manifest

TASK_CLASS = "normal"

#: A proposal needs this many findings, resting on this many *independent* voices,
#: and covering this many distinct workshops. Below any of them Strategy asks for
#: evidence instead of deciding.
#:
#: The workshop count is the point: one workshop showing four absences is still one
#: workshop, and does not justify a market-level content thesis.
MIN_FINDINGS = 3
MIN_INDEPENDENT_SOURCES = 2
MIN_WORKSHOPS = 3

#: Version 2 exists because version 1's prompt asked for a "core pain" and got
#: one asserted as fact. Version 1 text is immutable and still resolvable; this is
#: what a proposal uses now.
_PROMPT_ID = "strategy/propose-thesis"
_PROMPT_TEXT = """You are a content strategist working from website-observation
evidence. Propose ONE scoped learning/content hypothesis — not a proven problem.

You must respect what the evidence can support. The findings say only what the
sampled websites did or did not visibly show. They do NOT show that customers
behave a certain way, or that a workshop is losing money. Do not assert either.

Return ONLY a JSON object with exactly these fields:
- icp_segment: who this content would serve, grounded in the findings
- hypothesis: one sentence, phrased as a hypothesis to test, e.g. "Workshop
  owners may not realise that X is invisible to customers"
- content_thesis: one sentence on what the content would show or argue, phrased
  as something the audience can verify for themselves
- why_it_might_matter: one or two sentences, explicitly hedged, on what would be
  true if the hypothesis held. Do not state it as fact.
- alternatives: a JSON array of 1-3 objects, each with the keys "option" (an
  alternative you set aside) and "misses" (what it fails to account for)
- assumptions: a JSON array of strings — including the assumptions this evidence
  does NOT test
- what_to_measure_next: a JSON array of 1-4 concrete things to measure to test
  whether this actually matters commercially (e.g. mystery-shop response times,
  owner interviews, funnel data, a controlled experiment)
- rationale_summary: two sentences, plain language, hedged

Rules: ground everything in the findings. Invent no facts and no numbers. Never
write that a workshop is losing customers or money.

CRAFT GUIDANCE (apply these rules; do not reproduce anyone's example verbatim):
{craft_guidance}

FINDINGS:
{findings}
"""


#: Version 1, kept verbatim so the prompt that produced `dec-0001` stays
#: reproducible. It asked for a "core pain" and got one asserted as fact; version 2
#: asks for a testable hypothesis instead. History is not rewritten.
_PROMPT_TEXT_V1 = """You are a content strategist. Given the evidence findings below,
propose ONE content thesis: who the content serves and the single problem it
should attack.

Return ONLY a JSON object with exactly these fields:
- icp_segment: the audience this serves, grounded in the findings
- core_pain: the one problem the content should attack
- content_thesis: one sentence stating what the content will argue or show
- alternatives: a JSON array of 1-3 objects, each with the keys "option" (the
  alternative you set aside) and "misses" (what it fails to explain)
- assumptions: a JSON array of strings
- rationale_summary: two sentences, plain language

Rules: ground everything in the findings. Invent no facts and no numbers.

CRAFT GUIDANCE (apply these rules; do not reproduce anyone's example verbatim):
{craft_guidance}

FINDINGS:
{findings}
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
                    text=_PROMPT_TEXT_V1,
                    description="Strategy: propose one content thesis from findings (v1)",
                    version=1,
                    task_class=TASK_CLASS,
                )
            )
            self._registry.register(
                PromptTemplate(
                    id=_PROMPT_ID,
                    text=_PROMPT_TEXT,
                    description="Strategy: propose a scoped learning hypothesis (v2)",
                    version=2,
                    task_class=TASK_CLASS,
                )
            )
        return self._registry


_PROMPTS = _PromptHolder()


def _findings_and_artifacts(
    store, venture_id: str, *, correlation_id: str | None = None
) -> tuple[list[dict], list[dict]]:
    """The findings Strategy may reason from, and the artifacts behind them.

    Only findings with at least one observed absence are included. A feature
    finding records how many workshops lacked it in ``entity_ids``; when that is
    empty, every sampled site showed the feature and there is nothing to solve —
    reasoning from it produced a hypothesis about a contact page that every site
    already had. Presence is evidence, but it is not a problem statement.
    """
    findings = [
        item
        for item in list_items(store, venture_id, item_type=ItemType.FINDING)
        if item.get("status") == ItemStatus.ACTIVE.value
        and item.get("entity_ids")
        and (correlation_id is None or item.get("correlation_id") == correlation_id)
    ]
    artifact_ids: list[str] = []
    for finding in findings:
        artifact_ids.extend(finding.get("artifact_ids") or [])
    artifacts = [
        artifact
        for artifact in (load_artifact(store, venture_id, a) for a in dict.fromkeys(artifact_ids))
        if artifact is not None
    ]
    return findings, artifacts


def _independent_count(artifacts: list[dict]) -> int:
    return independent_support(artifacts)


def render_thesis_prompt(findings: list[dict], *, craft_brief: str | None = None):
    """The rendered, hashed prompt for one thesis proposal.

    Returns the ``RenderedPrompt`` (not just its text) so the caller can record
    the exact template version and hash in the decision's retrieval manifest.
    """
    guidance = craft_brief
    if guidance is None:
        from kleos.craft import compose_phase_bundle

        bundle, _ = compose_phase_bundle("strategy")
        guidance = bundle or ""
    lines = [
        f"- [{(f.get('constraint') or 'unspecified')}] {f['statement']} "
        f"(absent on {len(f.get('entity_ids') or [])} of the sampled sites; "
        f"evidence: {len(f.get('artifact_ids') or [])} artifact(s))"
        for f in findings
    ]
    return _PROMPTS.registry().render(
        _PROMPT_ID,
        {
            "craft_guidance": guidance or "(none supplied — apply sound strategy craft)",
            "findings": "\n".join(lines),
        },
    )


def evidence_gap(findings: list[dict], artifacts: list[dict]) -> list[str]:
    """Why the current evidence is not enough to decide, in plain terms."""
    gaps: list[str] = []
    if len(findings) < MIN_FINDINGS:
        gaps.append(f"only {len(findings)} finding(s); {MIN_FINDINGS} needed")
    independent = _independent_count(artifacts)
    if independent < MIN_INDEPENDENT_SOURCES:
        gaps.append(
            f"only {independent} independent source voice(s); {MIN_INDEPENDENT_SOURCES} needed"
        )
    workshops = {entity for f in findings for entity in (f.get("entity_ids") or [])}
    if len(workshops) < MIN_WORKSHOPS:
        gaps.append(f"findings cover only {len(workshops)} workshop(s); {MIN_WORKSHOPS} needed")
    return gaps


def propose_content_thesis(
    store,
    venture_id: str,
    *,
    model: Callable[[str, str], str],
    question: str | None = None,
    mandate_version: int | None = None,
    research_question: str | None = None,
    craft_brief: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    """Propose one content-thesis decision, or raise a research request.

    ``correlation_id`` scopes the evidence to one study pass. Without it, every
    active finding for the venture is used — which mixes passes, so a caller that
    has run more than one study should say which one it means.

    Returns ``{"decision": ...}`` when the evidence supports a proposal, or
    ``{"research_request": ..., "gaps": [...]}`` when it does not.
    """
    findings, artifacts = _findings_and_artifacts(
        store, venture_id, correlation_id=correlation_id
    )
    gaps = evidence_gap(findings, artifacts)
    if gaps:
        request = request_research(
            store,
            venture_id,
            question=research_question
            or "Which workshops leak inbound demand or trust, and how often?",
            gap=gaps,
        )
        return {"research_request": request, "gaps": gaps}

    prompt = render_thesis_prompt(findings, craft_brief=craft_brief)
    data = call_json(model, TASK_CLASS, prompt.text, data_class=data_policy.for_area("strategy"))
    if not isinstance(data, dict):
        raise TypeError("thesis proposal did not return a JSON object")

    icp_segment = str(data.get("icp_segment") or "").strip()
    hypothesis = str(data.get("hypothesis") or "").strip()
    thesis = str(data.get("content_thesis") or "").strip()
    if not icp_segment or not hypothesis or not thesis:
        raise RuntimeError("thesis proposal missing icp_segment, hypothesis or content_thesis")

    alternatives = [row for row in (data.get("alternatives") or []) if isinstance(row, dict)]
    assumptions = [str(a).strip() for a in (data.get("assumptions") or []) if str(a).strip()]
    to_measure = [str(m).strip() for m in (data.get("what_to_measure_next") or []) if str(m).strip()]
    if not to_measure:
        # The mandate's phase is learning-and-proof: a proposal that says nothing
        # about how it would be tested is not ready to be proposed.
        raise RuntimeError("thesis proposal did not say what to measure next")

    manifest = build_manifest(
        items=findings,
        artifacts=artifacts,
        query=question or "where do sampled workshops leak inbound demand or trust?",
        rendered_prompt=prompt,
        mandate_version=mandate_version,
        notes=(
            f"independent source voices: {_independent_count(artifacts)}"
            " | claim strength: observed_absence (website observation only)"
            " | model/provider not recorded: the injected model callable returns text "
            "only, so KLEOS cannot see which model the router chose"
        ),
    )
    decision = create_decision(
        store,
        venture_id,
        family_key="content_thesis",
        decision_type=DecisionType.CONTENT_STRATEGY,
        question=question or "What scoped content/learning hypothesis should we test?",
        choice={
            "icp_segment": icp_segment,
            "hypothesis": hypothesis,
            "content_thesis": thesis,
            "why_it_might_matter": str(data.get("why_it_might_matter") or "").strip() or None,
        },
        title=f"Content hypothesis: {hypothesis[:90]}",
        alternatives=alternatives,
        assumptions=assumptions,
        next_measurements=to_measure,
        rationale_summary=str(data.get("rationale_summary") or "").strip() or None,
        evidence_refs=[f["id"] for f in findings],
        artifact_refs=[a["id"] for a in artifacts],
        retrieval_manifest=manifest,
        mandate_version=mandate_version,
        claim_strength=ClaimStrength.OBSERVED_ABSENCE.value,
        note=(
            "proposed by Strategy as an unproven hypothesis from website observation; "
            "requires human approval before activation"
        ),
    )
    return {"decision": decision}


def feature_reading(store, venture_id: str) -> list[dict]:
    """The per-feature picture behind a study, read back from its findings.

    A small read helper so the dashboard and the report can show the same numbers
    the findings carry, without re-deriving them.
    """
    readings: list[dict] = []
    for finding in list_items(store, venture_id, item_type=ItemType.FINDING):
        note = finding.get("note") or ""
        if not note.startswith("feature:"):
            continue
        slug = note.split("feature:", 1)[1].strip()
        try:
            feature = SiteFeature(slug)
        except ValueError:
            continue
        health = finding.get("health") or {}
        readings.append(
            {
                "feature": feature.value,
                "statement": finding["statement"],
                "claim_strength": finding.get("claim_strength"),
                "workshops_without": len(finding.get("entity_ids") or []),
                "supporting": health.get("supporting_count"),
                "finding_id": finding["id"],
                "dataset_artifact_id": finding.get("dataset_artifact_id"),
            }
        )
    return readings
