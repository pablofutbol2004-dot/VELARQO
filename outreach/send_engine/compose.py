"""Email copy for Velarqo's own cold outreach to window and door installers.

Rules (from the ad pack's outbound/copywriting essentials and
.claude/skills/velarqo-outreach):
- Talk like one tradesperson to another. No agency words ("campaigns",
  "performance-based", "solutions"), no scraper-tell personalisation.
- One idea, one small ask that can be answered with a one-line reply.
- Every follow-up gives a new reason to reply; never "just bumping this".
- No claims we can't back: no results, clients or percentages.
- Every email says who we are and how to opt out.
"""

import os
import re

from outreach.send_engine import guards

SIGNATURE = "Pablo\nVelarqo, velarqo.com"
OPT_OUT_LINE = "Reply \"no\" and I won't email again."
MAX_WORDS = 80  # whole email, signature and opt-out included

# US (CAN-SPAM) footer: who we are (real name + business), a physical postal
# address from VELARQO_POSTAL_ADDRESS, and a plain opt-out. Replying "no" or
# "unsubscribe" is honoured by the reply classifier / suppression list.
US_OPT_OUT_LINE = "Reply \"no\" or \"unsubscribe\" and I won't email you again."
US_WORD_ALLOWANCE = 5  # the longer US footer (address words are not counted at all)


class PostalAddressMissing(ValueError):
    """US email needs VELARQO_POSTAL_ADDRESS; without it nothing US is written or sent."""


def sender_name() -> str:
    return " ".join((os.environ.get("VELARQO_SENDER_NAME") or "Pablo").split())


def business_name() -> str:
    return " ".join((os.environ.get("VELARQO_BUSINESS_NAME") or "Velarqo").split())


def us_signature() -> str:
    address = guards.postal_address()
    if not address:
        raise PostalAddressMissing(
            "VELARQO_POSTAL_ADDRESS is unset or not a US street address with a ZIP code: refusing to write US email")
    return f"{sender_name()}\n{business_name()}, velarqo.com\n{address}"

# First-email copy lives in config/experiments/*.json (one arm per variant),
# so tests can change without code changes. An arm can override a follow-up
# with its own ("follow_ups": {"2": "..."}); otherwise these shared ones are used.
FOLLOW_UP_TEMPLATES = {
    # New reason to reply (email 1 already showed the homeowner text): what
    # they get back, a start that needs no data, then a one-word sizing question.
    # Approved 2026-10-11 (docs/COLD_EMAIL_V2.md).
    2: (
        "Hi,\n\n"
        "What you'd get back: a short list of homeowners who replied \"yes, still interested\", "
        "each with a survey time in your diary. Anyone who says no is left alone for good.\n\n"
        "No spreadsheet needed to start. Read me five old quotes on a ten-minute call "
        "and I'll tell you if they're worth chasing.\n\n"
        "Roughly how many have you got: tens, hundreds?"
    ),
    # Close the loop, and ask for the right person in case it's not them.
    3: (
        "Hi,\n\n"
        "Last one from me.\n\n"
        "If old quotes aren't worth chasing right now, fair enough. "
        "If someone else at {company} looks after quotes, who's best to speak to?"
    ),
}

_PLACEHOLDER = re.compile(r"\[[^\]]+\]|\{[a-z_]+\}")


_LEGAL_SUFFIX = re.compile(r"[\s,.]+(ltd\.?|limited|llp)\s*$", re.IGNORECASE)
KEEP_UPPER = {"UPVC", "PVC", "PVCU", "UK", "GB", "NI"}


def _title_word(word: str) -> str:
    core = word.strip("()[],.&")
    if core in KEEP_UPPER or any(ch.isdigit() for ch in word):
        return word
    if len(core) <= 3 and core.isalpha() and not set(core) & set("AEIOUY"):
        return word  # initials like "JB" or "MTS"
    return "-".join(part[:1].upper() + part[1:].lower() for part in word.split("-"))


def clean_company(name: str) -> str:
    """How a person would write the name: no 'Ltd'/'Limited'/'LLP' on the end,
    and 'ACME WINDOWS LTD' -> 'Acme Windows' (acronyms like UPVC kept)."""
    name = " ".join((name or "").split())
    while True:
        shorter = _LEGAL_SUFFIX.sub("", name).strip()
        if shorter == name or not shorter:
            break
        name = shorter
    if name.isupper():
        name = " ".join(_title_word(w) for w in name.split())
    return name


def _company(row: dict) -> str:
    return clean_company(row.get("display_name") or "") or "your company"


def first_name(row: dict) -> str | None:
    """The company's only director's first name, if it's a real name."""
    name = (row.get("director_first_name") or "").strip()
    if len(name) < 2 or not name.replace("-", "").replace("'", "").isalpha():
        return None
    return name[:1].upper() + name[1:].lower() if name.isupper() or name.islower() else name


def _greet(body: str, row: dict) -> str:
    name = first_name(row)
    return f"Hi {name},{body[3:]}" if name and body.startswith("Hi,") else body


def _fill(template: str, company: str) -> str:
    """Insert the company name, with a correct possessive for names ending
    in s ("Leeds Windows And Doors' inbox", not "Doors's")."""
    text = template.format(company=company)
    if company.endswith(("s", "S")):
        text = text.replace(f"{company}'s", f"{company}'")
    return text


def _finish(body: str, market: str = "UK") -> str:
    if market == "US":
        return f"{body.rstrip()}\n\n{us_signature()}\n\n{US_OPT_OUT_LINE}\n"
    return f"{body.rstrip()}\n\n{SIGNATURE}\n\n{OPT_OUT_LINE}\n"


def first_touch(row: dict, experiment: dict, variant_index: int) -> dict:
    index = variant_index % len(experiment["arms"])
    arm = experiment["arms"][index]
    company = _company(row)
    market = guards.normalise_market(experiment.get("market"))
    return {
        "variant_index": index,
        "arm": arm["key"],
        "company": company,
        "market": market,
        "subject": _fill(arm["subject"], company),
        "body": _finish(_greet(_fill(arm["body"], company), row), market),
    }


def follow_up(step: int, row: dict, first_subject: str, arm: dict | None = None, market: str = "UK") -> dict:
    if market == "US":
        # Same subject, threaded by headers: a "Re:" here would pretend they wrote first.
        subject = guards.strip_thread_prefix(first_subject)
    else:
        subject = first_subject if first_subject.lower().startswith("re:") else f"Re: {first_subject}"
    template = ((arm or {}).get("follow_ups") or {}).get(str(step)) or FOLLOW_UP_TEMPLATES[step]
    return {"subject": subject, "market": market, "body": _finish(_greet(_fill(template, _company(row)), row), market)}


def legal_problems(email: dict) -> list[str]:
    """CAN-SPAM checks for a US email: honest subject, sender identity, postal
    address (the current VELARQO_POSTAL_ADDRESS, which must be set), opt-out."""
    issues = []
    address = guards.postal_address()
    body = email["body"]
    if guards.deceptive_subject(email["subject"]):
        issues.append("deceptive or empty subject")
    if not address:
        issues.append("VELARQO_POSTAL_ADDRESS unset or not a US address")
    elif address not in body:
        issues.append("missing postal address")
    if sender_name() not in body or business_name() not in body:
        issues.append("missing sender name or business name")
    if US_OPT_OUT_LINE not in body:
        issues.append("missing opt-out line")
    return issues


def problems(email: dict) -> list[str]:
    """Reasons an email must not go out as written."""
    issues = []
    text = f"{email['subject']}\n{email['body']}"
    us = email.get("market", "UK") == "US"
    if _PLACEHOLDER.search(text):
        issues.append("unfilled placeholder")
    if us:
        issues += legal_problems(email)
    elif OPT_OUT_LINE not in email["body"]:
        issues.append("missing opt-out line")
    if "velarqo.com" not in email["body"]:
        issues.append("missing sender identity")
    body, cap = email["body"], MAX_WORDS
    if us:
        body, cap = body.replace(guards.postal_address() or "", ""), MAX_WORDS + US_WORD_ALLOWANCE
    if word_count(body, email.get("company")) > cap:
        issues.append(f"over {cap} words")
    return issues


def word_count(body: str, company: str | None = None) -> int:
    """Words the reader has to read. A company name counts as one word, so a
    long trading name never pushes good copy over the cap."""
    words = len(body.split())
    if company and len(company.split()) > 1:
        words -= body.count(company) * (len(company.split()) - 1)
    return words
