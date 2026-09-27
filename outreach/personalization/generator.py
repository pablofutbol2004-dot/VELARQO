"""Personalized cold email generation from a researched lead.

Three structurally different default variants (observation-led, direct,
question-led) so A/B results in experiment_result actually mean something.
An ICP can override them via "email_templates": [{"subject", "body"}].

Template fields: {greeting} {company} {city} {label} {observation}
{angle_sentence} {offer_line} {sender_name}. Unknown/missing fields render
as empty rather than raising, and blank lines left behind are collapsed.
"""

import re

DEFAULT_TEMPLATES = [
    {
        "subject": "old quotes at {company}",
        "body": (
            "{greeting}\n\n{observation}\n\n{angle_sentence}\n\n{offer_line}\n\n"
            "Worth a quick 10-minute call to see if it'd work for {company}?\n\n{sender_name}"
        ),
    },
    {
        "subject": "{company} - quick idea",
        "body": (
            "{greeting}\n\n{angle_sentence}\n\n{offer_line}\n\n"
            "Would it be worth a quick chat to see what's sitting in your old quotes?\n\n{sender_name}"
        ),
    },
    {
        "subject": "question about your follow-ups",
        "body": (
            "{greeting}\n\nQuick question: when a quote goes out and the customer goes quiet, "
            "what happens next at {company}?\n\n{angle_sentence}\n\n{offer_line}\n\n"
            "If that's something you'd want a hand with, reply and I'll send over how it works.\n\n{sender_name}"
        ),
    },
]

DEFAULT_OFFER_LINE = (
    "We run follow-up campaigns on those old quotes for {trade} and turn a share of them into booked "
    "appointments. It's performance-based, so there's nothing to pay unless it works."
)


class _BlankMissing(dict):
    def __missing__(self, key):
        return ""


def _sentence(fragment: str) -> str:
    fragment = (fragment or "").strip().rstrip(".")
    return f"{fragment[0].upper()}{fragment[1:]}." if fragment else ""


def _fields(lead: dict, icp: dict, sender_name: str | None) -> dict:
    trade = icp.get("trade_noun") or f"{icp.get('vertical', 'local')} businesses"
    first_name = (lead.get("contact_name") or "").split(" ")[0]
    return {
        "greeting": f"Hi {first_name}," if first_name else "Hi there,",
        "company": lead.get("display_name") or lead.get("company_name") or "your company",
        "city": lead.get("city") or "",
        "label": lead.get("industry_label") or icp.get("vertical_label") or "",
        "observation": lead.get("observation") or "",
        "angle_sentence": _sentence(lead.get("angle") or ""),
        "offer_line": (icp.get("offer_line") or DEFAULT_OFFER_LINE).format(trade=trade),
        "sender_name": sender_name or icp.get("sender_name") or "[Your name]",
    }


def _render(template: str, fields: dict) -> str:
    text = template.format_map(_BlankMissing(fields))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def generate_email(lead: dict, icp: dict, variant_index: int = 0, sender_name: str | None = None) -> dict:
    templates = icp.get("email_templates") or DEFAULT_TEMPLATES
    template = templates[variant_index % len(templates)]
    fields = _fields(lead, icp, sender_name)

    return {
        "lead_id": lead["id"],
        "company_name": lead.get("display_name") or lead.get("company_name"),
        "email": lead.get("email"),
        "variant_index": variant_index % len(templates),
        "subject": _render(template["subject"], fields),
        "body": _render(template["body"], fields) + "\n",
    }


def generate_campaign_emails(leads: list[dict], icp: dict, sender_name: str | None = None) -> list[dict]:
    variant_count = len(icp.get("email_templates") or DEFAULT_TEMPLATES)
    sendable = [lead for lead in leads if lead.get("qualified") and not lead.get("duplicate_of")]
    return [generate_email(lead, icp, i % variant_count, sender_name) for i, lead in enumerate(sendable)]
