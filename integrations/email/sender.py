"""Sends a built campaign queue (outreach/campaign_builder/queue.py output)
through whichever EmailProvider the caller passes in. Nothing in the
pipeline knows or cares whether that's Gmail or Outlook.

Every item passes a gate first (default: outreach.compliance's Velarqo
gate, built from truth/). Safe by default: forgetting to pass a gate can't
send an email that fails compliance. Pass gate=None only in tests.
"""

from integrations.email.base import EmailProvider

_DEFAULT = object()


def _default_gate():
    from outreach.compliance import velarqo_send_gate
    return velarqo_send_gate()


def send_campaign_email(provider: EmailProvider, campaign_item: dict, gate=_DEFAULT) -> dict:
    if not campaign_item.get("email"):
        return {**campaign_item, "status": "skipped_no_email"}
    gate = _default_gate() if gate is _DEFAULT else gate
    if gate and (reasons := gate(campaign_item)):
        return {**campaign_item, "status": "blocked", "blocked_reasons": reasons}

    result = provider.send_email(
        to=campaign_item["email"],
        subject=campaign_item["subject"],
        body=campaign_item["body"],
    )
    return {
        **campaign_item,
        "status": "sent",
        "provider_message_id": result["message_id"],
        "provider_thread_id": result.get("thread_id"),
    }


def send_campaign(provider: EmailProvider, campaign: dict, gate=_DEFAULT) -> dict:
    gate = _default_gate() if gate is _DEFAULT else gate
    sent_queue = [send_campaign_email(provider, item, gate) for item in campaign["queue"]]
    return {**campaign, "queue": sent_queue}
