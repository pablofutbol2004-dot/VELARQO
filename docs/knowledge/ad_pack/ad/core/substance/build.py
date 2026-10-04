"""Substance gear, slice 1 — build a claim/proof-backed packet for a bet.

Deterministic: it does not write content. Given an experiment's problem and the
pool of relevant claims (from the ledger), it picks the claim the piece should
rest on, gathers supporting claims, and states what is true enough vs what still
needs checking. It never upgrades a ``NEEDS_CHECK`` claim into a fact — anything
unverified is listed as a truth gap instead, so the Quality gate / human review
sees the risk.
"""

from __future__ import annotations

from kleos.models import Claim, EvidenceLabel, SourceRef
from kleos.similarity import text_similarity

from .contracts import SubstancePacket


def _usable_claims(claims: list[Claim], problem: str) -> list[Claim]:
    ranked = sorted(
        (c for c in claims if c.statement.strip()),
        key=lambda c: text_similarity(c.statement, problem),
        reverse=True,
    )
    return ranked


def _truth_gaps(used: list[Claim]) -> list[str]:
    gaps: list[str] = []
    for claim in used:
        if claim.label is EvidenceLabel.NEEDS_CHECK:
            gaps.append(f"claim {claim.statement!r} is marked NEEDS_CHECK (unverified)")
        elif not claim.sources:
            gaps.append(f"claim {claim.statement!r} has no source")
    return gaps


def _proof_refs(used: list[Claim]) -> list[SourceRef]:
    seen: set[str] = set()
    refs: list[SourceRef] = []
    for claim in used:
        for source in claim.sources:
            if source.url and source.reference not in seen:
                seen.add(source.reference)
                refs.append(source)
    return refs


def build_substance_packet(
    *,
    business_id: str,
    problem: str,
    claims: list[Claim],
) -> SubstancePacket:
    """Assemble the truth packet a piece will be written from.

    The central claim is the best textual match to the problem in the pool.
    Supporting claims share its constraint or outcome bucket. Truth gaps and
    proof refs are derived deterministically; nothing is asserted that the
    claims do not support.
    """
    ranked = _usable_claims(claims, problem)
    if not ranked:
        raise ValueError("cannot build substance with no usable claims")
    central = ranked[0]
    others = [c for c in ranked if c is not central]

    supporting: list[Claim] = []
    for claim in others:
        same_angle = claim.bucket is not None and claim.bucket == central.bucket
        if same_angle or claim.constraint == central.constraint:
            supporting.append(claim)
    if not supporting and others:
        supporting = [others[0]]

    used = [central, *supporting]
    gaps = _truth_gaps(used)
    if not gaps and not _proof_refs(used):
        gaps.append("no measured, sourced proof yet — do not claim an economic result")
    return SubstancePacket(
        pack=business_id,
        claim=central,
        supporting_claims=supporting,
        proof_refs=_proof_refs(used),
        truth_gaps=gaps,
    )
