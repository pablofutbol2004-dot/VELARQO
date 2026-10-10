"""Reply classification. Keyword-based by default (no API key required).

classify_reply() returns the coarse sentiment used by experiment tracking.
categorize_reply() is what the send engine acts on: it decides whether a
reply suppresses the sender, stops the sequence, or needs a human.

Always classify the *new* text only: our own email sits quoted underneath
most replies and contains "Reply 'no'", which would otherwise read as an
opt-out on every reply. Signatures and disclaimers are cut off too: they
contain words like "spam", "ICO" and "GDPR" in perfectly friendly replies.
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
# Explicit accusations only. Bare words like "spam", "ICO", "GDPR" or "data
# protection" appear in ordinary footers ("scanned for spam", "ICO
# registration Z123", "in line with GDPR") and must not trigger a complaint.
_COMPLAINT_PATTERNS = [
    r"this is spam", r"\bspamm(ing|er)\b", r"\bspam (email|mail|message)s?\b", r"\breport(ed|ing)? (you|this)\b",
    r"complain(t|ing)? to the ico", r"(report|refer)\w* (it |this |you )?to the (ico|information commissioner)",
    r"how did you get (my|our|this) (email|address|details)", r"where did you get (my|our|this)",
    r"\bharass", r"unsolicited (email|mail|marketing)", r"breach of (gdpr|pecr|the regulations)",
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
# "Delivery Status Notification (Delay)" is a warning, not a failure.
_NOT_A_BOUNCE = ("delay", "delayed", "warning", "will retry", "still trying")
# Where a reply's own words end and the signature/disclaimer starts.
_SIGNATURE_START = re.compile(
    r"^\s*(--\s*$|kind regards|best regards|warm regards|regards\b|many thanks|thanks,?\s*$|cheers,?\s*$|"
    r"registered (in|office|company)|company (registration|reg)|this (e-?mail|message) (and any|is confidential|may)|"
    r"disclaimer|confidentiality|vat (no|number|reg))",
    re.IGNORECASE,
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


def own_words(new_text: str) -> str:
    """The message before the signature/disclaimer (always keeps line one)."""
    lines = new_text.splitlines()
    for i, line in enumerate(lines):
        if i > 0 and _SIGNATURE_START.match(line):
            return "\n".join(lines[:i]).strip()
    return new_text


def _has(text: str, phrases) -> bool:
    return any(re.search(rf"(?<![a-z]){re.escape(p)}(?![a-z])", text) for p in phrases)


def categorize_reply(from_email: str, subject: str, body: str, auto_submitted: bool = False) -> dict:
    """-> {"category", "sentiment", "suppress", "stops_sequence", "needs_human"}

    Opt-outs and complaints are checked before out-of-office, so "I'm away,
    but please remove us" is an opt-out. `auto_submitted` comes from the
    Auto-Submitted / X-Autoreply / Precedence headers (helpdesk auto-acks)."""
    sender = (from_email or "").lower()
    subj = (subject or "").lower()
    new_text = own_words(strip_quoted(body).lower())
    first_line = new_text.splitlines()[0] if new_text else ""

    bounce_like = sender.startswith(_BOUNCE_SENDERS) or any(s in subj for s in _BOUNCE_SUBJECTS)
    if bounce_like and not any(w in subj for w in _NOT_A_BOUNCE):
        category = "bounce"
    elif bounce_like:
        category = "out_of_office"            # a delay warning: an automatic notice, not a person
    elif any(re.search(p, new_text) for p in _COMPLAINT_PATTERNS):
        category = "complaint"
    elif _BARE_OPT_OUT.match(new_text) or _BARE_OPT_OUT.match(first_line) or _has(new_text, _UNSUBSCRIBE_PHRASES):
        category = "unsubscribe"
    elif auto_submitted or _has(f"{subj} {new_text}", _OUT_OF_OFFICE_PHRASES):
        category = "out_of_office"
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
        # a person reads every human reply (volume is tiny), so a wrong
        # automatic opt-out of an interested firm is caught the same day
        "needs_human": category not in ("bounce", "out_of_office"),
    }
