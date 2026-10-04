"""Strategy gear — draft input/output contracts (not implemented).

Strategy chooses what to make and why it should win attention, ending in a
hypothesis expressed as an experiment spec on the Lab/Factory portfolio (operator
vision). Draft seam only; field set pinned on first implementation.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ExperimentTier(StrEnum):
    """Portfolio tier: Lab (cheap, exploratory) vs Factory (proven, repeated)."""

    LAB = "lab"
    FACTORY = "factory"


class Hypothesis(BaseModel):
    """A falsifiable expectation about what will happen and why."""

    statement: str = Field(min_length=1)
    reasoning: str | None = None


class ContentExperimentSpec(BaseModel):
    """One content experiment the rest of the gears will execute."""

    pack: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    problem: str = Field(min_length=1)
    funnel_role: str | None = None  # what this piece is for in the funnel
    awareness: str | None = None  # audience awareness stage being targeted
    hypothesis: Hypothesis
    tier: ExperimentTier = ExperimentTier.LAB
    pillar_id: str | None = None  # which content pillar this bet serves
    icp_id: str | None = None  # which audience group (Icp) this piece is for
    source_claim_id: str | None = None  # which evidence/claim it tests
    notes: str | None = None
