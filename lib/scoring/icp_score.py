def score_icp(lead: dict, icp: dict) -> float:
    """Score a lead 0-100 against an ICP config (see config/templates/icp-template.json)."""
    score = 0.0
    weights = {"size": 20.0, "revenue": 20.0, "keywords": 45.0, "exclusion": 15.0}

    size = lead.get("company_size")
    if size is not None and icp.get("company_size_min") is not None:
        if icp["company_size_min"] <= size <= icp["company_size_max"]:
            score += weights["size"]

    revenue = lead.get("revenue")
    if revenue is not None and icp.get("revenue_min") is not None:
        if icp["revenue_min"] <= revenue <= icp["revenue_max"]:
            score += weights["revenue"]

    text = " ".join(
        str(lead.get(field, "")) for field in ("company_name", "industry", "research_summary")
    ).lower()

    keywords = [k.lower() for k in icp.get("industry_keywords", [])]
    if keywords and any(k in text for k in keywords):
        score += weights["keywords"]

    excluded = [k.lower() for k in icp.get("excluded_keywords", [])]
    if not excluded or not any(k in text for k in excluded):
        score += weights["exclusion"]

    return round(score, 2)


def meets_threshold(score: float, icp: dict) -> bool:
    return score >= icp.get("qualification_score_threshold", 65)
