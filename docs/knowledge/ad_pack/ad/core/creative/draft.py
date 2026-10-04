"""Creative gear, slice 1 — draft controlled variants from a truth packet.

Turns a ``SubstancePacket`` (what is true enough to say) into several controlled
variants in a chosen ``format``. The format is a per-pack plug-in value; this
gear never assumes which formats a business uses. Drafts are bounded (a small
number of variants), de-duplicated, and structurally validated. Whether a draft
is good is decided by the Quality gear + a human — never by this function.
"""

from __future__ import annotations

from collections.abc import Callable

from kleos import data_policy
from kleos.jsoncalls import call_json
from kleos.prompts import PromptRegistry, PromptTemplate
from kleos.similarity import text_similarity

from .contracts import CreativeVariant

TASK_CLASS = "normal"
_PROMPT_ID = "creative/draft-variants"
_PROMPT_TEXT = """You are a content creator. Write {count} distinct draft variants
for one piece in the format requested. Ground every draft ONLY in the allowed
claims; never state anything from the forbidden list.

Return ONLY a JSON array of {count} objects, each with:
- hook: the opening that stops attention (in the requested format)
- narrative: the body that carries the claim
- cta: one clear next action for the audience, or null
- note: which claim this variant leans on

Rules: each variant must be genuinely different (different angle or hook). Do not
repeat the same idea twice.

CRAFT GUIDANCE (apply these rules when writing; do not reproduce anyone's
example verbatim):
{craft_guidance}

FORMAT: {format}

ALLOWED CLAIMS (may assert):
{allowed}

FORBIDDEN (must NOT assert):
{forbidden}
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
                    description="Creative: draft controlled content variants",
                    version=1,
                    task_class=TASK_CLASS,
                )
            )
        return self._registry


_PROMPTS = _PromptHolder()


def packet_context(packet) -> tuple[str, str]:
    """Split a substance packet into what may be asserted vs what must not be."""
    claims = [packet.claim.statement, *(c.statement for c in packet.supporting_claims)]
    allowed = "\n".join(f"- {c}" for c in claims if c.strip())
    forbidden = "\n".join(f"- {g}" for g in packet.truth_gaps) or "- (none)"
    return allowed, forbidden


def draft_variants(
    *,
    business_id: str,
    format: str,
    packet,
    model: Callable[[str, str], str],
    count: int = 3,
    craft_brief: str | None = None,
    role: str | None = None,
) -> list[CreativeVariant]:
    """Draft and validate ``count`` distinct creative variants for a format.

    ``craft_brief``: when omitted, the drafting-phase craft is composed
    automatically (attention, copywriting, hooks, storytelling, spoken writing,
    value communication, proof) so creative writing follows the craft rules; pass
    an explicit empty string to opt out. ``role`` pins the cost tier
    (free | cheap_paid | premium); see ``kleos.model_tier.resolve``.
    """
    allowed, forbidden = packet_context(packet)
    guidance = craft_brief
    if guidance is None:
        from kleos.craft import compose_phase_bundle

        bundle, _ = compose_phase_bundle("draft")
        guidance = bundle or ""
    prompt_text = (
        _PROMPTS.registry()
        .render(
            _PROMPT_ID,
            {
                "craft_guidance": guidance or "(none supplied — apply sound creative craft)",
                "count": str(count),
                "format": format,
                "allowed": allowed,
                "forbidden": forbidden,
            },
        )
        .text
    )
    data = call_json(
        model, TASK_CLASS, prompt_text, role=role, data_class=data_policy.for_area("creative_draft")
    )
    if not isinstance(data, list):
        raise TypeError("creative draft did not return a JSON array")

    variants: list[CreativeVariant] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        try:
            variant = CreativeVariant(
                format=format,
                hook=str(row.get("hook") or "").strip(),
                narrative=str(row.get("narrative") or "").strip(),
                cta=str(row.get("cta")).strip() if row.get("cta") else None,
                note=str(row.get("note")).strip() if row.get("note") else None,
            )
        except (ValueError, TypeError):
            continue
        if any(text_similarity(variant.hook, v.hook) > 0.9 for v in variants):
            continue
        variants.append(variant)
        if len(variants) >= count:
            break
    if not variants:
        raise RuntimeError("creative draft produced no usable variants")
    return variants
