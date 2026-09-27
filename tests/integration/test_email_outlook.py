import pytest
import requests

from integrations.email.base import EmailRateLimitError
from integrations.email.outlook import OutlookProvider
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


def test_send_email_creates_then_sends_message():
    session = FakeSession([
        FakeResponse(201, {"id": "msg-1", "conversationId": "conv-1"}),
        FakeResponse(202, {}),
    ])
    provider = OutlookProvider(access_token="tok", session=session, rate_limiter=_no_op_rate_limiter())

    result = provider.send_email(to="lead@acme.com", subject="Quick idea", body="Hi there")

    assert result == {"message_id": "msg-1", "thread_id": "conv-1"}
    assert len(session.calls) == 2

    create_call = session.calls[0]
    assert create_call["method"] == "POST"
    assert create_call["url"].endswith("/me/messages")
    assert create_call["headers"]["Authorization"] == "Bearer tok"
    assert create_call["json"]["toRecipients"] == [{"emailAddress": {"address": "lead@acme.com"}}]
    assert create_call["json"]["body"]["content"] == "Hi there"

    send_call = session.calls[1]
    assert send_call["method"] == "POST"
    assert send_call["url"].endswith("/me/messages/msg-1/send")


def test_retries_on_429_during_create_step():
    sleeps = []
    session = FakeSession([
        FakeResponse(429, headers={"Retry-After": "1"}),
        FakeResponse(201, {"id": "msg-2", "conversationId": "conv-2"}),
        FakeResponse(202, {}),
    ])
    provider = OutlookProvider(
        access_token="tok", session=session, rate_limiter=_no_op_rate_limiter(), sleep=sleeps.append
    )

    result = provider.send_email(to="lead@acme.com", subject="Hi", body="Body")

    assert result["message_id"] == "msg-2"
    assert sleeps == [1.0]


def test_exhausts_retries_raises_rate_limit_error():
    session = FakeSession([FakeResponse(429, headers={}) for _ in range(4)])
    provider = OutlookProvider(
        access_token="tok", session=session, rate_limiter=_no_op_rate_limiter(), max_retries=3, sleep=lambda _: None
    )

    with pytest.raises(EmailRateLimitError):
        provider.send_email(to="lead@acme.com", subject="Hi", body="Body")
