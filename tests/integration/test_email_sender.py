from pathlib import Path

from integrations.email.sender import send_campaign, send_campaign_email
from pipelines.cold_outreach.pipeline import build_campaign, load_icp, run_pipeline

FIXTURE = Path(__file__).parents[1] / "fixtures" / "synthetic_leads.csv"
ICP_PATH = Path(__file__).parents[2] / "config" / "templates" / "icp-template.json"


class FakeProvider:
    def __init__(self):
        self.sent = []

    def send_email(self, to, subject, body, thread_id=None, in_reply_to_message_id=None):
        self.sent.append({"to": to, "subject": subject, "body": body})
        return {"message_id": f"msg-{len(self.sent)}", "thread_id": f"thread-{len(self.sent)}"}


def test_send_campaign_email_skips_when_no_email():
    provider = FakeProvider()
    result = send_campaign_email(provider, {"email": None, "subject": "x", "body": "y"}, gate=None)

    assert result["status"] == "skipped_no_email"
    assert provider.sent == []


def test_send_campaign_email_sends_and_annotates_result():
    provider = FakeProvider()
    item = {"email": "lead@acme.com", "subject": "Quick idea", "body": "Hi there"}

    result = send_campaign_email(provider, item, gate=None)

    assert result["status"] == "sent"
    assert result["provider_message_id"] == "msg-1"
    assert result["provider_thread_id"] == "thread-1"
    assert provider.sent[0]["to"] == "lead@acme.com"


def test_send_campaign_sends_full_queue_from_real_pipeline_output():
    icp = load_icp(ICP_PATH)
    leads = run_pipeline(FIXTURE)
    campaign = build_campaign(leads, icp)

    provider = FakeProvider()
    sent_campaign = send_campaign(provider, campaign, gate=None)

    assert len(provider.sent) == len(campaign["queue"])
    for item in sent_campaign["queue"]:
        assert item["status"] == "sent"
        assert item["provider_message_id"]
