from datetime import datetime, timezone

_LOST_REASON_RECOVERABILITY = {
    "price": 70,
    "timing": 85,
    "not_ready": 80,
    "no_show": 75,
    "competitor": 40,
    "unknown": 50,
}


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


def _recency_score(days_since_contact: float | None) -> float:
    if days_since_contact is None:
        return 50.0
    if days_since_contact < 14:
        return 30.0
    if days_since_contact <= 180:
        return 100.0
    if days_since_contact <= 365:
        return 60.0
    return 30.0


def score_recovery(record: dict, now: datetime | None = None) -> float:
    """0-100 likelihood this record converts if reactivated."""
    now = now or datetime.now(timezone.utc)

    recency = _recency_score(_days_since(record.get("last_contact"), now))
    reason_score = _LOST_REASON_RECOVERABILITY.get(
        (record.get("lost_reason") or "unknown").lower(), 50
    )

    segment = record.get("segment", "unknown")
    segment_bonus = {"no_show": 10, "expired": 5, "lost": 0, "quoted": -10, "won": -50}.get(segment, 0)

    score = 0.5 * recency + 0.5 * reason_score + segment_bonus
    return round(max(0.0, min(100.0, score)), 2)


def score_economic_priority(record: dict) -> float:
    """Rank score: recovery likelihood x deal value. Not bounded 0-100."""
    quote_value = record.get("quote_value") or 0
    recovery_score = record.get("recovery_score") or 0
    return round((recovery_score / 100) * quote_value, 2)


def score_records(records: list[dict], now: datetime | None = None) -> list[dict]:
    for record in records:
        if record.get("duplicate_of"):
            continue
        record["recovery_score"] = score_recovery(record, now)
        record["economic_priority"] = score_economic_priority(record)
    return records
