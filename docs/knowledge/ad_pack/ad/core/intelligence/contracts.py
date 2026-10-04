"""Intelligence gear — draft input/output contracts (not implemented).

First small Intelligence slice per the build order: capture real owner evidence
(conversations, notes, comments) and turn it into a structured, provenance-backed
list of pains/desires/beliefs/language. These types are the draft seam; the exact
field set is pinned when the gear is first implemented.

In:  raw evidence items.  Out: market insights, each with a kind and provenance.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from kleos.domain import MainConstraint, OutcomeBucket
from kleos.models import Claim, EvidenceLabel, SourceRef


class EvidenceItem(BaseModel):
    """One verbatim piece of raw owner evidence being ingested."""

    verbatim: str = Field(min_length=1)
    source: SourceRef
    source_language: str = "es"


class IntelligenceInput(BaseModel):
    """What the Intelligence gear consumes."""

    pack: str = Field(min_length=1)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class InsightKind(StrEnum):
    """The kinds of structured market knowledge Intelligence extracts."""

    PAIN = "pain"
    DESIRE = "desire"
    BELIEF = "belief"
    LANGUAGE = "language"
    OPPORTUNITY = "opportunity"


class MarketInsight(Claim):
    """A structured, provenance-backed market insight (a typed claim)."""

    kind: InsightKind


class IntelligenceOutput(BaseModel):
    """What the Intelligence gear produces for its pack."""

    pack: str
    insights: list[MarketInsight] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


def make_insight(
    kind: InsightKind,
    statement: str,
    *,
    label: EvidenceLabel = EvidenceLabel.NEEDS_CHECK,
    sources: list[SourceRef] | None = None,
    bucket: OutcomeBucket | None = None,
    constraint: MainConstraint | None = None,
) -> MarketInsight:
    """Small builder so callers write insights without repeating defaults."""
    return MarketInsight(
        kind=kind,
        statement=statement,
        label=label,
        sources=sources or [],
        bucket=bucket,
        constraint=constraint,
    )
