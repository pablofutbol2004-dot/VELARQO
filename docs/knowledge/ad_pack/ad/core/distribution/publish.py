"""Distribution gear, slice 1 — publish only through the operator gate.

Publishing is high-risk, so it never happens silently: a piece goes to a channel
only when the control plane allows it (which, at normal autonomy, means a human
approves first). The actual publish call is an injected Zeus surface
(``zeus.publish``), and the whole attempt is traced. No real channel is assumed.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
from collections.abc import Callable

from kleos.actions import ActionKind
from kleos.control import ActionDecision, ActionProposal, ControlPlane, Verdict
from kleos.gate import propose
from kleos.review import ReviewItem, ReviewQueue
from kleos.trace import TraceActor, TraceEvent, TraceOutcome, TraceStore


@dataclasses.dataclass
class PublishResult:
    decision: ActionDecision
    published: bool
    review_item: ReviewItem | None = None


def publish_piece(
    *,
    business_id: str,
    piece_ref: str,
    channel: str,
    payload: dict,
    plane: ControlPlane,
    trace: TraceStore,
    zeus_publish: Callable[[str, dict], None],
    review: ReviewQueue | None = None,
    correlation_id: str | None = None,
) -> PublishResult:
    """Attempt to publish one piece to a channel, gated and traced.

    ``correlation_id`` should be the producing run's id so the publish event
    stays on the same thread as the piece that was built.

    Returns ``published=True`` only when the plane allowed it and the channel
    accepted the payload; otherwise a human review item is queued (or the action
    is blocked). The piece never publishes past its policy.
    """
    proposal = ActionProposal(
        business_id=business_id,
        kind=ActionKind.CONTENT_PUBLISH,
        subject_kind="content_piece",
        subject_id=piece_ref,
        space={"platform": channel},
        detail=f"publish to {channel}",
    )
    gated = propose(plane, proposal, review=review, trace=trace, correlation_id=correlation_id)
    if gated.decision.verdict is not Verdict.ALLOW:
        return PublishResult(
            decision=gated.decision, published=False, review_item=gated.review_item
        )

    zeus_publish(channel, {"piece": piece_ref, **payload})
    trace.record(
        TraceEvent(
            id=trace.next_id(business_id),
            business_id=business_id,
            at=_dt.datetime.now(_dt.UTC),
            actor=TraceActor.MACHINE,
            outcome=TraceOutcome.COMPLETED,
            action_kind=ActionKind.CONTENT_PUBLISH,
            subject_kind="content_piece",
            subject_id=piece_ref,
            reason=f"published to {channel}",
            gear="distribution",
            correlation_id=correlation_id,
        )
    )
    return PublishResult(decision=gated.decision, published=True, review_item=None)
