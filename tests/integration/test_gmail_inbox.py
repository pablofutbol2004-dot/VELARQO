import base64

from integrations.email.gmail import GmailProvider
from integrations.email.google_auth import refresh_access_token, refresh_env_key


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data, self.status_code, self.headers = data, status_code, {}

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)

    def post(self, url, data=None, timeout=None):
        self.calls.append(("POST", url, data))
        return self.responses.pop(0)


class NoWait:
    def acquire(self):
        pass


def _b64(text):
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def test_get_message_extracts_sender_subject_and_plain_text():
    session = FakeSession([FakeResponse({
        "id": "m1", "threadId": "t1", "internalDate": "1791000000000",
        "payload": {
            "headers": [{"name": "From", "value": "Dave Smith <Dave@Acme.co.uk>"}, {"name": "Subject", "value": "Re: old quotes"}],
            "mimeType": "multipart/alternative",
            "parts": [
                {"mimeType": "text/html", "body": {"data": _b64("<p>Yes <b>call me</b></p>")}},
                {"mimeType": "text/plain", "body": {"data": _b64("Yes call me")}},
            ],
        },
    })])
    gmail = GmailProvider("tok", "pablo@x.com", session=session, rate_limiter=NoWait())

    msg = gmail.get_message("m1")

    assert msg == {"provider_message_id": "m1", "thread_id": "t1", "from_email": "dave@acme.co.uk",
                   "subject": "Re: old quotes", "body": "Yes call me", "internal_date_ms": 1791000000000,
                   "auto_submitted": False}


def test_list_inbox_pages_through_results():
    session = FakeSession([
        FakeResponse({"messages": [{"id": "a"}, {"id": "b"}], "nextPageToken": "p2"}),
        FakeResponse({"messages": [{"id": "c"}]}),
    ])
    gmail = GmailProvider("tok", "pablo@x.com", session=session, rate_limiter=NoWait())

    assert gmail.list_inbox("in:inbox") == ["a", "b", "c"]
    assert session.calls[1][2]["params"]["pageToken"] == "p2"


def test_rfc_message_id_reads_header():
    session = FakeSession([FakeResponse({"payload": {"headers": [{"name": "Message-Id", "value": "<abc@mail.gmail.com>"}]}})])
    gmail = GmailProvider("tok", "pablo@x.com", session=session, rate_limiter=NoWait())
    assert gmail.rfc_message_id("m1") == "<abc@mail.gmail.com>"


def test_refresh_access_token_and_env_key():
    session = FakeSession([FakeResponse({"access_token": "new-token"})])
    assert refresh_access_token("id", "secret", "refresh", session) == "new-token"
    assert session.calls[0][2]["grant_type"] == "refresh_token"
    assert refresh_env_key("pablo@get-velarqo.com") == "GMAIL_REFRESH_TOKEN_PABLO_GET_VELARQO_COM"
