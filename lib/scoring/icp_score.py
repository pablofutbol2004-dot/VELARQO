def score_icp(lead: dict, icp: dict) -> float:
    """Score a lead 0-100 against an ICP config (see config/templates/icp-template.json).

    Only scores against dimensions where data is actually available (a raw
    client CSV often lacks company_size/revenue before enrichment ever
    runs) - missing dimensions are excluded from the denominator rather
    than counted as failures, so a real industry match isn't capped below
    threshold just because enrichment hasn't filled in size/revenue yet.
    Excluded-keyword matches are a hard gate: an excluded company scores 0
    regardless of any other signal.
    """
    weights = {"size": 20.0, "revenue": 20.0, "keywords": 45.0, "exclusion": 15.0}

    text = " ".join(
        str(lead.get(field, "")) for field in ("company_name", "industry", "research_summary")
    ).lower()

    excluded = [k.lower() for k in icp.get("excluded_keywords", [])]
    if excluded and any(k in text for k in excluded):
        return 0.0

    dimensions: list[tuple[float, bool]] = []

    size = lead.get("company_size")
    if size is not None and icp.get("company_size_min") is not None:
        dimensions.append((weights["size"], icp["company_size_min"] <= size <= icp["company_size_max"]))

    revenue = lead.get("revenue")
    if revenue is not None and icp.get("revenue_min") is not None:
        dimensions.append((weights["revenue"], icp["revenue_min"] <= revenue <= icp["revenue_max"]))

    keywords = [k.lower() for k in icp.get("industry_keywords", [])]
    if keywords:
        dimensions.append((weights["keywords"], any(k in text for k in keywords)))

    if not dimensions:
        return 0.0

    total_weight = sum(weight for weight, _ in dimensions)
    achieved_weight = sum(weight for weight, passed in dimensions if passed)
    return round((achieved_weight / total_weight) * 100, 2)


def meets_threshold(score: float, icp: dict) -> bool:
    return score >= icp.get("qualification_score_threshold", 65)
