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
    text = re.sub(r"\(\s*0\s*\)", "", text)       # "+44 (0)7700 900123": the (0) isn't dialled after +44
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
    """A row's own identifier before grouping: mobile first, else email.
    Import then merges rows sharing ANY phone or email (group_people)."""
    return phone or mail


def group_people(rows: list[tuple[str, str | None, str | None]]) -> dict[str, str | None]:
    """rows: (homeowner_key, phone, email). Rows that share any phone OR email,
    directly or through a chain (A has P+E, B has E, C has P), are one person.
    Returns homeowner_key -> person key (the smallest identifier in the group,
    so it is stable for the same data), or None for rows with no identifier."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for _, phone, mail in rows:
        ids = [i for i in (phone, mail) if i]
        for i in ids:
            find(i)
        if len(ids) == 2:
            union(ids[0], ids[1])
    out: dict[str, str | None] = {}
    for key, phone, mail in rows:
        first = phone or mail
        out[key] = find(first) if first else None
    return out
