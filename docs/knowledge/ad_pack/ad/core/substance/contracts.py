"""Substance gear — draft input/output contracts (not implemented).

Substance researches and synthesises what is true and worth saying, ending in a
claim/proof-backed packet (``SubstancePacket``, named in the operator's vision)
that Creative turns into content. Draft seam only; field set pinned on first
implementation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from kleos.models import Claim, SourceRef


class SubstanceRequest(BaseModel):
    """What Substance is asked to research and back with proof."""

    pack: str = Field(min_length=1)
    focus: str = Field(min_length=1)  # the problem/claim to make true and sayable
    evidence_requirements: list[str] = Field(default_factory=list)


class SubstancePacket(BaseModel):
    """The truth-backed packet Creative will work from."""

    pack: str
    claim: Claim = Field(description="The central claim the piece rests on")
    supporting_claims: list[Claim] = Field(default_factory=list)
    proof_refs: list[SourceRef] = Field(
        default_factory=list,
        description="Real cases/results that back the claim (economic where possible)",
    )
    truth_gaps: list[str] = Field(
        default_factory=list,
        description="What is still unverified and must not be asserted",
    )
