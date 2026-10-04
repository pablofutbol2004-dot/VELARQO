"""Reply classification. Keyword-based by default (no API key required).

classify_reply() returns the coarse sentiment used by experiment tracking.
categorize_reply() is what the send engine acts on: it decides whether a
reply suppresses the sender, stops the sequence, or needs a human.

Always classify the *new* text only: our own email sits quoted underneath
most replies and contains "Reply 'no'", which would otherwise read as an
opt-out on every reply.
"""

import re

_POSITIVE_PHRASES = [
    "interested", "sounds good", "let's talk", "book a call",
    "send over", "yes please", "would like to know more", "schedule",
    "give me a call", "call me", "ring me", "tell me more", "more info",
    "how does it work", "happy to chat", "go on then",
]
_NEGATIVE_PHRASES = [
    "not interested", "unsubscribe", "remove me", "no thanks",
    "stop emailing", "not looking", "already have a provider",
    "no thank you", "not for us", "not at this time", "we're fine", "we are fine",
]
_UNSUBSCRIBE_PHRASES = [
    "unsubscribe", "remove me", "remove us", "take me off", "take us off",
    "stop emailing", "stop contacting", "do not contact", "don't contact",
    "do not email", "don't email", "opt out", "opt-out",
]
_COMPLAINT_PHRASES = [
    "spam", "reported", "report you", "ico", "gdpr", "data protection",
    "how did you get", "where did you get", "harass",
]
_OUT_OF_OFFICE_PHRASES = [
    "out of office", "out of the office", "automatic reply", "auto-reply", "autoreply",
    "annual leave", "on holiday", "away from the office", "currently away",
    "limited access to email", "will respond on my return", "back in the office",
]
_BOUNCE_SENDERS = ("mailer-daemon@", "postmaster@")
_BOUNCE_SUBJECTS = (
    "undeliverable", "delivery status notification", "mail delivery failed",
    "returned mail", "delivery has failed", "failure notice", "undelivered mail",
)
# A one-word "no" / "stop" is exactly what our footer asks people to send.
_BARE_OPT_OUT = re.compile(r"^\W*(no|nope|stop|unsubscribe|remove)\W*$")

CATEGORIES = ("bounce", "out_of_office", "unsubscribe", "complaint", "not_interested", "positive", "unknown")


def classify_reply(reply_text: str) -> str:
    text = (reply_text or "").lower()

    if any(phrase in text for phrase in _NEGATIVE_PHRASES):
        return "negative"
    if any(phrase in text for phrase in _POSITIVE_PHRASES):
        return "positive"
    return "maybe"


def strip_quoted(body: str) -> str:
    """The reply's own new text: drop quoted lines and everything after an
    'On ... wrote:' / 'From:' / '-----Original Message-----' marker."""
    lines = []
    for line in (body or "").splitlines():
        stripped = line.strip()
        if re.match(r"^on .+wrote:?$", stripped, re.IGNORECASE) or re.match(
            r"^(-{2,}\s*original message\s*-{2,}|from:\s.+|sent from my )", stripped, re.IGNORECASE
        ):
            break
        if stripped.startswith(">"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _has(text: str, phrases) -> bool:
    return any(re.search(rf"(?<![a-z]){re.escape(p)}(?![a-z])", text) for p in phrases)


def categorize_reply(from_email: str, subject: str, body: str) -> dict:
    """-> {"category", "sentiment", "suppress", "stops_sequence", "needs_human"}"""
    sender = (from_email or "").lower()
    subj = (subject or "").lower()
    new_text = strip_quoted(body).lower()

    if sender.startswith(_BOUNCE_SENDERS) or any(s in subj for s in _BOUNCE_SUBJECTS):
        category = "bounce"
    elif _has(f"{subj} {new_text}", _OUT_OF_OFFICE_PHRASES):
        category = "out_of_office"
    elif _has(new_text, _COMPLAINT_PHRASES):
        category = "complaint"
    elif _BARE_OPT_OUT.match(new_text) or _has(new_text, _UNSUBSCRIBE_PHRASES):
        category = "unsubscribe"
    elif _has(new_text, _NEGATIVE_PHRASES):
        category = "not_interested"
    elif _has(new_text, _POSITIVE_PHRASES):
        category = "positive"
    else:
        category = "unknown"

    return {
        "category": category,
        "sentiment": {"positive": "positive", "unknown": "maybe"}.get(
            category, None if category in ("bounce", "out_of_office") else "negative"
        ),
        # bounce suppresses the address; people who said no are never emailed again
        "suppress": category in ("bounce", "unsubscribe", "complaint", "not_interested"),
        # an auto-reply is not a person answering, so the sequence carries on
        "stops_sequence": category not in ("out_of_office",),
        "needs_human": category in ("positive", "unknown", "complaint"),
    }
