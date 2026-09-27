"""Microsoft Graph API sender for Velarqo's own cold outreach (Outlook/
Microsoft 365 mailbox). Same role as gmail.py, different provider.

Uses the create-then-send pattern (POST /me/messages, then
POST /me/messages/{id}/send) instead of the simpler /me/sendMail, because
/sendMail returns no body - we need the created message's id and
conversationId back to support future follow-up threading.

Known gap: Graph's natural way to keep a follow-up in the same visible
thread is POST /me/messages/{id}/reply, not re-sending a new message with
matching headers (that's the Gmail pattern). This client's send_email()
does not implement true threaded replies yet - thread_id returned is
conversationId for tracking/analytics, not a guarantee that a second
send_email() call lands in the same Outlook conversation. Revisit when
outreach/sequences is built.

Auth: expects an already-obtained OAuth2 access token (Mail.Send scope at
minimum). No credentials exist anywhere in this repo. Built and
unit-tested against a fake HTTP session, never exercised against a real
Microsoft 365 account.
"""

import time

import requests

from integrations.email.base import EmailRateLimitError
from lib.rate_limiter import RateLimiter

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

# Microsoft Graph throttling limits vary by endpoint/tenant and are not as
# simply published as Gmail's; this is a conservative starting default -
# re-verify against current Graph throttling guidance before raising it.
DEFAULT_MAX_REQUESTS = 4
DEFAULT_WINDOW_SECONDS = 1.0


class OutlookProvider:
    def __init__(
        self,
        access_token: str,
        session: requests.Session | None = None,
        rate_limiter: RateLimiter | None = None,
        max_retries: int = 3,
        sleep=time.sleep,
    ):
        self.access_token = access_token
        self.session = session or requests.Session()
        self.rate_limiter = rate_limiter or RateLimiter(DEFAULT_MAX_REQUESTS, DEFAULT_WINDOW_SECONDS)
        self.max_retries = max_retries
        self._sleep = sleep

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

    def _request(self, method: str, path: str, json: dict | None = None) -> requests.Response:
        url = f"{GRAPH_API_BASE}{path}"

        for attempt in range(self.max_retries + 1):
            self.rate_limiter.acquire()
            response = self.session.request(method, url, headers=self._headers(), json=json, timeout=30)

            if response.status_code == 429:
                if attempt == self.max_retries:
                    raise EmailRateLimitError(f"Outlook rate limited after {self.max_retries} retries")
                retry_after = float(response.headers.get("Retry-After", 2**attempt))
                self._sleep(retry_after)
                continue

            response.raise_for_status()
            return response

        raise EmailRateLimitError(f"Outlook rate limited after {self.max_retries} retries")

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
        in_reply_to_message_id: str | None = None,
    ) -> dict:
        message = {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": to}}],
        }

        created = self._request("POST", "/me/messages", json=message).json()
        message_id = created["id"]
        self._request("POST", f"/me/messages/{message_id}/send")

        return {"message_id": message_id, "thread_id": created.get("conversationId")}
