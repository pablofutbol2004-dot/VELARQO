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

import re

SIGNATURE = "Pablo\nVelarqo, velarqo.com"
OPT_OUT_LINE = "Reply \"no\" and I won't email again."
MAX_WORDS = 80  # whole email, signature and opt-out included

# First-email copy lives in config/experiments/*.json (one arm per variant),
# so tests can change without code changes. Follow-ups are shared by all arms.
FOLLOW_UP_TEMPLATES = {
    # New reason to reply: what actually happens, in concrete steps (email 1
    # already asked the "how many quotes" question, so don't repeat it).
    2: (
        "Hi,\n\n"
        "To make it concrete: I'd send a short message in your company's name to homeowners you quoted in "
        "the last year or two, asking if they're still thinking about it. Anyone who says yes gets a survey "
        "booked into your diary. Anyone who says no is left alone.\n\n"
        "Want a bit more detail?"
    ),
    # Close the loop politely and leave the door open.
    3: (
        "Hi,\n\n"
        "Last one from me. If chasing old quotes isn't on your list right now, fair enough.\n\n"
        "If it ever is, just reply to this and I'll pick it up."
    ),
}

_PLACEHOLDER = re.compile(r"\[[^\]]+\]|\{[a-z_]+\}")


def _company(row: dict) -> str:
    return (row.get("display_name") or "your company").strip()


def _finish(body: str) -> str:
    return f"{body.rstrip()}\n\n{SIGNATURE}\n\n{OPT_OUT_LINE}\n"


def first_touch(row: dict, experiment: dict, variant_index: int) -> dict:
    index = variant_index % len(experiment["arms"])
    arm = experiment["arms"][index]
    return {
        "variant_index": index,
        "arm": arm["key"],
        "subject": arm["subject"].format(company=_company(row)),
        "body": _finish(arm["body"].format(company=_company(row))),
    }


def follow_up(step: int, row: dict, first_subject: str, arm: dict | None = None) -> dict:
    subject = first_subject if first_subject.lower().startswith("re:") else f"Re: {first_subject}"
    template = ((arm or {}).get("follow_ups") or {}).get(str(step)) or FOLLOW_UP_TEMPLATES[step]
    return {"subject": subject, "body": _finish(template.format(company=_company(row)))}


def problems(email: dict) -> list[str]:
    """Reasons an email must not go out as written."""
    issues = []
    text = f"{email['subject']}\n{email['body']}"
    if _PLACEHOLDER.search(text):
        issues.append("unfilled placeholder")
    if OPT_OUT_LINE not in email["body"]:
        issues.append("missing opt-out line")
    if "velarqo.com" not in email["body"]:
        issues.append("missing sender identity")
    if word_count(email["body"]) > MAX_WORDS:
        issues.append(f"over {MAX_WORDS} words")
    return issues


def word_count(body: str) -> int:
    return len(body.split())
