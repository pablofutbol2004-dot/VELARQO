from datetime import datetime, timezone

DEFAULT_SUPPRESS_RECENT_CONTACT_DAYS = 30


def _days_since(timestamp: str | None, now: datetime) -> float | None:
    if not timestamp:
        return None
    try:
        contacted = datetime.fromisoformat(timestamp)
    except ValueError:
        return None
    if contacted.tzinfo is None:
        contacted = contacted.replace(tzinfo=timezone.utc)
    return (now - contacted).total_seconds() / 86400


def apply_suppression(
    records: list[dict],
    suppress_recent_contact_days: int = DEFAULT_SUPPRESS_RECENT_CONTACT_DAYS,
    now: datetime | None = None,
) -> list[dict]:
    now = now or datetime.now(timezone.utc)

    for record in records:
        if record.get("duplicate_of"):
            record["suppressed"] = True
            record["suppression_reason"] = "duplicate"
            continue

        if not record.get("email"):
            record["suppressed"] = True
            record["suppression_reason"] = "invalid_email"
            continue

        if (record.get("notes") or "").lower().find("unsubscribe") != -1:
            record["suppressed"] = True
            record["suppression_reason"] = "unsubscribed"
            continue

        days_since = _days_since(record.get("last_contact"), now)
        if days_since is not None and days_since < suppress_recent_contact_days:
            record["suppressed"] = True
            record["suppression_reason"] = "recently_contacted"
            continue

        record["suppressed"] = False
        record["suppression_reason"] = None

    return records
