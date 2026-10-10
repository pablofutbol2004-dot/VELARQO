import pytest
import requests

from integrations.ghl.client import GHLClient, GHLRateLimitError
from integrations.ghl.rate_limiter import RateLimiter


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
        self.calls.append({"method": method, "url": url, "headers": headers, "json": json, "params": params})
        return self.responses.pop(0)


def _no_op_rate_limiter():
    return RateLimiter(clock=lambda: 0.0, sleep=lambda _: None)


def test_upsert_contact_sends_correct_auth_headers_and_body():
    session = FakeSession([FakeResponse(200, {"new": True, "contact": {"id": "abc123"}})])
    client = GHLClient(
        api_token="test-token", location_id="loc-1", session=session, rate_limiter=_no_op_rate_limiter()
    )

    result = client.upsert_contact({"email": "a@b.com", "companyName": "Acme"})

    assert result["contact"]["id"] == "abc123"
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/contacts/upsert")
    assert call["headers"]["Authorization"] == "Bearer test-token"
    assert call["headers"]["Version"] == "v3"
    assert call["json"] == {"email": "a@b.com", "companyName": "Acme", "locationId": "loc-1"}


def test_get_pipelines_uses_query_params_not_body():
    session = FakeSession([FakeResponse(200, {"pipelines": []})])
    client = GHLClient(
        api_token="tok", location_id="loc-1", session=session, rate_limiter=_no_op_rate_limiter()
    )

    client.get_pipelines()

    call = session.calls[0]
    assert call["method"] == "GET"
    assert call["json"] is None
    assert call["params"] == {"locationId": "loc-1"}


def test_retries_on_429_then_succeeds():
    sleeps = []
    session = FakeSession([
        FakeResponse(429, headers={"Retry-After": "1.5"}),
        FakeResponse(200, {"new": False, "contact": {"id": "xyz"}}),
    ])
    client = GHLClient(
        api_token="tok", location_id="loc-1", session=session,
        rate_limiter=_no_op_rate_limiter(), sleep=sleeps.append,
    )

    result = client.upsert_contact({"email": "a@b.com"})

    assert result["contact"]["id"] == "xyz"
    assert sleeps == [1.5]
    assert len(session.calls) == 2


def test_exhausts_retries_raises_rate_limit_error():
    session = FakeSession([FakeResponse(429, headers={}) for _ in range(4)])
    client = GHLClient(
        api_token="tok", location_id="loc-1", session=session,
        rate_limiter=_no_op_rate_limiter(), max_retries=3, sleep=lambda _: None,
    )

    with pytest.raises(GHLRateLimitError):
        client.upsert_contact({"email": "a@b.com"})

    assert len(session.calls) == 4


def test_non_429_error_status_raises_http_error():
    session = FakeSession([FakeResponse(422, {})])
    client = GHLClient(
        api_token="token", location_id="loc-1", session=session, rate_limiter=_no_op_rate_limiter()
    )

    with pytest.raises(requests.HTTPError):
        client.upsert_contact({"email": "a@b.com"})


def test_auth_errors_are_their_own_kind_so_runs_stop_instead_of_blaming_rows():
    from integrations.ghl.client import GHLAuthError

    for status in (401, 403):
        client = GHLClient(api_token="bad", location_id="loc-1", session=FakeSession([FakeResponse(status, {})]),
                           rate_limiter=_no_op_rate_limiter())
        with pytest.raises(GHLAuthError):
            client.upsert_contact({"email": "a@b.com"})
