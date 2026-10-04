"""Production, format slice — draft a short-form video script for human QC.

Turns a truth-backed ``SubstancePacket`` plus one chosen ``CreativeVariant`` into
a structured short-form vertical video draft: a spoken cold-open, short spoken
beats each with a concrete visual suggestion, a closing CTA, the caption, and
packaging/presentation notes. This is a *judgment draft* — Production still makes
no real video; the operator decides upload / rework / kill.

The prompt stays engine-generic: language, audience and tone come from the
injected ``voice`` (a per-pack/operator value), never hardcoded here. Claims are
bounded to the substance packet's allowed/forbidden lists, and output is
validated loudly — no junk drafts.
"""

from __future__ import annotations

from collections.abc import Callable

from kleos import data_policy
from kleos.core.creative.contracts import CreativeVariant
from kleos.core.creative.draft import packet_context
from kleos.jsoncalls import call_json
from kleos.prompts import PromptRegistry, PromptTemplate

from .contracts import ScriptBeat, ShortFormVideoDraft

TASK_CLASS = "normal"
_PROMPT_ID = "production/short-form-video-script"
_PROMPT_TEXT = """You are a short-form video script director. Turn one creative
draft into a complete vertical short-form video script (roughly 30-40 seconds) a
human could shoot today. Write in the audience's own language. Structure it for a
video: a cold-open spoken hook, short spoken beats, a close with one clear CTA,
and the caption to publish. Give each beat a concrete visual (what appears on
screen, b-roll, actions, text overlays) so presentation stays a human decision.

Return ONLY a JSON object with exactly these fields:
- spoken_hook: a string, the first spoken line (cold open)
- beats: an array of 4 to 6 objects; each object has two string fields: spoken
  (the line said aloud) and visual (what is on screen / b-roll / action / text
  overlay for that line)
- close_cta: a string, the last spoken line that asks for one action
- caption: a string, the post text that goes with the video (hashtags optional)
- packaging_notes: an array of short strings — first-frame idea, style and tone,
  pacing/timing, on-screen text guidance, what to avoid

Rules: ground every claim in ALLOWED only; never assert FORBIDDEN; keep lines
short and spoken-natural (short-form cadence); do not invent facts or numbers;
no keys outside these fields.

CRAFT GUIDANCE (apply the craft rules; do not reproduce anyone's example verbatim):
{craft_guidance}

VOICE AND AUDIENCE:
{voice}

ALLOWED CLAIMS (may assert):
{allowed}

FORBIDDEN (must NOT assert):
{forbidden}

CREATIVE MATERIAL TO PRESERVE (keep the idea, improve the execution):
Hook: {hook}
Body: {narrative}
CTA: {cta}
"""


class _PromptHolder:
    def __init__(self) -> None:
        self._registry: PromptRegistry | None = None

    def registry(self) -> PromptRegistry:
        if self._registry is None:
            self._registry = PromptRegistry()
            self._registry.register(
                PromptTemplate(
                    id=_PROMPT_ID,
                    text=_PROMPT_TEXT,
                    description="Production: draft a short-form video script for human QC",
                    version=1,
                    task_class=TASK_CLASS,
                )
            )
        return self._registry


_PROMPTS = _PromptHolder()


def draft_short_form_video(
    *,
    business_id: str,
    packet,
    variant: CreativeVariant,
    model: Callable[[str, str], str],
    voice: str | None = None,
    craft_brief: str | None = None,
    task_class: str | None = None,
    role: str | None = None,
) -> ShortFormVideoDraft:
    """Draft one human-judgeable short-form video script from substance + variant.

    ``craft_brief`` is compact distilled craft context. When omitted, the format's
    craft bundle is composed automatically (the short_form_video pack + the
    general packs that apply to it — see ``kleos.craft.compose_format_bundle``),
    so the craft knowledge is actually consumed, not unused reference. Pass an
    explicit empty string to opt out of craft guidance.

    ``task_class`` selects the router class (normal | smart | writing) and
    ``role`` pins the cost tier (free | cheap_paid | premium). For intent-based
    choices use ``kleos.model_tier.resolve``.
    """
    allowed, forbidden = packet_context(packet)
    guidance = craft_brief
    if guidance is None:
        from kleos.craft import compose_format_bundle

        bundle, _ = compose_format_bundle("short_form_video")
        guidance = bundle or ""
    prompt_text = (
        _PROMPTS.registry()
        .render(
            _PROMPT_ID,
            {
                "craft_guidance": guidance
                or "(none supplied — apply standard short-form craft)",
                "voice": voice or "Write plainly and specifically, in the audience's language.",
                "allowed": allowed,
                "forbidden": forbidden,
                "hook": variant.hook,
                "narrative": variant.narrative,
                "cta": variant.cta or "no cta in the source draft",
            },
        )
        .text
    )
    data = call_json(
        model,
        task_class or TASK_CLASS,
        prompt_text,
        role=role,
        data_class=data_policy.for_area("video_script"),
    )
    if not isinstance(data, dict):
        raise TypeError("video-script draft did not return a JSON object")

    spoken_hook = str(data.get("spoken_hook") or "").strip()
    close_cta = str(data.get("close_cta") or "").strip()
    caption = str(data.get("caption") or "").strip()
    if not spoken_hook or not close_cta or not caption:
        raise RuntimeError("video-script draft missing spoken_hook, close_cta or caption")

    beats: list[ScriptBeat] = []
    for row in data.get("beats") or []:
        if not isinstance(row, dict):
            continue
        spoken = str(row.get("spoken") or "").strip()
        visual = str(row.get("visual") or "").strip()
        if spoken and visual:
            beats.append(ScriptBeat(spoken=spoken, visual=visual))
    if not beats:
        raise RuntimeError("video-script draft produced no usable beats")

    notes_raw = data.get("packaging_notes")
    notes = [str(n).strip() for n in (notes_raw if isinstance(notes_raw, list) else []) if str(n).strip()]
    return ShortFormVideoDraft(
        business_id=business_id,
        spoken_hook=spoken_hook,
        beats=beats,
        close_cta=close_cta,
        caption=caption,
        packaging_notes=notes,
    )
