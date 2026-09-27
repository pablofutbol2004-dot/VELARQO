"""ICP scoring: multi-signal, evidence-weighted, explainable.

Four dimensions, each 0-1, combined by ICP-configurable weights. A
dimension with no data at all (e.g. firmographics for an OSM-sourced lead)
is dropped from the denominator rather than counted as a failure.

- vertical_fit: is this actually the target trade? Strongest evidence
  wins (OSM category > name > website content > domain), with a small
  bonus when independent sources agree. Off-target signals in the name
  (blinds, garage doors, suppliers) and national chains are penalized.
- contactability: can we actually reach them by the ICP's channel?
- firmographic: size/revenue in range, only when that data exists.
- data_quality: valid postcode, address, a real business name (not
  "Blinds" or "Window Division").

Every lead also gets a tier and human-readable reasons, so a score is
never a black box:
  A/B  qualified and sendable now
  C    right vertical, but not sendable yet (no email) or weak score
  reject  wrong vertical, excluded, or off-target
"""

import re
from statistics import mean

from lib.scoring.matching import find_terms, find_terms_in_domain, lead_domain

DEFAULT_WEIGHTS = {"vertical_fit": 0.5, "contactability": 0.25, "firmographic": 0.15, "data_quality": 0.1}

_UK_POSTCODE = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$")
_GENERIC_NAME_WORDS = {
    "the", "and", "ltd", "limited", "co", "uk", "division", "sales", "centre", "center",
    "supplies", "supplier", "services", "service", "group", "company", "systems", "solutions",
}


def _to_number(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number != number else number


def _vertical_terms(icp: dict) -> tuple[list, list, list]:
    core = icp.get("core_terms") or icp.get("industry_keywords", [])
    return core, icp.get("adjacent_terms", []), icp.get("negative_terms", [])


def _category_weight(lead: dict, icp: dict) -> tuple[float | None, str | None]:
    weights = {k.lower(): v for k, v in icp.get("osm_category_weights", {}).items()}
    category = str(lead.get("osm_category") or "").strip().lower()
    if category in weights:
        return weights[category], category

    # CSVs sourced before osm_category existed only kept the tag value.
    value = str(lead.get("industry") or "").strip().lower()
    for key, weight in weights.items():
        if key.split("=", 1)[-1] == value:
            return weight, key
    return None, None


def _vertical_fit(lead: dict, icp: dict, name: str, reasons: list[str]) -> float:
    core, adjacent, negative = _vertical_terms(icp)
    category_text = " ".join(str(lead.get(f) or "") for f in ("industry", "osm_category"))
    website_text = " ".join(str(lead.get(f) or "") for f in ("website_title", "website_text"))
    signals: dict[str, float] = {}

    weight, category = _category_weight(lead, icp)
    if weight is not None:
        signals["category"] = weight
        reasons.append(f"+ listed as {category} (fit {weight:.1f})")

    if hits := find_terms(name, core):
        signals["name"] = 1.0
        reasons.append(f"+ name says '{hits[0]}'")
    elif hits := find_terms(name, adjacent):
        signals["name"] = 0.6
        reasons.append(f"+ name says adjacent '{hits[0]}'")

    if hits := find_terms(website_text, core):
        signals["website"] = min(1.0, 0.7 + 0.1 * (len(hits) - 1))
        reasons.append(f"+ website mentions {', '.join(hits[:3])}")
    elif hits := find_terms(category_text, core):
        signals["description"] = min(1.0, 0.7 + 0.1 * (len(hits) - 1))
        reasons.append(f"+ described as {', '.join(hits[:3])}")
    elif hits := find_terms(f"{category_text} {website_text}", adjacent):
        signals["description"] = 0.45
        reasons.append(f"+ adjacent mention '{hits[0]}'")

    domain = lead_domain(lead)
    if domain:
        if hits := find_terms_in_domain(domain, core):
            signals["domain"] = 0.8
            reasons.append(f"+ domain {domain} contains '{hits[0]}'")
        elif hits := find_terms_in_domain(domain, adjacent):
            signals["domain"] = 0.5
            reasons.append(f"+ domain {domain} contains adjacent '{hits[0]}'")

    fit = max(signals.values(), default=0.0)
    corroborating = sum(1 for v in signals.values() if v >= 0.5) - 1
    if fit > 0 and corroborating > 0:
        fit = min(1.0, fit + 0.05 * corroborating)

    if hits := find_terms(name, negative):
        fit *= 0.3
        reasons.append(f"- name suggests off-target '{hits[0]}' (x0.3)")
    elif (hits := find_terms(category_text, negative)) and not find_terms(name, core):
        fit *= 0.7
        reasons.append(f"- categorised as off-target '{hits[0]}' (x0.7)")

    chain = lead.get("brand") or next(iter(find_terms(name, icp.get("known_chains", []))), None)
    if chain:
        keep = 1 - icp.get("chain_penalty", 0.5)
        fit *= keep
        reasons.append(f"- national chain/brand '{chain}' (x{keep:.1f})")

    if not signals:
        reasons.append("- no evidence of the target vertical")
    return round(fit, 3)


def _contactability(lead: dict, reasons: list[str]) -> float:
    website_dead = lead.get("website_status") == "unreachable"
    if website_dead:
        reasons.append("- website unreachable (business may have closed)")

    if lead.get("email"):
        source = " (from website)" if lead.get("email_source") == "website" else ""
        reasons.append(f"+ email {lead['email']}{source}")
        return 1.0
    if lead.get("website") and not website_dead:
        reasons.append("- no email yet, but a website to find one")
        return 0.6
    if lead.get("phone"):
        reasons.append("- phone only, no email")
        return 0.3
    reasons.append("- no contact details")
    return 0.0


def _firmographic(lead: dict, icp: dict, reasons: list[str]) -> float | None:
    parts = []
    size = _to_number(lead.get("company_size"))
    if size is not None and icp.get("company_size_min") is not None:
        in_range = icp["company_size_min"] <= size <= icp["company_size_max"]
        parts.append(1.0 if in_range else 0.0)
        reasons.append(f"{'+' if in_range else '-'} {int(size)} employees")

    revenue = _to_number(lead.get("revenue"))
    if revenue is not None and icp.get("revenue_min") is not None:
        in_range = icp["revenue_min"] <= revenue <= icp["revenue_max"]
        parts.append(1.0 if in_range else 0.0)
        reasons.append(f"{'+' if in_range else '-'} revenue {int(revenue):,}")

    return mean(parts) if parts else None


def _is_generic_name(name: str, icp: dict) -> bool:
    core, adjacent, negative = _vertical_terms(icp)
    vertical_terms = [*core, *adjacent, *negative]
    tokens = [t for t in re.findall(r"[a-z0-9]+", name.lower())]
    return bool(tokens) and all(t in _GENERIC_NAME_WORDS or find_terms(t, vertical_terms) for t in tokens)


def _data_quality(lead: dict, icp: dict, name: str, reasons: list[str]) -> float:
    quality = 0.0
    postcode = str(lead.get("postcode") or "").strip().upper()
    if postcode:
        if str(icp.get("country", "")).upper() == "UK":
            quality += 0.4 if _UK_POSTCODE.match(postcode) else 0.1
        else:
            quality += 0.4
    if lead.get("address") or lead.get("city"):
        quality += 0.3
    if name and not _is_generic_name(name, icp):
        quality += 0.3
    elif name:
        reasons.append(f"- generic name '{name}'")
    return quality


def _tier(score: float, dims: dict, lead: dict, icp: dict, reasons: list[str]) -> tuple[str, bool]:
    threshold = icp.get("qualification_score_threshold", 65)
    if dims["vertical_fit"] < icp.get("min_vertical_fit", 0.5):
        return "reject", False

    channel = icp.get("required_channel", "email")
    if channel and not lead.get(channel):
        reasons.append(f"- not sendable yet: needs {channel}")
        return "C", False

    if score >= max(threshold, 80):
        return "A", True
    if score >= threshold:
        return "B", True
    return "C", False


def evaluate_lead(lead: dict, icp: dict) -> dict:
    name = str(lead.get("display_name") or lead.get("company_name") or "")
    reasons: list[str] = []

    excluded = find_terms(f"{name} {lead.get('industry') or ''}", icp.get("excluded_keywords", []))
    if excluded:
        return {
            "score": 0.0, "tier": "reject", "qualified": False, "vertical_fit": 0.0,
            "breakdown": {}, "reasons": [f"- excluded: '{excluded[0]}'"],
        }

    dims = {
        "vertical_fit": _vertical_fit(lead, icp, name, reasons),
        "contactability": _contactability(lead, reasons),
        "data_quality": _data_quality(lead, icp, name, reasons),
    }
    firmographic = _firmographic(lead, icp, reasons)
    if firmographic is not None:
        dims["firmographic"] = firmographic

    weights = {**DEFAULT_WEIGHTS, **icp.get("score_weights", {})}
    total_weight = sum(weights[k] for k in dims)
    score = round(100 * sum(weights[k] * v for k, v in dims.items()) / total_weight, 1)

    tier, qualified = _tier(score, dims, lead, icp, reasons)
    return {
        "score": score,
        "tier": tier,
        "qualified": qualified,
        "vertical_fit": dims["vertical_fit"],
        "breakdown": {k: round(v, 2) for k, v in dims.items()},
        "reasons": reasons,
    }


def score_icp(lead: dict, icp: dict) -> float:
    return evaluate_lead(lead, icp)["score"]


def meets_threshold(score: float, icp: dict) -> bool:
    return score >= icp.get("qualification_score_threshold", 65)
