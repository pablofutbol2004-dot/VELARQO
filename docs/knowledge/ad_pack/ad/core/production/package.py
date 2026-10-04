"""Production gear, slice 1 — assemble a finished copy from a creative draft.

Deterministic: takes one validated ``CreativeVariant`` and produces the final
piece text a Quality gate can check. Assembly is deliberately simple (hook,
then narrative, then CTA) because real per-format assembly lands with adapters.
"""

from __future__ import annotations

from kleos.core.creative.contracts import CreativeVariant

from .contracts import PieceCopy


def build_piece_copy(variant: CreativeVariant, *, business_id: str) -> PieceCopy:
    """Assemble the final copy text for one draft variant."""
    blocks = [variant.hook, variant.narrative]
    if variant.cta:
        blocks.append(variant.cta)
    final_text = "\n\n".join(blocks)
    return PieceCopy(
        business_id=business_id,
        format=variant.format,
        hook=variant.hook,
        narrative=variant.narrative,
        cta=variant.cta,
        final_text=final_text,
        chars=len(final_text),
    )
