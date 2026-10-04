"""Relevance-adaptive craft selection (Option 4, safe).

The curated bundles (``compose_format_bundle`` / ``compose_phase_bundle``) stay
the guaranteed baseline default. This module offers a smarter selector: given a
short request describing the piece's job, it ranks candidate craft rules —

- curated (format/phase) packs get a strong base weight, so the piece always
  starts from the rules that fit its format/phase;
- then rules from the wider general library are added by lexical relevance to
  the request, so an unusual piece can pull in knowledge its default map lacks;

…and the result is cut at a deterministic character budget.

Cross-language: craft rules are English while copy may be Spanish. Instead of
matching against the copy, use :func:`craft_request_for_piece`, which builds the
English request from the piece's STRUCTURED English tags (format, funnel role,
claim constraint/bucket, pillar, audience) — so relevance works even when the
copy is Spanish. Deterministic for a given input; kept separate from the baseline
so the two can be A/B tested on real pieces.
"""

from __future__ import annotations

from collections.abc import Sequence

from kleos.craft import (
    CRAFT_MAX_CHARS,
    GENERAL_PACKS_FOR_FORMAT,
    PHASE_PACKS,
    discover_library,
    load_craft_pack,
)

#: Extra weight for rules whose pack is already curated for this format/phase.
_CURATED_WEIGHT = 1.2
_MIN_WORD = 3


def _general_pack_names() -> list[str]:
    names: list[str] = []
    for entry in discover_library():
        if entry.kind == "general":
            names.append(entry.pack)
    return names


def _entries(pack_name: str, *, seq: int) -> list[dict]:
    pack = load_craft_pack(pack_name)
    out: list[dict] = []
    for category, rules in pack.categories.items():
        for item in rules:
            text = item.rule
            if item.why:
                text = f"{text} — {item.why}"
            out.append(
                {
                    "pack": pack_name,
                    "category": category,
                    "rule": item.rule,
                    "why": item.why,
                    "source": item.source,
                    "text": text,
                    "seq": seq,
                }
            )
            seq += 1
    return out


def _request_tokens(request: str) -> set[str]:
    words = {w for w in request.casefold().split() if len(w) >= _MIN_WORD}
    return words


def _score(entry: dict, request: str, curated: set[str]) -> float:
    base = _CURATED_WEIGHT if entry["pack"] in curated else 0.0
    if request:
        text_tokens = _request_tokens(entry["text"])
        req = _request_tokens(request)
        overlap = len(text_tokens & req)
        lex = overlap / max(1, len(req)) if req else 0.0
    else:
        lex = 0.0
    return base + lex


def _phrase(value: str) -> str:
    return " ".join(value.replace("_", " ").replace("-", " ").split())


def craft_request_for_piece(piece: dict) -> str:
    """Build an English relevance request from a piece's STRUCTURED tags.

    Rules are English; the copy may be Spanish. Rather than matching against the
    copy (which would give near-zero lexical overlap), use the English tags the
    piece already carries — format, funnel role, awareness, the claim's
    constraint and outcome bucket, pillar and audience — so relevance survives
    the language gap. E.g. a Spanish claim tagged ``constraint: conversion`` and
    ``bucket: make_more_money`` yields an English request containing
    "conversion make more money".
    """
    spec = piece.get("spec") or {}
    packet = piece.get("packet") or {}
    claim = packet.get("claim") or {}
    fields = [
        (piece.get("piece") or {}).get("format"),
        spec.get("funnel_role"),
        spec.get("awareness"),
        claim.get("constraint"),
        claim.get("bucket"),
        spec.get("pillar_id"),
        spec.get("icp_id"),
    ]
    return " ".join(_phrase(str(f)) for f in fields if f)


def select_craft_brief(
    *,
    request: str,
    format_name: str | None = None,
    phase: str | None = None,
    max_chars: int | None = CRAFT_MAX_CHARS,
    include_general: bool = True,
) -> tuple[str, list[dict]]:
    """Select a budget-bounded, relevance-ranked craft brief.

    Returns ``(brief_text, chosen)`` where ``chosen`` is the ordered list of
    chosen ``{pack, category, rule, why}`` entries (top-down). ``request`` is an
    English description of the piece's job/topic. Pack lists are resolved at call
    time, so newly added general packs are picked up automatically.
    """
    curated: set[str] = set()
    if format_name:
        curated.add(format_name)
        curated.update(GENERAL_PACKS_FOR_FORMAT.get(format_name, ()))
    if phase:
        curated.update(PHASE_PACKS.get(phase, ()))

    # Deterministic pool order: format first, then its general packs, then the
    # phase packs, then the rest of the general library (stable tie-breaking).
    pool: list[str] = []

    def _add(name: str) -> None:
        if name not in pool:
            pool.append(name)

    if format_name:
        _add(format_name)
        for name in GENERAL_PACKS_FOR_FORMAT.get(format_name, ()):
            _add(name)
    if phase:
        for name in PHASE_PACKS.get(phase, ()):
            _add(name)
    if include_general:
        for name in _general_pack_names():
            _add(name)

    entries: list[dict] = []
    seq = 0
    for name in pool:
        try:
            entries.extend(_entries(name, seq=seq))
        except Exception:  # noqa: BLE001 - skip packs that fail to load
            continue
        seq = len(entries)

    ranked = sorted(entries, key=lambda e: (-_score(e, request, curated), e["seq"]))
    chosen: list[dict] = []
    length = 0
    for entry in ranked:
        line = f"[{entry['pack']} · {entry['category']}] {entry['rule']}"
        if entry["why"]:
            line = f"{line} — {entry['why']}"
        if max_chars is not None and length + len(line) + 1 > max_chars:
            break
        chosen.append(
            {
                "pack": entry["pack"],
                "category": entry["category"],
                "rule": entry["rule"],
                "why": entry["why"],
            }
        )
        length += len(line) + 1
    brief = "\n".join(
        f"[{c['pack']} · {c['category']}] {c['rule']}" + (f" — {c['why']}" if c["why"] else "")
        for c in chosen
    )
    return brief, chosen


def retrieve_brief(
    request: str,
    *,
    branch: str | None = None,
    kinds: Sequence[str] | None = None,
    max_chars: int | None = CRAFT_MAX_CHARS,
) -> tuple[str, list[dict]]:
    """Budget-bounded relevance retrieval across the WHOLE knowledge library.

    Where :func:`select_craft_brief` returns content-craft guidance for a piece,
    this can pull rules from any area (``economics``, ``growth``, ``strategy``,
    ``ai_systems``, …) so a task that genuinely spans domains retrieves the
    smallest relevant set of rules rather than concatenating the library. Filter
    to one ``branch`` and/or ``kinds`` when the domain is known. Results are
    deterministic, capped at ``max_chars`` (dropping the tail at a line
    boundary), deduplicated by exact rule text, and every returned row keeps its
    ``source`` provenance. Returns ``(brief_text, chosen)``.
    """
    allowed = set(kinds) if kinds is not None else None
    branch_of: dict[str, str] = {}
    pool: list[str] = []
    for entry in discover_library():
        if branch is not None and entry.branch != branch:
            continue
        if allowed is not None and entry.kind not in allowed:
            continue
        pool.append(entry.pack)
        branch_of[entry.pack] = entry.branch

    entries: list[dict] = []
    seq = 0
    for name in pool:
        try:
            rows = _entries(name, seq=seq)
        except Exception:  # noqa: BLE001 - skip a pack that fails to load; validate_library gates it
            continue
        for row in rows:
            row["branch"] = branch_of[name]
        entries.extend(rows)
        seq = len(entries)

    ranked = sorted(entries, key=lambda entry: (-_score(entry, request, set()), entry["seq"]))
    chosen: list[dict] = []
    seen_rules: set[str] = set()
    length = 0
    for entry in ranked:
        if entry["rule"] in seen_rules:
            continue  # identical rule text never returned twice across areas
        line = f"[{entry['pack']} · {entry['category']}] {entry['rule']}"
        if entry["why"]:
            line = f"{line} — {entry['why']}"
        if max_chars is not None and length + len(line) + 1 > max_chars:
            break
        seen_rules.add(entry["rule"])
        chosen.append(
            {
                "pack": entry["pack"],
                "branch": entry["branch"],
                "category": entry["category"],
                "rule": entry["rule"],
                "why": entry["why"],
                "source": entry["source"],
            }
        )
        length += len(line) + 1
    brief = "\n".join(
        f"[{c['pack']} · {c['category']}] {c['rule']}" + (f" — {c['why']}" if c["why"] else "")
        for c in chosen
    )
    return brief, chosen
