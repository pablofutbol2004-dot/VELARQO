"""Pure send-safety rules (no database, no network) so they are easy to test."""

import os
from dataclasses import dataclass
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

# Website-builder / directory / placeholder domains: an address here is
# scraped junk, not the company's mailbox (e.g. blog@wordpress.com).
PLATFORM_DOMAINS = {
    "wordpress.com", "wix.com", "wixsite.com", "squarespace.com", "godaddy.com", "weebly.com", "example.com",
    "example.co.uk", "domain.com", "yourdomain.com", "sentry.io", "yell.com", "checkatrade.com", "mybuilder.com",
    "ratedpeople.com", "trustatrader.com", "bark.com", "facebook.com", "google.com",
}
# Business ISP mail: one firm saying no must not suppress every firm on it.
SHARED_ISP_DOMAINS = {
    "btconnect.com", "talk21.com", "virgin.net", "plus.net", "plusnet.com", "orange.net", "freeserve.co.uk",
    "tesco.net", "o2.co.uk", "zen.co.uk", "onetel.com", "fsmail.net", "supanet.com", "uwclub.net", "lineone.net",
}

# Send windows, per environment (.env or the shell), UK time:
#   VELARQO_SEND_WINDOW="Mon-Fri 08:30-17:00"       nothing goes out outside it
#   VELARQO_PREFERRED_WINDOW="Tue-Thu 08:30-12:00"  first emails wait for it ("off" disables)
# Follow-ups ignore the preferred window: they keep their business-day gaps.
DEFAULT_SEND_WINDOW = "Mon-Fri 08:30-17:00"
DEFAULT_PREFERRED_WINDOW = "Tue-Thu 08:30-12:00"
_DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


@dataclass(frozen=True)
class Window:
    days: frozenset
    start: time
    end: time

    def contains(self, now: datetime) -> bool:
        local = now.astimezone(UK)
        return local.weekday() in self.days and self.start <= local.time() < self.end


def parse_window(text: str) -> "Window | None":
    """'Tue-Thu 08:30-12:00' or 'Mon,Wed 09:00-11:00'; 'off' or '' -> None."""
    text = (text or "").strip()
    if text.lower() in ("", "off", "none"):
        return None
    try:
        day_part, hour_part = text.split()
        days = set()
        for chunk in day_part.lower().split(","):
            first, _, last = chunk.partition("-")
            a, b = _DAYS.index(first[:3]), _DAYS.index((last or first)[:3])
            days.update(range(a, b + 1))
        start, end = (time.fromisoformat(t) for t in hour_part.split("-"))
    except ValueError as exc:
        raise ValueError(f"send window {text!r} must look like 'Mon-Fri 08:30-17:00'") from exc
    if not days or start >= end:
        raise ValueError(f"send window {text!r} is empty")
    return Window(frozenset(days), start, end)


def send_window() -> Window:
    return parse_window(os.environ.get("VELARQO_SEND_WINDOW") or DEFAULT_SEND_WINDOW)


def preferred_window() -> "Window | None":
    return parse_window(os.environ.get("VELARQO_PREFERRED_WINDOW", DEFAULT_PREFERRED_WINDOW))


# Follow-up step -> business days after the previous step was sent.
FOLLOW_UP_GAPS = {2: 3, 3: 5}
LAST_STEP = max(FOLLOW_UP_GAPS)
DEFAULT_STEPS = 3  # an experiment can send fewer ("steps": 2 = email 1 + follow-up 2)

BOUNCE_STOP_RATE = 0.05
BOUNCE_STOP_MIN_SENT = 20


def is_corporate(company_category: str | None) -> bool:
    return (company_category or "") in CORPORATE_CATEGORIES


def is_company_mailbox(email: str | None) -> bool:
    """A Gmail/Hotmail-style account is subscribed by a person, not the
    company, so under PECR it counts as an individual subscriber even when a
    Ltd uses it. Only company-domain mailboxes are emailed."""
    domain = email_domain(email)
    return bool(domain) and domain not in FREE_MAIL_DOMAINS and domain not in PLATFORM_DOMAINS


def email_domain(email: str | None) -> str:
    return (email or "").rsplit("@", 1)[-1].strip().lower() if "@" in (email or "") else ""


def domain_suppressible(domain: str) -> bool:
    return bool(domain) and domain not in FREE_MAIL_DOMAINS | SHARED_ISP_DOMAINS | PLATFORM_DOMAINS


def in_send_window(now: datetime, window: Window | None = None) -> bool:
    return (window or send_window()).contains(now)


def preferred_capacity(now: datetime, daily_cap: int, preferred: Window, horizon_days: int = 7) -> int:
    """First emails one mailbox can still send in preferred windows over the
    next week (today counts only if its preferred window hasn't started)."""
    local = now.astimezone(UK)
    days = 0
    for offset in range(horizon_days):
        day = local.date() + timedelta(days=offset)
        if day.weekday() in preferred.days and (offset > 0 or local.time() < preferred.start):
            days += 1
    return days * daily_cap


def hold_first_emails(now: datetime, backlog_per_mailbox: int, daily_cap: int, preferred: Window | None) -> bool:
    """Outside the preferred window, first emails wait for it, unless the
    queue is bigger than the next week's preferred windows can send: then the
    surplus goes out in the normal window, so reach never slows down."""
    if preferred is None or preferred.contains(now):
        return False
    return backlog_per_mailbox <= preferred_capacity(now, daily_cap, preferred)


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


def follow_up_due(previous_sent_at: datetime, next_step: int, now: datetime, steps: int = DEFAULT_STEPS) -> bool:
    gap = FOLLOW_UP_GAPS.get(next_step)
    if gap is None or next_step > steps:
        return False
    return business_days_between(previous_sent_at.astimezone(UK).date(), now.astimezone(UK).date()) >= gap


def bounce_stop(sent: int, bounced: int) -> bool:
    return sent >= BOUNCE_STOP_MIN_SENT and bounced / sent > BOUNCE_STOP_RATE
