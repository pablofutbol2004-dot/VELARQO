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
# so tests can change without code changes. An arm can override a follow-up
# with its own ("follow_ups": {"2": "..."}); otherwise these shared ones are used.
FOLLOW_UP_TEMPLATES = {
    # New reason to reply: answer the installer's real worry (annoying old
    # customers) by showing the exact message, then a one-word sizing question.
    2: (
        "Hi,\n\n"
        "The usual worry is annoying old customers, so here's exactly what they'd get, from your name:\n\n"
        "\"Hi, it's {company}. We quoted you for windows a while back. Did you ever get them sorted?\"\n\n"
        "That's it. Anyone who says not yet gets offered a survey. Anyone who says no is left alone.\n\n"
        "Roughly how many old quotes have you got: tens, hundreds?"
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
