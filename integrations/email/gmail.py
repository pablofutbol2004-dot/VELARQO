"""Gmail API sender for Velarqo's own cold outreach (Google Workspace
mailbox) - not GHL, which is reserved for client fulfillment. See
README.md's "Architecture" section for the split.

Auth: expects an already-obtained OAuth2 access token (scope
gmail.send at minimum). Getting that token (OAuth consent flow, or a
service account with domain-wide delegation for a Workspace account) is
not built here - this client only does the send call, given a valid
token.

No credentials exist anywhere in this repo. Built and unit-tested against
a fake HTTP session, never exercised against a real Gmail account.
"""

import base64
import time
from email.message import EmailMessage as MimeEmailMessage

import requests

from integrations.email.base import EmailRateLimitError
from lib.rate_limiter import RateLimiter

GMAIL_API_BASE = "https://gmail.googleapis.com"

# Gmail API: messages.send costs 100 quota units against a 250 units/user/
# second budget - roughly 2/sec sustained. Conservative default; re-verify
# against the current Gmail API quota docs before raising it.
DEFAULT_MAX_REQUESTS = 2
DEFAULT_WINDOW_SECONDS = 1.0


class GmailProvider:
    def __init__(
        self,
        access_token: str,
        sender_email: str,
        session: requests.Session | None = None,
        rate_limiter: RateLimiter | None = None,
        max_retries: int = 3,
        sleep=time.sleep,
    ):
        self.access_token = access_token
        self.sender_email = sender_email
        self.session = session or requests.Session()
        self.rate_limiter = rate_limiter or RateLimiter(DEFAULT_MAX_REQUESTS, DEFAULT_WINDOW_SECONDS)
        self.max_retries = max_retries
        self._sleep = sleep

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

    def _build_raw_message(self, to: str, subject: str, body: str, in_reply_to_message_id: str | None) -> str:
        message = MimeEmailMessage()
        message["To"] = to
        message["From"] = self.sender_email
        message["Subject"] = subject
        if in_reply_to_message_id:
            message["In-Reply-To"] = in_reply_to_message_id
            message["References"] = in_reply_to_message_id
        message.set_content(body)
        return base64.urlsafe_b64encode(message.as_bytes()).decode()

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
        in_reply_to_message_id: str | None = None,
    ) -> dict:
        payload = {"raw": self._build_raw_message(to, subject, body, in_reply_to_message_id)}
        if thread_id:
            payload["threadId"] = thread_id

        url = f"{GMAIL_API_BASE}/gmail/v1/users/me/messages/send"

        for attempt in range(self.max_retries + 1):
            self.rate_limiter.acquire()
            response = self.session.request("POST", url, headers=self._headers(), json=payload, timeout=30)

            if response.status_code == 429:
                if attempt == self.max_retries:
                    raise EmailRateLimitError(f"Gmail rate limited after {self.max_retries} retries")
                retry_after = float(response.headers.get("Retry-After", 2**attempt))
                self._sleep(retry_after)
                continue

            response.raise_for_status()
            data = response.json()
            return {"message_id": data.get("id"), "thread_id": data.get("threadId")}

        raise EmailRateLimitError(f"Gmail rate limited after {self.max_retries} retries")
