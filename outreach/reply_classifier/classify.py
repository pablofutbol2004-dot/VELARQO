"""Reply sentiment classification. Keyword-based by default (no API key
required). Swap classify_reply for an LLM-backed version once configured.
"""

_POSITIVE_PHRASES = [
    "interested", "sounds good", "let's talk", "book a call",
    "send over", "yes please", "would like to know more", "schedule",
]
_NEGATIVE_PHRASES = [
    "not interested", "unsubscribe", "remove me", "no thanks",
    "stop emailing", "not looking", "already have a provider",
]


def classify_reply(reply_text: str) -> str:
    text = (reply_text or "").lower()

    if any(phrase in text for phrase in _NEGATIVE_PHRASES):
        return "negative"
    if any(phrase in text for phrase in _POSITIVE_PHRASES):
        return "positive"
    return "maybe"
