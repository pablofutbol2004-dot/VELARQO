"""Shared interface both Gmail and Outlook implementations satisfy, so
outreach/campaign_builder and the pipeline don't care which mailbox
provider a given client account actually sends through.
"""

import re
from typing import Protocol

# Mailbox config field (config/mailboxes.json "provider") -> implementation.
PROVIDERS = ("gmail", "outlook")


class EmailRateLimitError(Exception):
    pass


class EmailAuthError(Exception):
    """401/403 from the provider: the token expired, was revoked or belongs
    to the wrong account. Nothing is wrong with the email itself, so the
    caller puts it back in the queue and stops that mailbox."""


class EmailProvider(Protocol):
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
        in_reply_to_message_id: str | None = None,
    ) -> dict:
        """Send an email. Returns {"message_id": str, "thread_id": str | None}
        and, when the provider knows it at send time, "rfc_message_id".

        thread_id / in_reply_to_message_id let a follow-up land in the same
        conversation as the original send. A provider that threads by
        replying to the parent message (Outlook) sets THREADS_BY_PARENT_ID
        and also accepts parent_provider_message_id.
        """
        ...


def html_to_text(html: str) -> str:
    """Tag-stripped text of an HTML body, quoted history and styles removed."""
    html = re.sub(r"(?is)<(blockquote|style|script).*?</\1>", "", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", html)
    return re.sub(r"<[^>]+>", "", html)
