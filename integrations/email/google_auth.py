"""OAuth for Velarqo's own Google Workspace sending mailboxes.

One-time per mailbox: `python -m pipelines.outbound authorize-mailbox you@domain`
opens Google's consent page, catches the redirect on localhost, and writes
the long-lived refresh token into .env (gitignored) - it is never printed.
After that, access_token_for() swaps the refresh token for a 1-hour access
token on every run.

Setup (Google Cloud console, once): create an OAuth client of type
"Desktop app", set the consent screen user type to *Internal* (Workspace
only - External/Testing tokens expire after 7 days), enable the Gmail API,
and put GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET in .env.
"""

import base64
import hashlib
import http.server
import os
import re
import secrets
import urllib.parse
import webbrowser
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
# gmail.modify covers sending and reading the inbox for replies/bounces.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
ENV_PATH = Path(__file__).parents[2] / ".env"


def refresh_env_key(mailbox: str) -> str:
    return "GMAIL_REFRESH_TOKEN_" + re.sub(r"[^A-Za-z0-9]", "_", mailbox).upper()


def _client() -> tuple[str, str]:
    load_dotenv(ENV_PATH)
    client_id, client_secret = os.environ.get("GOOGLE_CLIENT_ID"), os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env")
    return client_id, client_secret


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str,
                         session: requests.Session | None = None) -> str:
    response = (session or requests.Session()).post(TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, timeout=30)
    response.raise_for_status()
    return response.json()["access_token"]


def access_token_for(mailbox: str, session: requests.Session | None = None) -> str:
    client_id, client_secret = _client()
    refresh_token = os.environ.get(refresh_env_key(mailbox))
    if not refresh_token:
        raise RuntimeError(f"No refresh token for {mailbox}: run `python -m pipelines.outbound authorize-mailbox {mailbox}`")
    return refresh_access_token(client_id, client_secret, refresh_token, session)


def account_email(access_token: str, session=None) -> str:
    """The Gmail address an access token belongs to."""
    response = (session or requests).get("https://gmail.googleapis.com/gmail/v1/users/me/profile",
                                         headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    response.raise_for_status()
    return (response.json().get("emailAddress") or "").lower()


def authorize_mailbox(mailbox: str) -> None:
    """Interactive consent flow; stores the refresh token in .env."""
    client_id, client_secret = _client()
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    result: dict = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            result.update({k: v[0] for k, v in query.items()})
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Velarqo: mailbox connected. You can close this tab.")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect_uri = f"http://127.0.0.1:{server.server_port}"
    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "login_hint": mailbox,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    print(f"Opening Google sign-in for {mailbox}. If no browser opens, visit:\n{url}")
    webbrowser.open(url)
    while "code" not in result and "error" not in result:
        server.handle_request()
    server.server_close()

    if result.get("state") != state or "code" not in result:
        raise RuntimeError(f"Authorization failed: {result.get('error', 'state mismatch')}")

    response = requests.post(TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": result["code"],
        "code_verifier": verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }, timeout=30)
    response.raise_for_status()
    tokens = response.json()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("Google returned no refresh token; remove the app's access at myaccount.google.com and retry")
    # login_hint doesn't force the account: with several mailboxes signed in
    # to one browser, Google may hand back a token for the wrong one.
    actual = account_email(tokens["access_token"])
    if actual != mailbox.lower():
        raise RuntimeError(f"Google signed in as {actual}, not {mailbox}. Nothing saved. "
                           f"Sign out of {actual} (or use a private window) and run authorize-mailbox again.")
    set_key(str(ENV_PATH), refresh_env_key(mailbox), refresh_token)
    print(f"Saved refresh token for {mailbox} to .env as {refresh_env_key(mailbox)}")
