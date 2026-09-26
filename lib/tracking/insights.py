import sqlite3


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def variant_performance(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            message_variant,
            COUNT(*) AS sent,
            SUM(reply) AS replies,
            SUM(appointment_booked) AS appointments,
            SUM(sale_closed) AS sales,
            COALESCE(SUM(revenue), 0) AS revenue
        FROM experiment_result
        GROUP BY message_variant
        ORDER BY revenue DESC
        """
    ).fetchall()

    return [
        {
            "message_variant": row["message_variant"],
            "sent": row["sent"],
            "reply_rate": _rate(row["replies"], row["sent"]),
            "appointment_rate": _rate(row["appointments"], row["sent"]),
            "close_rate": _rate(row["sales"], row["sent"]),
            "revenue": row["revenue"],
            "revenue_per_send": round(row["revenue"] / row["sent"], 2) if row["sent"] else 0.0,
        }
        for row in rows
    ]


def segment_effectiveness(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            segment,
            COUNT(*) AS sent,
            SUM(reply) AS replies,
            SUM(sale_closed) AS sales,
            COALESCE(SUM(revenue), 0) AS revenue
        FROM experiment_result
        WHERE segment IS NOT NULL
        GROUP BY segment
        ORDER BY revenue DESC
        """
    ).fetchall()

    return [
        {
            "segment": row["segment"],
            "sent": row["sent"],
            "reply_rate": _rate(row["replies"], row["sent"]),
            "close_rate": _rate(row["sales"], row["sent"]),
            "revenue_per_100": round((row["revenue"] / row["sent"]) * 100, 2) if row["sent"] else 0.0,
        }
        for row in rows
    ]


def send_time_performance(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            send_day,
            COUNT(*) AS sent,
            SUM(reply) AS replies
        FROM experiment_result
        WHERE send_day IS NOT NULL
        GROUP BY send_day
        ORDER BY replies DESC
        """
    ).fetchall()

    return [
        {
            "send_day": row["send_day"],
            "sent": row["sent"],
            "reply_rate": _rate(row["replies"], row["sent"]),
        }
        for row in rows
    ]


def overall_summary(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS sent,
            SUM(reply) AS replies,
            SUM(appointment_booked) AS appointments,
            SUM(sale_closed) AS sales,
            COALESCE(SUM(revenue), 0) AS revenue
        FROM experiment_result
        """
    ).fetchone()

    sent = row["sent"] or 0
    return {
        "sent": sent,
        "reply_rate": _rate(row["replies"] or 0, sent),
        "appointment_rate": _rate(row["appointments"] or 0, sent),
        "close_rate": _rate(row["sales"] or 0, sent),
        "revenue": row["revenue"],
        "revenue_per_100_leads": round(((row["revenue"] or 0) / sent) * 100, 2) if sent else 0.0,
    }
