"""Production gear — draft contracts.

Production turns an approved creative draft into the final, platform-ready copy
and later, real assets. This slice models the *piece* (the finished text) and
its basic technical shape. Format-aware assembly, media and platform packaging
are later slices built against adapters — format stays a plug-in value.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PieceCopy(BaseModel):
    """A finished, ready-to-gate piece of copy in one format."""

    business_id: str = Field(min_length=1)
    format: str = Field(min_length=1)
    hook: str = Field(min_length=1)
    narrative: str = Field(min_length=1)
    cta: str | None = None
    final_text: str = Field(min_length=1, description="Assembled copy as it will be seen")
    chars: int = Field(ge=0, description="Length of final_text")


class ScriptBeat(BaseModel):
    """One spoken line of a short-form video plus what is on screen for it."""

    spoken: str = Field(min_length=1, description="The line said aloud")
    visual: str = Field(
        min_length=1, description="On-screen action/b-roll/text overlay for that line"
    )


class ShortFormVideoDraft(BaseModel):
    """A short-form video script a human could shoot, with packaging suggestions.

    Production stays out of making real video; this is the draft the operator
    judges (upload / rework / kill) before any production of assets exists.
    """

    business_id: str = Field(min_length=1)
    spoken_hook: str = Field(min_length=1, description="The cold-open line")
    beats: list[ScriptBeat] = Field(min_length=1)
    close_cta: str = Field(min_length=1, description="The closing spoken line asking one action")
    caption: str = Field(min_length=1, description="The post text that goes with the video")
    packaging_notes: list[str] = Field(
        default_factory=list,
        description="Suggestions: first frame, style/tone, pacing, overlays, what to avoid",
    )
