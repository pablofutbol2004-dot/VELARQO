"""Pure send-safety rules (no database, no network) so they are easy to test."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")

# UK PECR: B2B email without prior consent is allowed only to corporate
# subscribers. Sole traders and ordinary/limited partnerships count as
# individuals, so anything not on this list is never emailed.
CORPORATE_CATEGORIES = {
    "Private Limited Company",
    "Public Limited Company",
    "Limited Liability Partnership",
    "PRI/LTD BY GUAR/NSC (Private, limited by guarantee, no share capital)",
    "PRIV LTD SECT. 30 (Private limited company, section 30 of the Companies Act)",
}

# Never suppress a whole domain that thousands of unrelated people share.
FREE_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "hotmail.com", "hotmail.co.uk", "outlook.com", "live.com", "live.co.uk",
    "yahoo.com", "yahoo.co.uk", "icloud.com", "me.com", "aol.com", "aol.co.uk", "btinternet.com",
    "btopenworld.com", "sky.com", "virginmedia.com", "ntlworld.com", "talktalk.net", "msn.com",
    "protonmail.com", "proton.me", "mail.com", "gmx.com", "gmx.co.uk", "blueyonder.co.uk", "tiscali.co.uk",
}

SEND_DAYS = range(0, 5)  # Mon-Fri
SEND_START, SEND_END = time(8, 30), time(17, 0)

# Follow-up step -> business days after the previous step was sent.
FOLLOW_UP_GAPS = {2: 3, 3: 5}
LAST_STEP = max(FOLLOW_UP_GAPS)

BOUNCE_STOP_RATE = 0.05
BOUNCE_STOP_MIN_SENT = 20


def is_corporate(company_category: str | None) -> bool:
    return (company_category or "") in CORPORATE_CATEGORIES


def email_domain(email: str | None) -> str:
    return (email or "").rsplit("@", 1)[-1].strip().lower() if "@" in (email or "") else ""


def domain_suppressible(domain: str) -> bool:
    return bool(domain) and domain not in FREE_MAIL_DOMAINS


def in_send_window(now: datetime) -> bool:
    local = now.astimezone(UK)
    return local.weekday() in SEND_DAYS and SEND_START <= local.time() < SEND_END


def uk_day_start(now: datetime) -> datetime:
    local = now.astimezone(UK)
    return datetime.combine(local.date(), time(0), tzinfo=UK)


def business_days_between(start: date, end: date) -> int:
    """Weekdays after `start` up to and including `end`."""
    days, current = 0, start
    while current < end:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days += 1
    return days


def follow_up_due(previous_sent_at: datetime, next_step: int, now: datetime) -> bool:
    gap = FOLLOW_UP_GAPS.get(next_step)
    if gap is None:
        return False
    return business_days_between(previous_sent_at.astimezone(UK).date(), now.astimezone(UK).date()) >= gap


def bounce_stop(sent: int, bounced: int) -> bool:
    return sent >= BOUNCE_STOP_MIN_SENT and bounced / sent > BOUNCE_STOP_RATE
