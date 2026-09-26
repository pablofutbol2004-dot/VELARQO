import uuid
from datetime import datetime, time, timedelta, timezone

_DAY_NAME_TO_WEEKDAY = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2,
    "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6,
}


def _next_send_datetime(icp: dict, after: datetime) -> datetime:
    target_weekday = _DAY_NAME_TO_WEEKDAY.get(icp.get("optimal_send_day", "Tuesday"), 1)
    send_time = icp.get("optimal_send_time", "09:00")
    hour, minute = (int(part) for part in send_time.split(":"))

    days_ahead = (target_weekday - after.weekday()) % 7
    candidate = after + timedelta(days=days_ahead)
    return candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)


def build_campaign_queue(emails: list[dict], icp: dict, campaign_id: str | None = None) -> dict:
    campaign_id = campaign_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    send_time = _next_send_datetime(icp, now)

    queue = []
    for email in emails:
        queue.append({
            **email,
            "campaign_id": campaign_id,
            "send_time": send_time.isoformat(),
            "status": "queued",
        })

    return {
        "campaign_id": campaign_id,
        "vertical": icp.get("vertical"),
        "created_at": now.isoformat(),
        "queue": queue,
    }
