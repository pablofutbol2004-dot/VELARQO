from integrations.email.sender import send_campaign_email
from outreach.compliance import footer, lead_problems, setup_problems, velarqo_send_gate

COMPANY = {
    "trading_name": "Velarqo", "legal_name": "Velarqo Ltd", "registered_address": "1 Street, Town",
    "privacy_notice_url": "https://velarqo.com/privacy",
    "sender": {"name": "Pablo", "email": "pablo@velarqo.com", "opt_out_instruction": 'Reply "stop" and I won\'t contact you again.'},
}
READY = {"compliance": {"cold_email_status": "allowed"}, "company": COMPANY}
ITEM = {"email": "mike@acme.co.uk", "company_category": "Private Limited Company", "body": "Hi\n\n" + footer(COMPANY)}


def test_footer_identifies_sender_and_offers_opt_out():
    text = footer(COMPANY)
    assert "Velarqo Ltd, 1 Street, Town" in text
    assert "stop" in text


def test_ready_setup_and_compliant_lead_pass():
    assert setup_problems(READY) == []
    assert lead_problems(ITEM) == []


def test_todo_identity_and_blocked_status_stop_everything():
    problems = setup_problems({
        "compliance": {"cold_email_status": "blocked_pending_legal_advice"},
        "company": {**COMPANY, "legal_name": "TODO", "sender": {**COMPANY["sender"], "email": "TODO"}},
    })
    assert len(problems) == 3


def test_lead_level_blocks():
    assert "suppressed" in lead_problems(ITEM, suppressed={"acme.co.uk"})[0]
    assert "PECR" in lead_problems({**ITEM, "company_category": "Limited Partnership"})[0]
    assert "PECR" in lead_problems({**ITEM, "company_category": None})[0]
    assert lead_problems({**ITEM, "body": "Hi"}) == ["body has no opt-out line"]


def test_sender_blocks_by_default_while_truth_has_todos():
    # truth/velarqo/company.yaml still has TODOs, so the default gate must block.
    class Provider:
        sent = []
        def send_email(self, **kwargs):
            self.sent.append(kwargs)
            return {"message_id": "m1"}

    provider = Provider()
    result = send_campaign_email(provider, dict(ITEM, subject="s"))
    assert result["status"] == "blocked"
    assert provider.sent == []
    assert velarqo_send_gate()(ITEM)  # non-empty reasons
