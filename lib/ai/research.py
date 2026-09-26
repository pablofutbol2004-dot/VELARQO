"""Company research + outreach angle generation.

Template-based by default (no API key required). Swap generate_research/
generate_angle for LLM-backed versions once an AI provider is configured.
"""


def generate_research_summary(lead: dict) -> str:
    company = lead.get("company_name", "This company")
    industry = lead.get("industry", "their industry")
    size = lead.get("company_size")

    size_clause = f" with roughly {int(size)} employees" if size else ""
    return f"{company} operates in {industry}{size_clause}."


def generate_angle(lead: dict, icp: dict) -> str:
    company = lead.get("company_name", "your company")
    vertical = icp.get("vertical", "your industry")
    return (
        f"Noticed {company} is active in {vertical} — we help similar "
        f"businesses recover lost quotes and book more appointments from "
        f"their existing pipeline."
    )


def research_lead(lead: dict, icp: dict) -> dict:
    if lead.get("duplicate_of") or not lead.get("qualified"):
        return lead
    return {
        **lead,
        "research_summary": generate_research_summary(lead),
        "angle": generate_angle(lead, icp),
    }


def research_leads(leads: list[dict], icp: dict) -> list[dict]:
    return [research_lead(lead, icp) for lead in leads]
