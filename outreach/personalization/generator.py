"""Personalized email generation from a lead's research + angle.

Template-based by default. Each ICP can define its own variants; if none
are configured, a single generic variant is used.
"""

DEFAULT_VARIANTS = [
    "Hi {contact_name},\n\n{angle}\n\n{research_summary}\n\n"
    "Worth a quick 15-minute call this week?\n\n{sender_name}",
]


def generate_email(lead: dict, icp: dict, variant_index: int = 0, sender_name: str = "The Team") -> dict:
    variants = icp.get("email_templates") or DEFAULT_VARIANTS
    template = variants[variant_index % len(variants)]

    body = template.format(
        contact_name=lead.get("contact_name") or lead.get("company_name", "there"),
        angle=lead.get("angle", ""),
        research_summary=lead.get("research_summary", ""),
        sender_name=sender_name,
    )

    return {
        "lead_id": lead["id"],
        "company_name": lead.get("company_name"),
        "email": lead.get("email"),
        "variant_index": variant_index,
        "subject": f"Quick idea for {lead.get('company_name', 'you')}",
        "body": body,
    }


def generate_campaign_emails(leads: list[dict], icp: dict, sender_name: str = "The Team") -> list[dict]:
    variant_count = icp.get("email_variants", 1)
    emails = []
    for i, lead in enumerate(leads):
        if lead.get("duplicate_of") or not lead.get("qualified"):
            continue
        variant_index = i % variant_count
        emails.append(generate_email(lead, icp, variant_index, sender_name))
    return emails
