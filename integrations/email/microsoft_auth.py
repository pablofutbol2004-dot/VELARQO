"""OAuth for Velarqo's own Microsoft 365 sending mailboxes (Microsoft Graph).

Mirror of google_auth.py. One-time per mailbox:
`python -m pipelines.outbound authorize-mailbox you@domain` opens Microsoft's
sign-in page, catches the redirect on localhost, and writes the long-lived
refresh token into .env (gitignored) - it is never printed. After that,
access_token_for() swaps the refresh token for a ~1-hour access token on
every run.

Differences from Google worth knowing:
- The app is a *public client* (type "Mobile and desktop applications"), so
  there is no client secret: PKCE protects the code exchange instead.
- Microsoft rotates refresh tokens: every refresh may hand back a new one,
  and the old one eventually stops working. refresh_access_token() saves the
  new one to .env whenever it changes.
- Refresh tokens for public clients expire after 90 days without use; a
  mailbox that sends every weekday never hits that.

Setup (Microsoft Entra admin centre, once per tenant) is in docs/LAUNCH.md.
.env needs MS_CLIENT_ID (application id) and MS_TENANT_ID (directory id, or
the tenant's primary domain such as example.onmicrosoft.com).
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

# Delegated permissions. Mail.ReadWrite (not just Mail.Read) because a
# threaded follow-up is a draft reply that gets edited before sending.
SCOPES = ["offline_access", "User.Read", "Mail.ReadWrite", "Mail.Send"]
ENV_PATH = Path(__file__).parents[2] / ".env"
GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"


def refresh_env_key(mailbox: str) -> str:
    return "OUTLOOK_REFRESH_TOKEN_" + re.sub(r"[^A-Za-z0-9]", "_", mailbox).upper()


def _client() -> tuple[str, str]:
    load_dotenv(ENV_PATH)
    client_id, tenant = os.environ.get("MS_CLIENT_ID"), os.environ.get("MS_TENANT_ID")
    if not client_id or not tenant:
        raise RuntimeError("MS_CLIENT_ID and MS_TENANT_ID must be set in .env (see docs/LAUNCH.md, Microsoft section)")
    return client_id, tenant


def token_url(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


def auth_url(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"


def _error_text(response) -> str:
    try:
        data = response.json()
        return f"{data.get('error')}: {str(data.get('error_description', ''))[:200]}"
    except ValueError:
        return f"HTTP {response.status_code}"


def refresh_access_token(client_id: str, tenant: str, refresh_token: str, session: requests.Session | None = None,
                         mailbox: str | None = None, env_path: Path = ENV_PATH) -> str:
    """Access token for a refresh token. If Microsoft rotates the refresh
    token, the new one replaces the old in .env (when `mailbox` is given)."""
    response = (session or requests.Session()).post(token_url(tenant), data={
        "client_id": client_id,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "scope": " ".join(SCOPES),
    }, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Microsoft refused the refresh token ({_error_text(response)}); "
                           f"re-run authorize-mailbox for {mailbox or 'this mailbox'}")
    tokens = response.json()
    rotated = tokens.get("refresh_token")
    if mailbox and rotated and rotated != refresh_token:
        set_key(str(env_path), refresh_env_key(mailbox), rotated)
        os.environ[refresh_env_key(mailbox)] = rotated
    return tokens["access_token"]


def access_token_for(mailbox: str, session: requests.Session | None = None) -> str:
    client_id, tenant = _client()
    refresh_token = os.environ.get(refresh_env_key(mailbox))
    if not refresh_token:
        raise RuntimeError(f"No refresh token for {mailbox}: run `python -m pipelines.outbound authorize-mailbox {mailbox}`")
    return refresh_access_token(client_id, tenant, refresh_token, session, mailbox=mailbox)


def account_email(access_token: str, session=None) -> str:
    """The Microsoft 365 address an access token belongs to."""
    response = (session or requests).get(GRAPH_ME_URL, params={"$select": "mail,userPrincipalName"},
                                         headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    response.raise_for_status()
    data = response.json()
    return (data.get("mail") or data.get("userPrincipalName") or "").lower()


def save_tokens(mailbox: str, tokens: dict, env_path: Path = ENV_PATH, lookup=account_email) -> str:
    """Checks the token really belongs to `mailbox`, then stores the refresh
    token. Returns the .env key written. Never prints token material."""
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("Microsoft returned no refresh token: make sure offline_access was granted and retry")
    # With several mailboxes signed in to one browser, Microsoft may hand back
    # a token for the wrong one; login_hint is only a hint.
    actual = lookup(tokens["access_token"])
    if actual != mailbox.lower():
        raise RuntimeError(f"Microsoft signed in as {actual}, not {mailbox}. Nothing saved. "
                           f"Use a private window (or sign out of {actual}) and run authorize-mailbox again.")
    key = refresh_env_key(mailbox)
    set_key(str(env_path), key, refresh_token)
    return key


def authorize_mailbox(mailbox: str) -> None:
    """Interactive consent flow (authorization code + PKCE); stores the
    refresh token in .env."""
    client_id, tenant = _client()
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
    # Entra matches any port for a registered http://localhost redirect.
    redirect_uri = f"http://localhost:{server.server_port}"
    url = auth_url(tenant) + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "response_mode": "query",
        "scope": " ".join(SCOPES),
        "prompt": "select_account",
        "login_hint": mailbox,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    print(f"Opening Microsoft sign-in for {mailbox}. If no browser opens, visit:\n{url}")
    webbrowser.open(url)
    while "code" not in result and "error" not in result:
        server.handle_request()
    server.server_close()

    if result.get("state") != state or "code" not in result:
        raise RuntimeError(f"Authorization failed: {result.get('error', 'state mismatch')}: "
                           f"{result.get('error_description', '')[:200]}")

    response = requests.post(token_url(tenant), data={
        "client_id": client_id,
        "code": result["code"],
        "code_verifier": verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
    }, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Token exchange failed ({_error_text(response)}). If it says a client secret is required, "
                           "set 'Allow public client flows' to Yes on the app registration.")
    key = save_tokens(mailbox, response.json())
    print(f"Saved refresh token for {mailbox} to .env as {key}")
