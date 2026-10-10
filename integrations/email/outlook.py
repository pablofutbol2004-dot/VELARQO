"""Microsoft Graph sender/reader for Velarqo's own cold outreach (Microsoft
365 mailbox). Same role and the same method names as gmail.py, so the send
engine and the CLI treat both providers alike.

Sending: create a draft (POST /me/messages), then POST /me/messages/{id}/send.
/me/sendMail would be one call, but returns nothing - we need the message id,
conversationId and internetMessageId back for threading and reply matching.

Threading: Graph does not let a client set In-Reply-To/References (only
custom x-* headers are allowed), so a follow-up is a draft *reply* to the
message we sent earlier (POST /me/messages/{id}/createReply). Exchange then
writes In-Reply-To, References and the thread index itself, so the follow-up
sits under the first email in the recipient's inbox. The draft reply is
addressed back to us (we sent the original), so it is PATCHed with the real
recipient, our subject and our plain-text body before sending. If the parent
can't be found any more, a plain send goes out instead - delivered, just not
threaded.

Every request sends Prefer: IdType="ImmutableId", so a message keeps its id
when it moves from Drafts to Sent Items; the id the engine stores is the one
createReply needs later.

Auth: expects an already-obtained OAuth2 access token (delegated
Mail.ReadWrite + Mail.Send + User.Read; see microsoft_auth.py). No
credentials exist anywhere in this repo. Built and unit-tested against a fake
HTTP session, never exercised against a real Microsoft 365 account.
"""

import re
import time
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr

import requests

from integrations.email.base import EmailAuthError, EmailRateLimitError, html_to_text
from lib.rate_limiter import RateLimiter

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

# Microsoft Graph throttling limits vary by endpoint/tenant and are not as
# simply published as Gmail's; this is a conservative starting default -
# re-verify against current Graph throttling guidance before raising it.
DEFAULT_MAX_REQUESTS = 4
DEFAULT_WINDOW_SECONDS = 1.0
MAX_RETRY_AFTER_SECONDS = 60.0
PAGE_SIZE = 100

_MESSAGE_FIELDS = "id,conversationId,from,subject,body,receivedDateTime,internetMessageHeaders,internetMessageId,isDraft"


def _retry_after(response, attempt: int) -> float:
    try:
        value = float(response.headers.get("Retry-After", 2**attempt))
    except (TypeError, ValueError):
        value = 2.0**attempt
    return min(max(value, 0.0), MAX_RETRY_AFTER_SECONDS)


class OutlookProvider:
    THREADS_BY_PARENT_ID = True   # the engine passes parent_provider_message_id for follow-ups

    def __init__(
        self,
        access_token: str,
        sender_email: str | None = None,
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
        self._rfc_ids: dict[str, str] = {}   # message id -> internetMessageId seen at creation

    def _headers(self, extra: dict | None = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Prefer": 'IdType="ImmutableId"',
        }
        if extra:
            headers.update(extra)
        return headers

    def _request(self, method: str, path: str, json: dict | None = None, params: dict | None = None,
                 headers: dict | None = None) -> requests.Response:
        url = path if path.startswith("https://") else f"{GRAPH_API_BASE}{path}"
        for attempt in range(self.max_retries + 1):
            self.rate_limiter.acquire()
            response = self.session.request(method, url, headers=self._headers(headers), json=json, params=params,
                                            timeout=30)
            if response.status_code in (429, 503):
                if attempt == self.max_retries:
                    raise EmailRateLimitError(f"Outlook rate limited after {self.max_retries} retries")
                self._sleep(_retry_after(response, attempt))
                continue
            if response.status_code in (401, 403):
                raise EmailAuthError(f"Microsoft Graph refused the token: HTTP {response.status_code}")
            response.raise_for_status()
            return response
        raise EmailRateLimitError(f"Outlook rate limited after {self.max_retries} retries")

    # --- Sending ---------------------------------------------------------

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
        in_reply_to_message_id: str | None = None,
        parent_provider_message_id: str | None = None,
    ) -> dict:
        """Returns {"message_id", "thread_id" (conversationId), "rfc_message_id"}.

        A follow-up passes the parent's Graph id in parent_provider_message_id
        (the engine stores it as provider_message_id); thread_id and
        in_reply_to_message_id are accepted for interface parity and used to
        find the parent when no id is given.
        """
        fields = {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": to}}],
        }
        parent = parent_provider_message_id or self._find_parent(thread_id, in_reply_to_message_id)
        created = None
        if parent:
            try:
                created = self._request("POST", f"/me/messages/{parent}/createReply", json={}).json()
                self._request("PATCH", f"/me/messages/{created['id']}", json=fields)
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                if status != 404:
                    raise
                created = None            # parent gone (deleted from Sent Items): fall through to a plain send
        if created is None:
            created = self._request("POST", "/me/messages", json=fields).json()
        message_id = created["id"]
        self._request("POST", f"/me/messages/{message_id}/send")
        rfc_id = created.get("internetMessageId")
        if rfc_id:
            self._rfc_ids[message_id] = rfc_id
        return {"message_id": message_id, "thread_id": created.get("conversationId"), "rfc_message_id": rfc_id}

    def _find_parent(self, conversation_id: str | None, rfc_message_id: str | None) -> str | None:
        """Latest message we sent in the conversation (or with that
        Message-ID), when the caller doesn't know the parent's Graph id."""
        if rfc_message_id:
            rows = self._list_sent({"$filter": f"internetMessageId eq '{_odata(rfc_message_id)}'", "$select": "id"})
            if rows:
                return rows[0]["id"]
        if conversation_id:
            rows = self._list_sent({"$filter": f"conversationId eq '{_odata(conversation_id)}'",
                                    "$select": "id,sentDateTime"})
            if rows:
                return max(rows, key=lambda r: r.get("sentDateTime") or "")["id"]
        return None

    def _list_sent(self, params: dict) -> list[dict]:
        return self._request("GET", "/me/mailFolders/sentitems/messages", params={"$top": 10, **params}).json().get("value", [])

    def rfc_message_id(self, message_id: str) -> str | None:
        """The RFC 5322 Message-ID of a message we sent (same role as Gmail's)."""
        if message_id in self._rfc_ids:
            return self._rfc_ids[message_id]
        data = self._request("GET", f"/me/messages/{message_id}", params={"$select": "internetMessageId"}).json()
        return data.get("internetMessageId")

    # --- Reading the mailbox (replies, bounces) ---------------------------

    def list_inbox(self, query: str = "newer_than:30d", max_results: int = 200) -> list[str]:
        """Ids of received messages from every folder (inbox, junk, archive,
        deleted) in the last N days. `query` is the engine's Gmail-style
        string; only its newer_than:<N>d part means anything here."""
        match = re.search(r"newer_than:(\d+)d", query or "")
        days = int(match.group(1)) if match else 30
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {"$filter": f"receivedDateTime ge {since} and isDraft eq false", "$select": "id",
                  "$top": min(PAGE_SIZE, max_results)}
        ids, url = [], "/me/messages"
        while url and len(ids) < max_results:
            data = self._request("GET", url, params=params).json()
            ids += [m["id"] for m in data.get("value", [])]
            url, params = data.get("@odata.nextLink"), None     # nextLink carries its own query string
        return ids[:max_results]

    def profile_email(self) -> str:
        """The address this token really belongs to."""
        data = self._request("GET", "/me", params={"$select": "mail,userPrincipalName"}).json()
        return (data.get("mail") or data.get("userPrincipalName") or "").lower()

    def get_message(self, message_id: str) -> dict:
        # Body as stored (text or HTML); HTML is flattened here, the same way
        # as Gmail's, so quoted history in <blockquote> drops out before the
        # reply classifier sees it.
        data = self._request("GET", f"/me/messages/{message_id}", params={"$select": _MESSAGE_FIELDS}).json()
        body = data.get("body") or {}
        text = body.get("content") or ""
        if (body.get("contentType") or "").lower() == "html":
            text = html_to_text(text).strip()
        headers = {h.get("name", "").lower(): h.get("value", "") for h in data.get("internetMessageHeaders") or []}
        return {
            "provider_message_id": data["id"],
            "thread_id": data.get("conversationId"),
            "from_email": _address(data.get("from")),
            "subject": data.get("subject") or "",
            "body": text.replace("\x00", ""),
            "internal_date_ms": _epoch_ms(data.get("receivedDateTime")),
            "auto_submitted": _auto_submitted(headers),
        }


def _auto_submitted(headers: dict) -> bool:
    """Helpdesk acknowledgements and auto-replies flag themselves (RFC 3834)."""
    auto = (headers.get("auto-submitted") or "no").strip().lower()
    precedence = (headers.get("precedence") or "").strip().lower()
    return (auto != "no" or precedence in ("auto_reply", "bulk", "junk")
            or "x-autoreply" in headers or "x-autorespond" in headers)


def _address(recipient: dict | None) -> str:
    address = ((recipient or {}).get("emailAddress") or {}).get("address") or ""
    return parseaddr(address)[1].lower() or address.lower()


def _epoch_ms(value: str | None) -> int:
    if not value:
        return 0
    try:
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return 0


def _odata(value: str) -> str:
    return value.replace("'", "''")
