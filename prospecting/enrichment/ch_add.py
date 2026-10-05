"""Add a company we don't hold yet, found through its own website showing a
Companies House number (e.g. a window installer registered under a SIC code
our bulk pull didn't cover). Free: one Companies House API call."""

import os

from data.supabase_store import push_universe
from lib.normalization.normalize import normalize_lead
from lib.scoring.icp_score import evaluate_lead
from prospecting.enrichment.free_facts import Client

CATEGORY = {"ltd": "Private Limited Company", "llp": "Limited Liability Partnership", "plc": "Public Limited Company"}


def _accounts_category(profile: dict) -> str:
    kind = ((profile.get("accounts") or {}).get("last_accounts") or {}).get("type")
    return kind.replace("-", " ").upper() if kind and kind != "null" else "NO ACCOUNTS FILED"


def lead_from_profile(profile: dict, website: str, site: dict, source: str) -> dict | None:
    """Only active companies UK law lets us email (Ltd, LLP, PLC)."""
    if profile.get("company_status") != "active" or profile.get("type") not in CATEGORY:
        return None
    address = profile.get("registered_office_address") or {}
    return normalize_lead({
        "company_name": profile.get("company_name"),
        "legal_name": profile.get("company_name"),
        "company_number": profile.get("company_number"),
        "company_category": CATEGORY[profile["type"]],
        "accounts_category": _accounts_category(profile),
        "incorporation_date": profile.get("date_of_creation"),
        "sic_codes": profile.get("sic_codes") or [],
        "industry": " ".join(profile.get("sic_codes") or []),
        "address": ", ".join(address.get(k) for k in ("address_line_1", "address_line_2") if address.get(k)) or None,
        "city": address.get("locality"),
        "postcode": address.get("postal_code"),
        "registered_postcode": address.get("postal_code"),
        "website": website,
        "website_status": "ok",
        "website_title": site.get("website_title"),
        "website_text": site.get("website_text"),
        "emails_found": site.get("emails_found") or [],
        "email": site.get("email"),
        "email_source": "website" if site.get("email") else None,
        "sources": ["companies_house_api", source],
        "lead_source": source,
    })


def add_company(conn, number: str, website: str, site: dict, icp: dict, source: str, client: Client | None = None):
    """Returns the new company's id and tier, or None if it isn't one we can use."""
    client = client or Client(os.environ["COMPANIES_HOUSE_API_KEY"], max_requests=5)
    profile = client.get(f"/company/{number}")
    lead = lead_from_profile(profile or {}, website, site, source)
    if not lead:
        return None
    result = evaluate_lead(lead, icp)
    lead.update(icp_score=result["score"], tier=result["tier"], vertical_fit=result["vertical_fit"],
                score_breakdown=result["breakdown"], score_reasons=result["reasons"])
    if lead["tier"] == "reject":
        return None
    push_universe(conn, [lead], "windows", icp)
    return lead["company_id"], lead["tier"]
