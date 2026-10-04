"""Intelligence gear — a supervised, observable evidence pass.

Puts the extraction slice together with the engine's guarantees:

1. Ask the operator control plane first (evidence ingest is low-risk, so it
   auto-allows at normal autonomy; it blocks or queues a human when policy says so).
2. Run extraction (see ``extraction.py``).
3. Register every resulting insight in the claim ledger at ``research`` status —
   never ``confirmed``; turning a research insight into a belief stays a human act.
4. Record the whole pass to the trace (decision + completed run + prompt hash).

Pure and deterministic around the injected model call; no persistence, no vendor.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
from collections.abc import Callable

from kleos.actions import ActionKind
from kleos.control import ActionDecision, ActionProposal, ControlPlane, Verdict
from kleos.gate import propose
from kleos.ledger import Ledger
from kleos.models import Claim, ClaimStatus
from kleos.review import ReviewItem, ReviewQueue
from kleos.trace import TraceActor, TraceEvent, TraceOutcome, TraceStore

from .contracts import IntelligenceInput, IntelligenceOutput, MarketInsight
from .extraction import extract_insights, prompt_hash, render_extraction_prompt


@dataclasses.dataclass
class RunResult:
    decision: ActionDecision
    output: IntelligenceOutput | None
    claim_ids: list[str]
    review_item: ReviewItem | None = None


def run_intelligence_pass(
    request: IntelligenceInput,
    *,
    model: Callable[[str, str], str],
    plane: ControlPlane,
    ledger: Ledger,
    trace: TraceStore,
    review: ReviewQueue | None = None,
    pass_id: str | None = None,
    correlation_id: str | None = None,
) -> RunResult:
    """Run one supervised evidence pass and register its insights.

    ``correlation_id`` links the pass to the run that triggered it (e.g. a
    content-piece production), so the trace thread survives across gears.

    If the control plane does not allow the pass, nothing is extracted and the
    human path (review item) is returned instead — the machine never proceeds
    past its policy.
    """
    business = request.pack
    pass_id = pass_id or f"{business}-pass-{len(ledger) + 1:04d}"
    proposal = ActionProposal(
        business_id=business,
        kind=ActionKind.EVIDENCE_INGEST,
        subject_kind="evidence_pass",
        subject_id=pass_id,
        detail=f"{len(request.evidence)} evidence item(s)",
    )
    gated = propose(plane, proposal, review=review, trace=trace, correlation_id=correlation_id)
    if gated.decision.verdict is not Verdict.ALLOW:
        return RunResult(
            decision=gated.decision, output=None, claim_ids=[], review_item=gated.review_item
        )

    output = extract_insights(request, model=model)
    claim_ids: list[str] = []
    for insight in output.insights:
        claim = Claim.model_validate(insight.model_dump(exclude={"kind"}))
        entry = ledger.add(claim, status=ClaimStatus.RESEARCH)
        claim_ids.append(entry.id)

    rendered = render_extraction_prompt(request.evidence) if output.insights else None
    trace.record(
        TraceEvent(
            id=trace.next_id(business),
            business_id=business,
            at=_dt.datetime.now(_dt.UTC),
            actor=TraceActor.MACHINE,
            outcome=TraceOutcome.COMPLETED,
            action_kind=ActionKind.EVIDENCE_INGEST,
            subject_kind="evidence_pass",
            subject_id=pass_id,
            reason=f"registered {len(claim_ids)} research insight(s)",
            prompt_hash=prompt_hash(rendered) if rendered else None,
            prompt_version=1,
            detail={"claims": claim_ids},
            correlation_id=correlation_id,
        )
    )
    return RunResult(decision=gated.decision, output=output, claim_ids=claim_ids, review_item=None)


def insight_to_claim(insight: MarketInsight) -> Claim:
    """Strip the typed insight to its claim form for the ledger."""
    return Claim.model_validate(insight.model_dump(exclude={"kind"}))
