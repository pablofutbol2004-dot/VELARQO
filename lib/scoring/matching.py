import re
from urllib.parse import urlparse

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_MAX_INFLECTION = 3

FREEMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "hotmail.com", "hotmail.co.uk", "outlook.com", "live.com",
    "live.co.uk", "yahoo.com", "yahoo.co.uk", "icloud.com", "aol.com", "btinternet.com",
    "sky.com", "virginmedia.com", "talktalk.net", "mail.com",
}


def normalize_text(text) -> str:
    if not text:
        return ""
    return _NON_ALNUM.sub(" ", str(text).lower()).strip()


def _word_matches(token: str, word: str) -> bool:
    # Allows short inflections (window -> windows, glazier -> glaziers,
    # conservator -> conservatories) without letting "car" match "cardiff".
    return token == word or (token.startswith(word) and len(token) - len(word) <= _MAX_INFLECTION)


def find_terms(text, terms) -> list[str]:
    """Terms present in text. Multi-word terms match as phrases, with the
    last word allowed to inflect ("garage door" matches "garage doors")."""
    tokens = normalize_text(text).split()
    if not tokens:
        return []

    found = []
    for term in terms:
        words = normalize_text(term).split()
        if not words:
            continue
        n = len(words)
        for i in range(len(tokens) - n + 1):
            if tokens[i:i + n - 1] == words[:-1] and _word_matches(tokens[i + n - 1], words[-1]):
                found.append(term)
                break
    return found


def find_terms_in_domain(domain: str, terms, min_length: int = 4) -> list[str]:
    """Domains are run together ("repairmywindowsanddoors"), so match terms
    as substrings of the first label rather than as whole words."""
    label = re.sub(r"[^a-z0-9]", "", domain.lower().removeprefix("www.").split(".")[0])
    found = []
    for term in terms:
        squashed = re.sub(r"[^a-z0-9]", "", term.lower())
        if len(squashed) >= min_length and squashed in label:
            found.append(term)
    return found


def lead_domain(lead: dict) -> str | None:
    website = lead.get("website")
    if isinstance(website, str) and website.strip():
        url = website.strip() if "://" in website else f"http://{website.strip()}"
        host = (urlparse(url).hostname or "").lower()
        if host:
            return host.removeprefix("www.")

    email = lead.get("email")
    if isinstance(email, str) and "@" in email:
        domain = email.rsplit("@", 1)[1].lower()
        if domain not in FREEMAIL_DOMAINS:
            return domain
    return None
