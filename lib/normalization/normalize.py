import re

_COMPANY_SUFFIXES = re.compile(
    r"\b(ltd|limited|llc|inc|incorporated|plc|llp|corp|corporation|co)\b\.?",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_UK_POSTCODE_RE = re.compile(r"^([A-Z]{1,2}\d[A-Z\d]?)\s*(\d[A-Z]{2})$", re.IGNORECASE)


def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    cleaned = name.strip()
    cleaned = _COMPANY_SUFFIXES.sub("", cleaned)
    cleaned = re.sub(r"[&,.]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.title()


def normalize_email(email: str) -> str | None:
    if not email:
        return None
    cleaned = email.strip().lower()
    return cleaned if _EMAIL_RE.match(cleaned) else None


_MIN_PHONE_DIGITS = 9


def normalize_phone(phone: str, default_country_code: str = "44") -> str | None:
    if not phone:
        return None
    digits = re.sub(r"[^\d+]", "", str(phone))
    if sum(c.isdigit() for c in digits) < _MIN_PHONE_DIGITS:
        return None
    if digits.startswith("+"):
        return digits
    if digits.startswith("00"):
        return "+" + digits[2:]
    if digits.startswith("0"):
        return f"+{default_country_code}{digits[1:]}"
    return f"+{digits}"


def normalize_postcode(postcode: str) -> str | None:
    if not postcode:
        return None
    cleaned = postcode.strip().upper().replace(" ", "")
    match = re.match(r"^([A-Z]{1,2}\d[A-Z\d]?)(\d[A-Z]{2})$", cleaned)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return cleaned or None


def normalize_lead(raw: dict) -> dict:
    # company_name is a matching key (suffixes/punctuation stripped for
    # dedupe); display_name keeps the real name for anything a human reads.
    display_name = raw.get("display_name") or re.sub(r"\s+", " ", str(raw.get("company_name") or "")).strip()
    return {
        **raw,
        "display_name": display_name,
        "company_name": normalize_company_name(raw.get("company_name", "")),
        "email": normalize_email(raw.get("email", "")),
        "phone": normalize_phone(raw.get("phone", "")),
        "postcode": normalize_postcode(raw.get("postcode", "")),
        "normalized": True,
    }
