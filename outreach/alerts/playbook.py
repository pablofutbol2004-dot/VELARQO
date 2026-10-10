"""The reply to suggest for each kind of inbound, lifted from
docs/SALES_PLAYBOOK.md section 1 (keep the two in step: the playbook is the
source, this is what the phone shows). Every suggestion is a draft to read
and adjust, never sent automatically.

The "send info" text is read from docs/delivery/01_send_info_email.md so the
alert carries the current version.
"""

from pathlib import Path

ROOT = Path(__file__).parents[2]
SEND_INFO_DOC = ROOT / "docs" / "delivery" / "01_send_info_email.md"

INTERESTED = (
    "Thanks {name}. Simple version: you send me a list of quotes that went quiet, I follow those homeowners up "
    "in {company}'s name, and anyone who's still interested gets booked back in for a survey. You only pay for "
    "surveys that get booked.\n\n"
    "Easiest is a 15-minute call so I can see if your old quotes are worth doing. What day suits, or what's the "
    "best number to ring you on?"
)
HOW_MUCH = (
    "No setup fee, and you only pay for surveys that get booked.\n"
    "The exact number depends on how many old quotes you've got and what a job's worth to you, so it's easier "
    "on a quick 15-minute call. When suits?"
)
CALL_ME = (
    "Ring them, now if it's 08:30-17:00 UK. Before the call: `python -m pipelines.outbound call-sheet {email}` "
    "(history and the price arm to quote). After: `outcome {email} call_held --reaction ok|hesitant|objected`."
)
ALREADY_FOLLOW_UP = (
    "Good, a lot don't. Out of interest, what happens after the second or third chase? If every quote gets to a "
    "clear yes or no, this probably isn't for you and I'll leave you be."
)
GDPR_QUESTION = (
    "Answer it yourself, never with a template. Say where the address came from (their website / Companies "
    "House listing), that you only email limited companies, not individuals, and that you've removed them if "
    "they want that. Then `python -m pipelines.outbound suppress {email}` if they ask. The legitimate interests "
    "assessment is in docs/legal/."
)
WRONG_PERSON = (
    "Thank them, then email the person they named (one line: who you are, what the first email said, same "
    "small ask). Add the new contact with `suppress`/`call-sheet` as needed; don't re-send the whole sequence "
    "to the old address."
)
LATER = (
    "Reply once: \"No problem, I'll come back to you in {when}. If anything changes before then, my number's "
    "below.\" Then log it: `outcome {email} lost --note \"later: {when}\"` so the next slice doesn't re-touch them "
    "too early."
)
MIXED = (
    "Read the whole reply before anything else. It has both a no and a yes in it, so nothing was suppressed "
    "automatically. If it's a no, `handled {reply_id} --as not_interested`. If it's a conversation, answer the "
    "question they actually asked."
)
QUESTION = "Answer the question in one or two lines, then ask for the 15-minute call."
COMPLAINT = (
    "Sending is PAUSED for every mailbox until you review this. Don't reply to argue. If they asked for "
    "deletion or a subject access request, answer that within a month (docs/legal/). Then "
    "`python -m pipelines.outbound handled {reply_id}` and `sending on` once you're sure the rest of the list is fine."
)
NOT_INTERESTED = "Already suppressed. Don't reply. `handled {reply_id}`."
UNSUBSCRIBE = "Already suppressed. Don't reply. `handled {reply_id}`."
UNMATCHED = (
    "This reply couldn't be tied to an email we sent (forwarded from another address?). Search the sending "
    "mailbox for the thread, then treat it like any other reply."
)
YES = "They said yes with no detail: ask for the call straight away.\n\n" + INTERESTED


def send_info_text(company: str = "{company}") -> str:
    """The body of docs/delivery/01_send_info_email.md (between the two '---' rules)."""
    if not SEND_INFO_DOC.exists():
        return "Send docs/delivery/01_send_info_email.md (file not found here)."
    text = SEND_INFO_DOC.read_text(encoding="utf-8")
    parts = text.split("\n---\n")
    body = parts[1].strip() if len(parts) >= 3 else text
    return body.replace("{company}", company)


def suggestion(category: str, intent: str | None, *, name: str = "", company: str = "", email: str = "",
               reply_id: str = "", matched: bool = True, arm: str | None = None) -> str:
    """The playbook reply (or instruction) for one inbound."""
    fill = dict(name=name or "", company=company or "your company", email=email, reply_id=reply_id, when="a few months")
    if not matched and category not in ("complaint", "unsubscribe", "not_interested"):
        return UNMATCHED
    if category == "complaint":
        return COMPLAINT.format(**fill)
    if category == "unsubscribe":
        return UNSUBSCRIBE.format(**fill)
    if category == "not_interested":
        return NOT_INTERESTED.format(**fill)
    if category == "positive":
        text = {
            "call_me": CALL_ME, "how_much": HOW_MUCH, "send_info": None, "yes": YES,
        }.get(intent, INTERESTED)
        if intent == "send_info":
            text = "Reply in the same thread with (docs/delivery/01_send_info_email.md):\n\n" + send_info_text(fill["company"])
            if arm and arm.startswith("B"):
                text += "\n\n(Arm B, first 50 free: swap steps 2-4 for \"I'll chase your first 50 for free, so you can see it work before paying anything.\")"
            return text
        return text.format(**fill)
    # unknown
    return {
        "gdpr_question": GDPR_QUESTION, "wrong_person": WRONG_PERSON, "already_follow_up": ALREADY_FOLLOW_UP,
        "later": LATER, "mixed": MIXED, "question": QUESTION,
    }.get(intent, "Read it and decide. If it's a conversation, aim for the 15-minute call.").format(**fill)
