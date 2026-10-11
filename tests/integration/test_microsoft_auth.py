"""Microsoft 365 OAuth helpers: env keys, refresh-token rotation, and the
'token belongs to this mailbox' check. No network, no real secrets."""

import pytest
from dotenv import dotenv_values

from integrations.email import microsoft_auth
from integrations.email.microsoft_auth import (
    SCOPES, access_token_for, refresh_access_token, refresh_env_key, save_tokens,
)


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data, self.status_code = data, status_code

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def post(self, url, data=None, timeout=None):
        self.calls.append((url, data))
        return self.responses.pop(0)


def test_env_key_matches_google_naming_but_is_its_own_namespace():
    assert refresh_env_key("pablo@velarqo-mail.com") == "OUTLOOK_REFRESH_TOKEN_PABLO_VELARQO_MAIL_COM"


def test_refresh_uses_public_client_flow_and_stores_rotated_token(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OUTLOOK_REFRESH_TOKEN_A_B_COM='old-refresh'\n")
    session = FakeSession([FakeResponse({"access_token": "acc-1", "refresh_token": "new-refresh"})])

    token = refresh_access_token("client", "tenant-id", "old-refresh", session, mailbox="a@b.com", env_path=env)

    assert token == "acc-1"
    url, data = session.calls[0]
    assert url == "https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token"
    assert data["grant_type"] == "refresh_token" and "client_secret" not in data
    assert set(data["scope"].split()) == set(SCOPES) >= {"offline_access", "Mail.Send", "Mail.ReadWrite"}
    assert dotenv_values(env)["OUTLOOK_REFRESH_TOKEN_A_B_COM"] == "new-refresh"


def test_refresh_without_rotation_leaves_env_alone(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OUTLOOK_REFRESH_TOKEN_A_B_COM='same'\n")
    session = FakeSession([FakeResponse({"access_token": "acc", "refresh_token": "same"})])
    refresh_access_token("client", "t", "same", session, mailbox="a@b.com", env_path=env)
    assert env.read_text() == "OUTLOOK_REFRESH_TOKEN_A_B_COM='same'\n"


def test_refused_refresh_token_names_the_fix():
    session = FakeSession([FakeResponse({"error": "invalid_grant", "error_description": "AADSTS70008 expired"}, 400)])
    with pytest.raises(RuntimeError, match="authorize-mailbox for a@b.com"):
        refresh_access_token("client", "t", "dead", session, mailbox="a@b.com")


def test_access_token_for_needs_client_and_a_stored_token(monkeypatch, tmp_path):
    monkeypatch.setattr(microsoft_auth, "ENV_PATH", tmp_path / ".env")
    monkeypatch.delenv("MS_CLIENT_ID", raising=False)
    monkeypatch.delenv("MS_TENANT_ID", raising=False)
    with pytest.raises(RuntimeError, match="MS_CLIENT_ID and MS_TENANT_ID"):
        access_token_for("a@b.com")
    monkeypatch.setenv("MS_CLIENT_ID", "cid")
    monkeypatch.setenv("MS_TENANT_ID", "tid")
    monkeypatch.delenv(refresh_env_key("a@b.com"), raising=False)
    with pytest.raises(RuntimeError, match="authorize-mailbox a@b.com"):
        access_token_for("a@b.com")


def test_save_tokens_refuses_a_token_for_another_mailbox(tmp_path):
    env = tmp_path / ".env"
    tokens = {"access_token": "acc", "refresh_token": "r1"}
    with pytest.raises(RuntimeError, match="signed in as other@b.com, not pablo@b.com"):
        save_tokens("pablo@b.com", tokens, env_path=env, lookup=lambda _: "other@b.com")
    assert not env.exists(), "nothing saved on mismatch"

    key = save_tokens("Pablo@b.com", tokens, env_path=env, lookup=lambda _: "pablo@b.com")
    assert key == "OUTLOOK_REFRESH_TOKEN_PABLO_B_COM" and dotenv_values(env)[key] == "r1"

    with pytest.raises(RuntimeError, match="no refresh token"):
        save_tokens("pablo@b.com", {"access_token": "acc"}, env_path=env, lookup=lambda _: "pablo@b.com")
