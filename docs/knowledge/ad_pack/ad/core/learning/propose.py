"""Learning gear, slice 1 — assemble change proposals for a human to decide.

Learning's output is never an instant mutation. When evidence (operator-recorded
results, trace outcomes) points at a change — updating an offer, a claim, an
experiment, or retiring something — the gear assembles a typed proposal with a
reason and queues it for human approval. The machine proposes; the person
disposes.
"""

from __future__ import annotations

import datetime as _dt
import json
from enum import StrEnum

from pydantic import BaseModel, Field

from kleos.review import ReviewItem, ReviewQueue
from kleos.trace import TraceActor, TraceEvent, TraceOutcome, TraceStore


class ProposalType(StrEnum):
    UPDATE_OFFER = "update_offer"
    PROMOTE_OFFER = "promote_offer"
    RETIRE_OFFER = "retire_offer"
    CONFIRM_CLAIM = "confirm_claim"
    REJECT_CLAIM = "reject_claim"
    UPDATE_SEED = "update_seed"
    KILL_EXPERIMENT = "kill_experiment"
    RETIRE_EXPERIMENT = "retire_experiment"


class LearningProposal(BaseModel):
    """One evidence-backed change the Learning gear wants a human to decide."""

    id: str = Field(min_length=1)
    business_id: str = Field(min_length=1)
    proposal_type: ProposalType
    subject_kind: str = Field(min_length=1)  # offer | claim | experiment | seed
    subject_id: str = Field(min_length=1)
    proposed: dict = Field(default_factory=dict)
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)


def propose_change(
    *,
    proposal: LearningProposal,
    review: ReviewQueue,
    trace: TraceStore | None = None,
) -> ReviewItem:
    """Queue a learning change for a human decision; never apply it directly."""
    review_item = review.enqueue(
        business_id=proposal.business_id,
        subject_kind=f"learning:{proposal.subject_kind}",
        subject_id=proposal.subject_id,
        context=json.dumps(
            {
                "type": proposal.proposal_type.value,
                "proposed": proposal.proposed,
                "reason": proposal.reason,
                "evidence_refs": proposal.evidence_refs,
            },
            indent=2,
        ),
    )
    if trace is not None:
        trace.record(
            TraceEvent(
                id=trace.next_id(proposal.business_id),
                business_id=proposal.business_id,
                at=_dt.datetime.now(_dt.UTC),
                actor=TraceActor.MACHINE,
                outcome=TraceOutcome.NEEDS_HUMAN,
                subject_kind=f"learning:{proposal.subject_kind}",
                subject_id=proposal.subject_id,
                reason=f"proposed {proposal.proposal_type.value}",
                gear="learning",
                evidence_refs=proposal.evidence_refs,
            )
        )
    return review_item
