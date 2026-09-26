import sqlite3
from datetime import datetime, timezone

from data.db import SCHEMA
from lib.tracking.insights import (
    overall_summary,
    segment_effectiveness,
    send_time_performance,
    variant_performance,
)


def _make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _insert(conn, **overrides):
    row = {
        "id": overrides.get("id", "id-" + str(id(overrides))),
        "campaign_id": "camp-1",
        "lead_id": "lead-1",
        "company_name": "Acme",
        "vertical": "windows",
        "segment": "new_prospect",
        "message_variant": 0,
        "send_time": datetime.now(timezone.utc).isoformat(),
        "send_day": "Tuesday",
        "reply": 0,
        "appointment_booked": 0,
        "sale_closed": 0,
        "revenue": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    row.update(overrides)
    conn.execute(
        """
        INSERT INTO experiment_result
        (id, campaign_id, lead_id, company_name, vertical, segment,
         message_variant, send_time, send_day, reply, appointment_booked,
         sale_closed, revenue, created_at)
        VALUES (:id, :campaign_id, :lead_id, :company_name, :vertical, :segment,
                :message_variant, :send_time, :send_day, :reply, :appointment_booked,
                :sale_closed, :revenue, :created_at)
        """,
        row,
    )


def test_variant_performance_computes_rates():
    conn = _make_conn()
    _insert(conn, id="1", message_variant=0, reply=1, sale_closed=1, revenue=1000)
    _insert(conn, id="2", message_variant=0, reply=0)
    _insert(conn, id="3", message_variant=1, reply=1)
    conn.commit()

    results = {row["message_variant"]: row for row in variant_performance(conn)}
    assert results[0]["sent"] == 2
    assert results[0]["reply_rate"] == 0.5
    assert results[0]["close_rate"] == 0.5
    assert results[0]["revenue"] == 1000
    assert results[1]["reply_rate"] == 1.0


def test_segment_effectiveness_ranks_by_revenue():
    conn = _make_conn()
    _insert(conn, id="1", segment="lost", sale_closed=1, revenue=5000)
    _insert(conn, id="2", segment="no_show", sale_closed=1, revenue=1000)
    conn.commit()

    results = segment_effectiveness(conn)
    assert results[0]["segment"] == "lost"
    assert results[0]["revenue_per_100"] == 500000.0


def test_send_time_performance_groups_by_day():
    conn = _make_conn()
    _insert(conn, id="1", send_day="Tuesday", reply=1)
    _insert(conn, id="2", send_day="Tuesday", reply=0)
    _insert(conn, id="3", send_day="Saturday", reply=0)
    conn.commit()

    results = {row["send_day"]: row for row in send_time_performance(conn)}
    assert results["Tuesday"]["sent"] == 2
    assert results["Tuesday"]["reply_rate"] == 0.5
    assert results["Saturday"]["reply_rate"] == 0.0


def test_overall_summary_on_empty_db():
    conn = _make_conn()
    summary = overall_summary(conn)
    assert summary["sent"] == 0
    assert summary["reply_rate"] == 0.0
    assert summary["revenue_per_100_leads"] == 0.0
