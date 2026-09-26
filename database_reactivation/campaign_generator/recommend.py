_SEGMENT_STRATEGY = {
    "lost": {
        "price": {"offer": "Updated pricing", "angle": "We've revised our pricing since we last quoted you."},
        "competitor": {"offer": "Feature comparison", "angle": "Here's what's changed since you compared us to alternatives."},
        "default": {"offer": "Free re-quote", "angle": "Worth a fresh look now that things may have changed?"},
    },
    "no_show": {
        "default": {"offer": "Easy reschedule", "angle": "Let's find a better time to reschedule your appointment."},
    },
    "expired": {
        "default": {"offer": "Still interested?", "angle": "Your quote has expired — still interested in moving forward?"},
    },
    "quoted": {
        "default": {"offer": "Decision support", "angle": "Happy to answer any questions before you decide."},
    },
}


def recommend_campaign(record: dict) -> dict:
    segment = record.get("segment", "unknown")
    lost_reason = (record.get("lost_reason") or "default").lower()

    strategies = _SEGMENT_STRATEGY.get(segment, {"default": {"offer": "Check-in", "angle": "Just checking in — anything changed on your end?"}})
    strategy = strategies.get(lost_reason, strategies["default"])
    return strategy


def recommend_campaigns(records: list[dict]) -> list[dict]:
    for record in records:
        if record.get("duplicate_of"):
            continue
        strategy = recommend_campaign(record)
        record["recommended_offer"] = strategy["offer"]
        record["angle"] = strategy["angle"]
    return records
