"""Research summary, observation line and outreach angle for a lead.

Deterministic and evidence-based: every statement comes from data actually
on the lead (OSM category, city, content fetched from their own website).
When there's no evidence for something specific, the copy falls back to a
generic-but-true angle instead of a specific-sounding guess - e.g. a lead
with no website on file is never told "you don't have a website", because
OSM simply may not know it.

Callers only depend on research_leads(); an LLM-backed version can replace
the internals later.
"""

from lib.scoring.matching import find_terms, lead_domain

CATEGORY_LABELS = {
    "window_construction": "window installation",
    "glaziery": "glazing",
    "doors": "door",
    "window_blind": "blinds",
    "carpenter": "joinery",
    "kitchen": "kitchen",
    "cabinet_maker": "cabinet making",
}

_WEBSITE_SIGNALS = {
    "free quotes": ["free quote", "free quotation", "no obligation quote"],
    "quote/survey form": ["request a quote", "get a quote", "book a survey", "free survey", "request a callback"],
    "finance": ["finance available", "interest free", "pay monthly"],
    "reviews": ["testimonial", "trustpilot", "google reviews", "customer reviews"],
}

_ACCREDITATIONS = {
    "fensa": "FENSA registered",
    "certass": "CERTASS registered",
    "trustmark": "TrustMark approved",
    "checkatrade": "on Checkatrade",
    "which trusted trader": "a Which? Trusted Trader",
    "guild of master craftsmen": "a Guild of Master Craftsmen member",
}

# No "in our experience" / "installers we talk to": Velarqo has no client
# track record yet, and copy must not imply one. Revisit once it does.
DEFAULT_ANGLES = {
    "quote_driven": (
        "you're clearly getting quote requests in already, and a lot of the value usually sits "
        "in the ones that go quiet after the quote goes out"
    ),
    "default": (
        "most {trade} have a pile of old quotes sitting in a CRM or spreadsheet "
        "that never got a proper follow-up"
    ),
}


def display_name(lead: dict) -> str:
    return lead.get("display_name") or lead.get("company_name") or "your company"


def industry_label(lead: dict, icp: dict) -> str:
    fallback = icp.get("vertical_label") or icp.get("vertical") or "local"
    labels = {**CATEGORY_LABELS, **icp.get("category_labels", {})}
    category = str(lead.get("osm_category") or "")
    value = category.split("=", 1)[-1] if category else str(lead.get("industry") or "")

    weights = icp.get("osm_category_weights", {})
    weight = weights.get(category) or next((w for k, w in weights.items() if k.split("=", 1)[-1] == value), None)
    if weight is not None:
        # A weak category (shop=doors under a windows ICP) describes the lead
        # worse than the ICP's own label: "door firms" for a window+door company.
        return labels.get(value, fallback) if weight >= 0.8 else fallback

    if value in labels:
        return labels[value]
    if value and "_" not in value and len(value) <= 60:
        return value
    return fallback


def website_signals(lead: dict) -> list[str]:
    if lead.get("website_status") != "ok":
        return []
    text = f"{lead.get('website_title') or ''} {lead.get('website_text') or ''}"
    return [label for label, phrases in _WEBSITE_SIGNALS.items() if find_terms(text, phrases)]


def accreditations(lead: dict) -> list[str]:
    if lead.get("website_status") != "ok":
        return []
    text = lead.get("website_text") or ""
    return [label for term, label in _ACCREDITATIONS.items() if find_terms(text, [term])]


def choose_angle(lead: dict, icp: dict, signals: list[str]) -> tuple[str, str]:
    angles = {**DEFAULT_ANGLES, **icp.get("angles", {})}
    key = "quote_driven" if {"free quotes", "quote/survey form"} & set(signals) else "default"
    trade = icp.get("trade_noun") or f"{icp.get('vertical', 'local')} businesses"
    return key, angles[key].format(trade=trade)


def build_observation(lead: dict, label: str, accreditation_list: list[str]) -> str:
    city = lead.get("city")
    line = f"Came across {display_name(lead)} while looking at {label} firms{f' in {city}' if city else ''}"
    if accreditation_list:
        line += f" and saw you're {accreditation_list[0]}"
    return line + "."


def build_research_summary(lead: dict, label: str, signals: list[str], accreditation_list: list[str]) -> str:
    city = lead.get("city")
    parts = [f"{display_name(lead)}: {label}{f', {city}' if city else ''}."]

    domain = lead_domain(lead)
    status = lead.get("website_status")
    if status == "ok":
        title = (lead.get("website_title") or "").strip()
        title_part = f' - "{title[:80]}"' if title else ""
        parts.append(f"Site {domain} checked{title_part}.")
    elif lead.get("website"):
        parts.append(f"Site {domain} not checked ({status or 'enrichment not run'}).")
    else:
        parts.append("No website on file.")

    if signals:
        parts.append(f"Site shows: {', '.join(signals)}.")
    if accreditation_list:
        parts.append(f"Accreditations: {', '.join(accreditation_list)}.")

    contact = lead.get("email") or "no email found"
    if lead.get("email_source") == "website":
        contact += " (found on website)"
    parts.append(f"Contact: {contact}{f', {lead['phone']}' if lead.get('phone') else ''}.")
    parts.append(f"Score {lead.get('icp_score')} / tier {lead.get('tier')}.")
    return " ".join(parts)


def research_lead(lead: dict, icp: dict) -> dict:
    if lead.get("duplicate_of") or not lead.get("qualified"):
        return lead

    label = industry_label(lead, icp)
    signals = website_signals(lead)
    accreditation_list = accreditations(lead)
    angle_key, angle = choose_angle(lead, icp, signals)

    return {
        **lead,
        "industry_label": label,
        "website_signals": signals,
        "accreditations": accreditation_list,
        "angle_key": angle_key,
        "angle": angle,
        "observation": build_observation(lead, label, accreditation_list),
        "research_summary": build_research_summary(lead, label, signals, accreditation_list),
    }


def research_leads(leads: list[dict], icp: dict) -> list[dict]:
    return [research_lead(lead, icp) for lead in leads]
