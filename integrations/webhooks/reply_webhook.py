"""Handles an inbound reply event (from an email provider's webhook).

This is the processing logic only — wiring an actual HTTP endpoint
(Flask/FastAPI) is left for when a real email provider is configured.
"""

from outreach.reply_classifier.classify import classify_reply
from lib.tracking.experiments import record_reply


def handle_reply(experiment_id: str, reply_text: str) -> str:
    sentiment = classify_reply(reply_text)
    record_reply(experiment_id, sentiment)
    return sentiment
