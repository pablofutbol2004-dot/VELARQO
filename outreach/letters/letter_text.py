"""The letter. One page, plain British English, one person to another.

Rules it obeys (velarqo-outreach skill, PRODUCT.md): no results claimed, no price,
"You only pay for surveys that get booked", the exact homeowner text, the
"read me five quotes" ask, honest about being new. The mini-estimate is built
only from public facts in the CSV row (Companies House incorporation year and,
when their own website says so, the year they claim to have started).

Merge fields come from one row of data/letters_batch1.csv plus SENDER.
Anything in {{DOUBLE_BRACES}} is a placeholder Pablo fills before printing.
"""
from __future__ import annotations

from datetime import date

# Placeholders: real values are added separately (legal name, photo, UK number).
SENDER = {
    "name": "Pablo {{SURNAME}}",
    "first_name": "Pablo",
    "company": "Velarqo",
    "phone": "{{UK_NUMBER}}",
    "email": "post@velarqo.com",
    "site": "velarqo.com",
    "site_path": "velarqo.com/windows",
    "legal_line": "Velarqo is run by Pablo {{SURNAME}}, {{LEGAL_ADDRESS}}.",
    "photo_path": "",  # set to a JPG/PNG path once the photo exists; blank = placeholder box
}


def uk_date(d: date | None = None) -> str:
    d = d or date.today()
    return f"{d.day} {d.strftime('%B %Y')}"


def years_sentence(row: dict) -> str:
    """Honest mini-estimate from public facts only."""
    firm = row["display_name"]
    inc = int(row["incorporation_year"]) if row.get("incorporation_year") else None
    est = int(row["website_established_year"]) if row.get("website_established_year") else None
    years = int(row["years_trading"]) if row.get("years_trading") else None

    if est and inc and est < inc:
        start = (f"Your website says {firm} has been at it since {est}, and Companies House "
                 f"has the limited company from {inc}.")
    elif inc:
        start = f"Companies House shows {firm} has been going since {inc}."
    else:
        start = f"{firm} has been fitting windows and doors for a good while."

    if years and years >= 15:
        scale = "A firm trading that long has probably sent out a few hundred quotes that went quiet"
    elif years and years >= 8:
        scale = "A firm trading that long has probably sent out well over a hundred quotes that went quiet"
    else:
        scale = "Even in a few years a firm sends out a lot of quotes that go quiet"
    return (f"{start} {scale}: not a no, just nothing. They sit in old files or the job "
            f"system, and nobody has the time to go back through them.")


def homeowner_text(row: dict) -> str:
    return f"“Hi, it’s {row['display_name']}. We quoted for your windows a while back. Did you ever get that sorted?”"


def salutation(row: dict) -> str:
    first = (row.get("salutation_first_name") or "").strip()
    return f"Dear {first}," if first else "Hello,"


def paragraphs(row: dict, sender: dict = SENDER) -> list[str]:
    """Body paragraphs in order. The homeowner text is returned as its own item
    prefixed with '>' so the renderer can indent it."""
    return [
        "I’ve written rather than emailed because I’d rather be the one letter on your desk "
        "than the fortieth email in your inbox.",

        years_sentence(row),

        "That is the only thing I do. I take a firm’s old quotes that never turned into a job, "
        "three months to two years old, and get back in touch with each homeowner by text, in your "
        "name. This is the message they would get, word for word:",

        "> " + homeowner_text(row),

        "Anyone who says they are still interested goes straight into your diary for a survey. "
        "Anyone who says no is left alone for good. You only pay for surveys that get booked, and "
        "the terms are agreed in writing before anything starts.",

        "I should be straight with you: Velarqo is new, and you would be one of the first firms I "
        "work with. I run it myself, so you would deal with me, not an account manager.",

        "Here is a small way to test it. Pick five old quotes, ring me, and read them to me. Ten "
        "minutes. I’ll tell you honestly whether they are worth chasing, and you decide from "
        "there. No spreadsheet, nothing to send over.",

        f"My number is {sender['phone']}. If you would rather write, {sender['email']} comes "
        f"straight to me. The code at the bottom opens a short page on how it works.",
    ]


def footer(row: dict, sender: dict = SENDER) -> str:
    return (f"{sender['legal_line']} If you would rather not hear from me again, say so by email "
            f"or phone and I won’t write again. Ref {row['letter_code']}.")


def as_plain_text(row: dict, sender: dict = SENDER, when: date | None = None) -> str:
    lines = [f"{sender['name']}, {sender['company']}", f"{sender['phone']} · {sender['email']} · {sender['site']}",
             uk_date(when), "",
             row.get("addressee") or "The Owner", row.get("legal_name") or row["display_name"]]
    lines += [row[k] for k in ("address_1", "address_2", "address_3", "address_4", "address_5") if row.get(k)]
    lines += [row.get("postcode", ""), "", salutation(row), ""]
    for p in paragraphs(row, sender):
        lines += [("    " + p[2:]) if p.startswith("> ") else p, ""]
    lines += ["Yours sincerely,", "", sender["name"], sender["company"], "", footer(row, sender)]
    return "\n".join(lines)


def word_count(row: dict, sender: dict = SENDER) -> int:
    body = " ".join(p[2:] if p.startswith("> ") else p for p in paragraphs(row, sender))
    return len(body.split())
