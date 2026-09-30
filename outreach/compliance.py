"""Velarqo's own cold email: the footer every email carries and the gate
every send passes. Both read truth/velarqo/, so changing the company
details or the cold email decision there changes behaviour here.

Client campaigns don't come through here: they go out from the client's
own GHL account under the client's identity (see CLAUDE.md).
"""

from lib import truth

GENERIC_TODO = truth.TODO

# PECR corporate subscribers: may be emailed without prior consent.
# English limited partnerships and anything unknown count as individuals.
CORPORATE_CATEGORIES_EXCLUDED = {"Limited Partnership"}

_REQUIRED_IDENTITY = ("legal_name", "registered_address", "privacy_notice_url")
_REQUIRED_SENDER = ("name", "email")


def footer(company: dict) -> str:
    """Sender identity + opt-out, required on every email (PECR reg 23,
    LSSI arts 20 and 22). Kept to three plain lines so it reads like a
    person's signature, not a newsletter."""
    sender = company["sender"]
    return (
        f"{sender['name']}, {company['trading_name']}\n"
        f"{company['legal_name']}, {company['registered_address']}. Privacy: {company['privacy_notice_url']}\n"
        f"{sender['opt_out_instruction']}"
    )


def setup_problems(velarqo: dict) -> list[str]:
    """Why Velarqo can't send cold email at all right now (empty = ready)."""
    problems = []
    compliance = velarqo["compliance"]
    if compliance.get("cold_email_status") != "allowed":
        problems.append(f"cold email is {compliance.get('cold_email_status')} (truth/velarqo/compliance.yaml)")
    company = velarqo["company"]
    for key in _REQUIRED_IDENTITY:
        if company.get(key) in (None, "", GENERIC_TODO):
            problems.append(f"company.{key} is not set (truth/velarqo/company.yaml)")
    for key in _REQUIRED_SENDER:
        if company["sender"].get(key) in (None, "", GENERIC_TODO):
            problems.append(f"company.sender.{key} is not set (truth/velarqo/company.yaml)")
    return problems


def lead_problems(item: dict, suppressed: set[str] = frozenset()) -> list[str]:
    """Why this one email must not go out (empty = OK to send)."""
    problems = []
    email = (item.get("email") or "").strip().lower()
    if not email:
        problems.append("no email")
    elif email in suppressed or email.split("@")[-1] in suppressed:
        problems.append("suppressed (opted out or bounced)")
    category = item.get("company_category")
    if not category or category in CORPORATE_CATEGORIES_EXCLUDED:
        problems.append(f"not a corporate subscriber under PECR ({category or 'unknown entity type'})")
    if "stop" not in (item.get("body") or "").lower():
        problems.append("body has no opt-out line")
    return problems


def velarqo_send_gate(suppressed: set[str] = frozenset()):
    """A gate for integrations/email/sender.py: item -> list of reasons it
    must not be sent. Setup problems block every item."""
    setup = setup_problems(truth.velarqo())

    def gate(item: dict) -> list[str]:
        return setup + lead_problems(item, suppressed)

    return gate
