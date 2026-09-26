from pathlib import Path

from data.db import get_connection
from integrations.webhooks.reply_webhook import handle_reply
from lib.tracking.experiments import record_appointment, record_sale, record_send
from outreach.reply_classifier.classify import classify_reply
from pipelines.cold_outreach.pipeline import build_campaign, load_icp, run_pipeline

FIXTURE = Path(__file__).parents[1] / "fixtures" / "synthetic_leads.csv"
ICP_PATH = Path(__file__).parents[2] / "config" / "templates" / "icp-template.json"


def test_classify_reply_sentiments():
    assert classify_reply("Sounds good, let's book a call") == "positive"
    assert classify_reply("Not interested, please unsubscribe") == "negative"
    assert classify_reply("Maybe next quarter, circle back then") == "maybe"


def test_full_send_to_sale_tracking_cycle(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("data.db.DB_PATH", db_path)

    icp = load_icp(ICP_PATH)
    leads = run_pipeline(FIXTURE)
    campaign = build_campaign(leads, icp)
    item = campaign["queue"][0]

    experiment_id = record_send(item, vertical=icp.get("vertical"))
    sentiment = handle_reply(experiment_id, "This sounds good, let's book a call")
    assert sentiment == "positive"

    record_appointment(experiment_id)
    record_sale(experiment_id, revenue=4500.0)

    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM experiment_result WHERE id = ?", (experiment_id,)).fetchone()
    conn.close()

    assert row["reply"] == 1
    assert row["reply_sentiment"] == "positive"
    assert row["appointment_booked"] == 1
    assert row["sale_closed"] == 1
    assert row["revenue"] == 4500.0
