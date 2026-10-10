"""Homeowner contact details, normalised for texting UK mobiles.

The generic normaliser turned Excel-mangled numbers into foreign ones
(7700900123 -> +7700900123, Kazakhstan). Here a number only counts as a
textable phone if it is a UK mobile (+447 and 9 more digits); anything else
is treated as "no phone" rather than guessed.
"""

import re

from lib.normalization.normalize import normalize_email

_UK_MOBILE = re.compile(r"^\+447\d{9}$")


def uk_mobile(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    text = re.sub(r"\.0+$", "", text)             # pandas read the column as float: 7700900123.0
    digits = re.sub(r"\D", "", text)
    if text.startswith("+"):
        candidate = "+" + digits
    elif digits.startswith("0044"):
        candidate = "+44" + digits[4:]
    elif digits.startswith("44") and len(digits) == 12:
        candidate = "+" + digits
    elif digits.startswith("07") and len(digits) == 11:
        candidate = "+44" + digits[1:]
    elif digits.startswith("7") and len(digits) == 10:   # Excel dropped the leading 0
        candidate = "+44" + digits
    else:
        return None
    return candidate if _UK_MOBILE.match(candidate) else None


def email(value) -> str | None:
    return normalize_email(str(value)) if value not in (None, "") else None


def person_key(phone: str | None, mail: str | None) -> str | None:
    """Who this is, across several quotes: mobile first, else email."""
    return phone or mail
