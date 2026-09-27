import base64

import pytest
import requests

from integrations.email.base import EmailRateLimitError
from integrations.email.gmail import GmailProvider
from lib.rate_limiter import RateLimiter


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, headers=None, json=None, params=None, timeout=None):
        self.calls.append({"method": method, "url": url, "headers": headers, "json": json})
        return self.responses.pop(0)


def _no_op_rate_limiter():
    return RateLimiter(clock=lambda: 0.0, sleep=lambda _: None)


def test_send_email_builds_correct_mime_message_and_auth():
    session = FakeSession([FakeResponse(200, {"id": "msg-1", "threadId": "thread-1"})])
    provider = GmailProvider(
        access_token="tok", sender_email="me@business.com", session=session, rate_limiter=_no_op_rate_limiter()
    )

    result = provider.send_email(to="lead@acme.com", subject="Quick idea", body="Hi there")

    assert result == {"message_id": "msg-1", "thread_id": "thread-1"}
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/gmail/v1/users/me/messages/send")
    assert call["headers"]["Authorization"] == "Bearer tok"

    raw = base64.urlsafe_b64decode(call["json"]["raw"]).decode()
    assert "To: lead@acme.com" in raw
    assert "From: me@business.com" in raw
    assert "Subject: Quick idea" in raw
    assert "Hi there" in raw


def test_reply_includes_in_reply_to_and_thread_id():
    session = FakeSession([FakeResponse(200, {"id": "msg-2", "threadId": "thread-1"})])
    provider = GmailProvider(
        access_token="tok", sender_email="me@business.com", session=session, rate_limiter=_no_op_rate_limiter()
    )

    provider.send_email(
        to="lead@acme.com", subject="Re: Quick idea", body="Following up",
        thread_id="thread-1", in_reply_to_message_id="<original@mail.gmail.com>",
    )

    call = session.calls[0]
    assert call["json"]["threadId"] == "thread-1"
    raw = base64.urlsafe_b64decode(call["json"]["raw"]).decode()
    assert "In-Reply-To: <original@mail.gmail.com>" in raw


def test_retries_on_429_then_succeeds():
    sleeps = []
    session = FakeSession([
        FakeResponse(429, headers={"Retry-After": "2"}),
        FakeResponse(200, {"id": "msg-3", "threadId": "thread-2"}),
    ])
    provider = GmailProvider(
        access_token="tok", sender_email="me@business.com", session=session,
        rate_limiter=_no_op_rate_limiter(), sleep=sleeps.append,
    )

    result = provider.send_email(to="lead@acme.com", subject="Hi", body="Body")

    assert result["message_id"] == "msg-3"
    assert sleeps == [2.0]


def test_exhausts_retries_raises_rate_limit_error():
    session = FakeSession([FakeResponse(429, headers={}) for _ in range(4)])
    provider = GmailProvider(
        access_token="tok", sender_email="me@business.com", session=session,
        rate_limiter=_no_op_rate_limiter(), max_retries=3, sleep=lambda _: None,
    )

    with pytest.raises(EmailRateLimitError):
        provider.send_email(to="lead@acme.com", subject="Hi", body="Body")
