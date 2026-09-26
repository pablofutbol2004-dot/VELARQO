"""Maps arbitrary client CSV column headers onto our canonical schema fields.

Real clients export from wildly different CRMs (GHL, HubSpot, spreadsheets,
Salesforce). This does exact alias matching first, then fuzzy header
matching, so onboarding a new client is "map once," not "rebuild the
pipeline."
"""

from rapidfuzz import fuzz

FUZZY_HEADER_MATCH_THRESHOLD = 80

_CANONICAL_ALIASES: dict[str, list[str]] = {
    "company_name": ["company", "company name", "business name", "account name"],
    "name": ["name", "full name", "contact name", "customer name"],
    "email": ["email", "email address", "e-mail", "contact email"],
    "phone": ["phone", "phone number", "tel", "telephone", "mobile", "contact number"],
    "postcode": ["postcode", "post code", "zip", "zip code", "zipcode"],
    "website": ["website", "url", "web address", "domain"],
    "lead_source": ["lead source", "source", "channel"],
    "quote_value": ["quote value", "quote amount", "deal value", "opportunity value"],
    "quote_status": ["quote status", "deal status", "opportunity status"],
    "appointment_status": ["appointment status", "appt status", "meeting status"],
    "lost_reason": ["lost reason", "loss reason", "reason lost"],
    "last_contact": ["last contact", "last contacted", "last activity"],
    "notes": ["notes", "comments", "remarks"],
}


def _normalize_header(header: str) -> str:
    return header.strip().lower().replace("_", " ").replace("-", " ")


def build_column_mapping(headers: list[str]) -> dict[str, str]:
    """Returns {original_header: canonical_field} for headers we can map."""
    mapping: dict[str, str] = {}
    normalized_headers = {h: _normalize_header(h) for h in headers}

    for header, normalized in normalized_headers.items():
        for canonical, aliases in _CANONICAL_ALIASES.items():
            if normalized == canonical or normalized in aliases:
                mapping[header] = canonical
                break

    unmapped = [h for h in headers if h not in mapping]
    for header in unmapped:
        normalized = normalized_headers[header]
        best_match, best_score = None, 0
        for canonical, aliases in _CANONICAL_ALIASES.items():
            for candidate in [canonical, *aliases]:
                score = fuzz.ratio(normalized, candidate)
                if score > best_score:
                    best_match, best_score = canonical, score
        if best_score >= FUZZY_HEADER_MATCH_THRESHOLD:
            mapping[header] = best_match

    return mapping


def apply_mapping(records: list[dict], mapping: dict[str, str]) -> list[dict]:
    mapped_records = []
    for record in records:
        mapped = {mapping.get(k, k): v for k, v in record.items()}
        mapped_records.append(mapped)
    return mapped_records
