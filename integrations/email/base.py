"""Shared interface both Gmail and Outlook implementations satisfy, so
outreach/campaign_builder and the pipeline don't care which mailbox
provider a given client account actually sends through.
"""

from typing import Protocol


class EmailRateLimitError(Exception):
    pass


class EmailProvider(Protocol):
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
        in_reply_to_message_id: str | None = None,
    ) -> dict:
        """Send an email. Returns {"message_id": str, "thread_id": str | None}.

        thread_id / in_reply_to_message_id let a follow-up land in the same
        conversation as the original send, once outreach/sequences exists
        to drive follow-ups.
        """
        ...
