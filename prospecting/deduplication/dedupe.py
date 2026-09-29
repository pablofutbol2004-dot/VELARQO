from rapidfuzz import fuzz

FUZZY_MATCH_THRESHOLD = 90


def _exact_key(record: dict, name_field: str) -> tuple[str, str]:
    return (record.get("email") or "", record.get(name_field) or "")


def _is_fuzzy_match(a: dict, b: dict, name_field: str) -> bool:
    if not a.get(name_field) or not b.get(name_field):
        return False
    if a.get("postcode") != b.get("postcode"):
        return False
    return fuzz.ratio(a[name_field], b[name_field]) >= FUZZY_MATCH_THRESHOLD


def deduplicate(records: list[dict], name_field: str = "company_name") -> list[dict]:
    """Annotate each record with duplicate_of (canonical record id) or None.

    Returns all input records, in order, unmodified except for duplicate_of.
    name_field selects which field holds the entity name (company_name for
    leads, name for reactivation records) used in fuzzy matching.
    """
    seen_exact: dict[tuple[str, str], dict] = {}
    canonical: list[dict] = []

    for record in records:
        record.setdefault("duplicate_of", None)
        key = _exact_key(record, name_field)
        existing = seen_exact.get(key)
        if existing is not None:
            record["duplicate_of"] = existing["id"]
            continue
        seen_exact[key] = record
        canonical.append(record)

    # Fuzzy matches require the same postcode, so only compare within a
    # postcode - the all-pairs version was ~1e9 comparisons at UK scale.
    fuzzy_canonical: dict[str, list[dict]] = {}
    for record in canonical:
        bucket = fuzzy_canonical.setdefault(record.get("postcode") or "", [])
        match = next((existing for existing in bucket if _is_fuzzy_match(record, existing, name_field)), None)
        if match:
            record["duplicate_of"] = match["id"]
        else:
            bucket.append(record)

    return records
