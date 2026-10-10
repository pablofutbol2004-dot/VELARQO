"""Tiny HTTP endpoint for GoHighLevel webhooks. Runs on the VPS behind HTTPS
(e.g. Caddy) at https://<host>/ghl/webhook; locally for tests.

    python -m delivery.webhook_server --port 8787

Returns 200 only after the event is committed (or recognised as a duplicate /
not ours), so GHL retries anything we failed to store. Bad signatures → 401.
No third-party web framework: stdlib only, one route.
"""

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import click

from data.supabase_store import connect
from delivery.webhooks import BadSignature, check_fresh, handle_event, verify_signature

MAX_BODY = 1_000_000
log = logging.getLogger("velarqo.webhooks")


def make_handler(get_conn, verify=True):
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
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_BODY:
                return self._reply(413, "bad length")
            raw = self.rfile.read(length)
            try:
                if verify:
                    verify_signature(raw, self.headers.get("x-wh-signature"))
                event = json.loads(raw)
                if verify:
                    check_fresh(event)
            except BadSignature as exc:
                log.warning("rejected webhook: %s", exc)
                return self._reply(401, "unauthorised")
            except json.JSONDecodeError:
                return self._reply(400, "not json")
            conn = None
            try:
                conn = get_conn()  # one connection per request: threads never share a transaction
                outcome = handle_event(conn, event)
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


@click.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind address; keep localhost behind a reverse proxy")
@click.option("--port", default=8787, show_default=True)
def main(host, port):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    def fresh_connection():
        conn = connect()
        conn.autocommit = True
        return conn

    server = ThreadingHTTPServer((host, port), make_handler(fresh_connection))
    log.info("listening on %s:%s/ghl/webhook", host, port)
    server.serve_forever()


if __name__ == "__main__":
    main()
