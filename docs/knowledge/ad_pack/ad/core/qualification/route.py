"""Qualification gear, slice 1 — route an inbound signal to a human decision.

Who is worth pursuing is a judgement call. This slice formalises the seam: when
an owned contact arrives, the machine assembles a clear qualification request
(signal context + the signals it still needs) and queues it for a person — it
never guesses a route on its own. Real scoring/routing rules, fed by data and
offers, attach later.
"""

from __future__ import annotations

import datetime as _dt
import json

from kleos.review import ReviewItem, ReviewQueue
from kleos.trace import TraceActor, TraceEvent, TraceOutcome, TraceStore

ROUTES = ("nurture", "research_interview", "diagnostic", "sales", "no_fit")


def propose_qualification(
    *,
    business_id: str,
    signal_id: str,
    piece_ref: str,
    channel: str,
    contact_kind: str,
    context: str | None = None,
    needed: list[str] | None = None,
    review: ReviewQueue,
    trace: TraceStore | None = None,
) -> ReviewItem:
    """Queue one inbound signal for a human qualification decision.

    The review context states what a person should decide: which route
    (nurture / research interview / diagnostic / sales / no fit) and which
    signals are still missing.
    """
    needed = needed or []
    payload = {
        "signal_id": signal_id,
        "piece": piece_ref,
        "channel": channel,
        "contact_kind": contact_kind,
        "route_options": list(ROUTES),
        "signals_needed": needed,
    }
    if context:
        payload["context"] = context
    review_item = review.enqueue(
        business_id=business_id,
        subject_kind="inbound_signal",
        subject_id=signal_id,
        context="Decide route for inbound signal:\n"
        + json.dumps(payload, indent=2, ensure_ascii=False),
    )
    if trace is not None:
        trace.record(
            TraceEvent(
                id=trace.next_id(business_id),
                business_id=business_id,
                at=_dt.datetime.now(_dt.UTC),
                actor=TraceActor.MACHINE,
                outcome=TraceOutcome.NEEDS_HUMAN,
                subject_kind="inbound_signal",
                subject_id=signal_id,
                reason="qualification decision requested",
                gear="qualification",
                detail={"signals_needed": needed},
            )
        )
    return review_item
