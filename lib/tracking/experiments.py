import uuid
from datetime import datetime, timezone

from data.db import get_connection, init_db

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def record_send(campaign_item: dict, vertical: str, segment: str = "new_prospect") -> str:
    init_db()
    experiment_id = str(uuid.uuid4())
    send_time = datetime.fromisoformat(campaign_item["send_time"])

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO experiment_result
            (id, campaign_id, lead_id, company_name, vertical, segment,
             message_variant, send_time, send_day, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                experiment_id,
                campaign_item["campaign_id"],
                campaign_item["lead_id"],
                campaign_item["company_name"],
                vertical,
                segment,
                campaign_item["variant_index"],
                campaign_item["send_time"],
                _DAY_NAMES[send_time.weekday()],
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return experiment_id


def record_reply(experiment_id: str, sentiment: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE experiment_result SET reply = 1, reply_sentiment = ? WHERE id = ?",
            (sentiment, experiment_id),
        )
        conn.commit()
    finally:
        conn.close()


def record_appointment(experiment_id: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE experiment_result SET appointment_booked = 1, appointment_date = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), experiment_id),
        )
        conn.commit()
    finally:
        conn.close()


def record_sale(experiment_id: str, revenue: float) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE experiment_result SET sale_closed = 1, revenue = ?, revenue_date = ? WHERE id = ?",
            (revenue, datetime.now(timezone.utc).isoformat(), experiment_id),
        )
        conn.commit()
    finally:
        conn.close()
