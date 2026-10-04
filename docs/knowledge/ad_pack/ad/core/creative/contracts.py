"""Creative gear — draft contracts (format is a per-pack plug-in value).

A creative draft is one controlled variant of a piece: the hook (what stops
attention), the narrative/body (what carries the claim), and the CTA (what the
audience does next). ``format`` is deliberately a free string — which formats a
pack actually produces is an operator decision, not an engine assumption.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreativeVariant(BaseModel):
    """One controlled draft of a piece."""

    format: str = Field(
        min_length=1, description="e.g. video_script, caption, post, email — pack decides"
    )
    hook: str = Field(min_length=1, description="The first thing that stops attention")
    narrative: str = Field(
        min_length=1, description="The body: carries the claim, stays inside the truth gaps"
    )
    cta: str | None = Field(default=None, description="What the audience should do next")
    note: str | None = Field(default=None, description="Which evidence/claim this variant leans on")
