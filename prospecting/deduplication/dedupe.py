from rapidfuzz import fuzz

FUZZY_MATCH_THRESHOLD = 90


def _exact_key(lead: dict) -> tuple[str, str]:
    return (lead.get("email") or "", lead.get("company_name") or "")


def _is_fuzzy_match(a: dict, b: dict) -> bool:
    if not a.get("company_name") or not b.get("company_name"):
        return False
    if a.get("postcode") != b.get("postcode"):
        return False
    return fuzz.ratio(a["company_name"], b["company_name"]) >= FUZZY_MATCH_THRESHOLD


def deduplicate(leads: list[dict]) -> list[dict]:
    """Annotate each lead with duplicate_of (canonical lead id) or None.

    Returns all input leads, in order, unmodified except for duplicate_of.
    """
    seen_exact: dict[tuple[str, str], dict] = {}
    canonical: list[dict] = []

    for lead in leads:
        lead.setdefault("duplicate_of", None)
        key = _exact_key(lead)
        existing = seen_exact.get(key)
        if existing is not None:
            lead["duplicate_of"] = existing["id"]
            continue
        seen_exact[key] = lead
        canonical.append(lead)

    fuzzy_canonical: list[dict] = []
    for lead in canonical:
        match = next(
            (existing for existing in fuzzy_canonical if _is_fuzzy_match(lead, existing)),
            None,
        )
        if match:
            lead["duplicate_of"] = match["id"]
        else:
            fuzzy_canonical.append(lead)

    return leads
