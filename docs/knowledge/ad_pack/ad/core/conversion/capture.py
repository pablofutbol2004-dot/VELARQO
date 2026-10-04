"""Conversion gear, slice 1 — capture an owned contact from inbound.

When a piece's CTA turns attention into a real, self-identified contact, we must
record it safely: only capture a contact handle when the person opted in
(consent). This slice models the signal and keeps a small in-memory log plus a
trace event. Real channel wiring and the per-business contact store come later
(via ZEUS); no platform is assumed here.
"""

from __future__ import annotations

import datetime as _dt
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from kleos.trace import TraceActor, TraceEvent, TraceOutcome, TraceStore


class ContactKind(StrEnum):
    NONE = "none"  # anonymous signal (e.g. a comment), no handle captured
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class InboundSignal(BaseModel):
    """One CTA-driven contact signal for a piece."""

    business_id: str = Field(min_length=1)
    piece_ref: str = Field(min_length=1)
    cta: str | None = None
    channel: str = Field(min_length=1)
    contact_kind: ContactKind = ContactKind.NONE
    contact_handle: str | None = None
    consent: bool = False
    note: str | None = None

    @model_validator(mode="after")
    def _consent_rules(self) -> InboundSignal:
        if self.contact_kind is not ContactKind.NONE:
            if not self.contact_handle:
                raise ValueError("a contact handle is required when contact_kind is set")
            if not self.consent:
                raise ValueError("capturing a contact handle requires consent (opt-in)")
        return self


class InboundLog:
    """In-memory capture log for owned contacts (until the ZEUS store)."""

    def __init__(self) -> None:
        self._items: dict[str, InboundSignal] = {}
        self._seq = 0

    def __len__(self) -> int:
        return len(self._items)

    def get(self, signal_id: str) -> InboundSignal:
        return self._items[signal_id]

    def all(self, business_id: str | None = None) -> list[InboundSignal]:
        if business_id is None:
            return list(self._items.values())
        return [s for s in self._items.values() if s.business_id == business_id]

    def next_id(self) -> str:
        self._seq += 1
        return f"lead-{self._seq:05d}"

    def add(self, signal_id: str, signal: InboundSignal) -> None:
        if signal_id in self._items:
            raise ValueError(f"signal already logged: {signal_id}")
        self._items[signal_id] = signal


def capture_inbound(
    signal: InboundSignal, log: InboundLog, *, trace: TraceStore | None = None
) -> str:
    """Record an owned inbound contact signal.

    Consent is enforced by the model; an anonymous signal (no handle) needs no
    contact capture. Returns the signal id.
    """
    signal_id = log.next_id()
    log.add(signal_id, signal)
    if trace is not None:
        trace.record(
            TraceEvent(
                id=trace.next_id(signal.business_id),
                business_id=signal.business_id,
                at=_dt.datetime.now(_dt.UTC),
                actor=TraceActor.MACHINE,
                outcome=TraceOutcome.OBSERVED,
                subject_kind="content_piece",
                subject_id=signal.piece_ref,
                reason=f"inbound via {signal.channel}"
                + (
                    f" ({signal.contact_kind.value})"
                    if signal.contact_kind is not ContactKind.NONE
                    else ""
                ),
                gear="conversion",
                detail={"signal_id": signal_id, "cta": signal.cta},
            )
        )
    return signal_id
