"""Tiny HTTP endpoint for GoHighLevel webhooks. Runs on the VPS behind HTTPS
(e.g. Caddy) at https://<host>/ghl/webhook; locally for tests.

    python -m delivery.webhook_server --port 8787

Two ways a request is trusted (one must pass):
- GHL's RSA signature (x-wh-signature), used by Marketplace-app webhooks;
- our shared secret in `x-velarqo-secret` (env VELARQO_WEBHOOK_SECRET), for
  GHL *workflow* "Webhook" actions, which are unsigned. Which one GHL will
  actually send for a Private Integration sub-account must be confirmed at
  setup (WORKFLOW.md "verify against real GHL").

Returns 200 only after the event is committed (or recognised as a duplicate),
so GHL retries anything we failed to store. Untrusted → 401, malformed → 400.
After storing, pending opt-outs for that pilot are pushed to GHL (best effort;
`check` retries). No third-party web framework: stdlib only, one route.
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import click

from data.supabase_store import connect
from delivery.webhooks import BadSignature, check_fresh, handle_event, verify_secret, verify_signature

MAX_BODY = 1_000_000
log = logging.getLogger("velarqo.webhooks")


def authenticate(raw: bytes, headers, secret: str | None) -> None:
    signature = headers.get("x-wh-signature")
    if signature:
        verify_signature(raw, signature)
    else:
        verify_secret(headers.get("x-velarqo-secret"), secret)


def make_handler(get_conn, secret: str | None = None, after=None):
    class Handler(BaseHTTPRequestHandler):
        def _reply(self, code: int, text: str):
            body = text.encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path.rstrip("/") != "/ghl/webhook":
                return self._reply(404, "not found")
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return self._reply(400, "bad length")
            if length <= 0 or length > MAX_BODY:
                return self._reply(413, "bad length")
            raw = self.rfile.read(length)
            try:
                authenticate(raw, self.headers, secret)
                event = json.loads(raw)
                if not isinstance(event, dict):
                    raise ValueError("not an object")
                check_fresh(event)
            except BadSignature as exc:
                log.warning("rejected webhook: %s", exc)
                return self._reply(401, "unauthorised")
            except (ValueError, TypeError, UnicodeDecodeError):
                return self._reply(400, "malformed")
            conn = None
            try:
                conn = get_conn()  # one autocommit connection per request: threads never share a transaction
                outcome = handle_event(conn, event)
                if after:
                    after(conn, event)
            except Exception:  # noqa: BLE001 - non-200 makes GHL retry later
                log.exception("failed to store webhook %s", event.get("type"))
                return self._reply(500, "retry later")
            finally:
                if conn is not None:
                    conn.close()
            log.info("%s %s -> %s", event.get("type"), event.get("locationId"), outcome)
            return self._reply(200, outcome)

        def log_message(self, fmt, *args):  # route http.server's noise through logging
            log.debug(fmt, *args)

    return Handler


def push_opt_outs_after(conn, event: dict) -> None:
    """Best effort: send any new do-not-disturb to GHL right away."""
    from delivery.ghl_push import push_opt_outs
    from delivery.pilot import PilotError, ghl_client_for

    row = conn.execute("select id from pilots where ghl_location_id = %s", (event.get("locationId"),)).fetchone()
    if not row:
        return
    try:
        client, _ = ghl_client_for(conn, row[0])
        push_opt_outs(conn, client, row[0])
    except (PilotError, Exception) as exc:  # noqa: BLE001 - never fail the webhook over this; `check` retries
        log.warning("opt-out push deferred for %s: %s", row[0], exc)


@click.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind address; keep localhost behind a reverse proxy")
@click.option("--port", default=8787, show_default=True)
def main(host, port):
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    def fresh_connection():
        conn = connect()
        conn.autocommit = True
        return conn

    secret = os.environ.get("VELARQO_WEBHOOK_SECRET")
    server = ThreadingHTTPServer((host, port), make_handler(fresh_connection, secret, push_opt_outs_after))
    log.info("listening on %s:%s/ghl/webhook (shared secret %s)", host, port, "set" if secret else "NOT set")
    server.serve_forever()


if __name__ == "__main__":
    main()
