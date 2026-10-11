"""A stateful stand-in for Microsoft Graph's mail endpoints, used instead of
a network session by OutlookProvider in tests. It models just enough to
prove the engine's flow: drafts, send (Drafts -> Sent Items with a stable
id), createReply (In-Reply-To/References + same conversationId), PATCH,
listing received messages, reading one, /me, 401, 429.
"""

import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import requests


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code, self._json, self.headers = status_code, json_data if json_data is not None else {}, headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"HTTP {self.status_code}")
            err.response = self
            raise err

    def json(self):
        return self._json


class FakeGraph:
    """`session.request(...)` compatible. Messages live in self.messages
    keyed by id; folder is 'drafts', 'sentitems' or 'inbox'."""

    def __init__(self, mailbox="pablo@velarqomail.com", token="tok"):
        self.mailbox, self.token = mailbox, token
        self.messages: dict[str, dict] = {}
        self.calls: list[dict] = []
        self.fail_next: list[FakeResponse] = []   # canned responses returned before any real handling
        self._n = 0

    # --- helpers for tests -----------------------------------------------

    def receive(self, from_email, subject, body, conversation_id=None, headers=None, content_type="text",
                received=None):
        """Drop an incoming message into the inbox; returns its id."""
        mid = self._new_id("in")
        self.messages[mid] = {
            "id": mid, "folder": "inbox", "isDraft": False, "conversationId": conversation_id or self._new_id("conv"),
            "from": {"emailAddress": {"address": from_email}}, "subject": subject,
            "body": {"contentType": content_type, "content": body},
            "receivedDateTime": (received or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "internetMessageHeaders": [{"name": k, "value": v} for k, v in (headers or {}).items()],
            "internetMessageId": f"<{mid}@theirs.example>",
        }
        return mid

    def sent(self):
        return [m for m in self.messages.values() if m["folder"] == "sentitems"]

    def _new_id(self, prefix):
        self._n += 1
        return f"{prefix}-{self._n}"

    # --- the fake API -------------------------------------------------------

    def request(self, method, url, headers=None, json=None, params=None, timeout=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "json": json, "params": params})
        if self.fail_next:
            return self.fail_next.pop(0)
        if (headers or {}).get("Authorization") != f"Bearer {self.token}":
            return FakeResponse(401, {"error": {"code": "InvalidAuthenticationToken"}})
        if 'IdType="ImmutableId"' not in (headers or {}).get("Prefer", ""):
            return FakeResponse(400, {"error": {"code": "test: Prefer IdType=ImmutableId missing"}})
        path = urlparse(url).path.replace("/v1.0", "")
        query = {**{k: v[0] for k, v in parse_qs(urlparse(url).query).items()}, **(params or {})}

        if path == "/me":
            return FakeResponse(200, {"mail": self.mailbox, "userPrincipalName": self.mailbox})
        if method == "POST" and path == "/me/messages":
            return self._create(json, parent=None)
        m = re.fullmatch(r"/me/messages/([^/]+)(/createReply|/send)?", path)
        if m:
            mid, action = m.group(1), m.group(2)
            msg = self.messages.get(mid)
            if msg is None:
                return FakeResponse(404, {"error": {"code": "ErrorItemNotFound"}})
            if action == "/createReply":
                return self._create({}, parent=msg)
            if action == "/send":
                if msg["folder"] != "drafts":
                    return FakeResponse(400, {"error": {"code": "ErrorInvalidRecipients"}})
                msg["folder"], msg["isDraft"] = "sentitems", False
                msg["sentDateTime"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                return FakeResponse(202)
            if method == "PATCH":
                if msg["folder"] != "drafts":
                    return FakeResponse(400, {"error": {"code": "ErrorCannotUpdateSentItem"}})
                msg.update(json or {})
                return FakeResponse(200, self._public(msg))
            if method == "GET":
                return FakeResponse(200, self._public(msg, query.get("$select"), (headers or {}).get("Prefer", "")))
        if method == "GET" and path in ("/me/messages", "/me/mailFolders/sentitems/messages"):
            rows = [m for m in self.messages.values()
                    if path == "/me/messages" or m["folder"] == "sentitems"]
            rows = [m for m in rows if self._matches(m, query.get("$filter", ""))]
            top = int(query.get("$top", 100))
            skip = int(query.get("$skip", 0))
            page = rows[skip:skip + top]
            data = {"value": [self._public(m, query.get("$select")) for m in page]}
            if skip + top < len(rows):
                data["@odata.nextLink"] = (f"https://graph.microsoft.com/v1.0{path}?$top={top}&$skip={skip + top}"
                                           f"&$select={query.get('$select', '')}&$filter={query.get('$filter', '')}")
            return FakeResponse(200, data)
        return FakeResponse(404, {"error": {"code": f"test: unhandled {method} {path}"}})

    def _create(self, fields, parent):
        mid = self._new_id("msg")
        msg = {"id": mid, "folder": "drafts", "isDraft": True,
               "from": {"emailAddress": {"address": self.mailbox}}, "subject": "", "toRecipients": [],
               "body": {"contentType": "text", "content": ""}, "internetMessageHeaders": [],
               "internetMessageId": f"<{mid}@velarqomail.example>"}
        if parent is not None:
            msg["conversationId"] = parent["conversationId"]
            msg["subject"] = "RE: " + parent["subject"]
            msg["toRecipients"] = [parent["from"]]          # a reply goes back to the sender: us, for a sent item
            refs = {h["name"].lower(): h["value"] for h in parent.get("internetMessageHeaders", [])}.get("references", "")
            msg["internetMessageHeaders"] = [
                {"name": "In-Reply-To", "value": parent["internetMessageId"]},
                {"name": "References", "value": f"{refs} {parent['internetMessageId']}".strip()},
            ]
        else:
            msg["conversationId"] = self._new_id("conv")
        msg.update(fields or {})
        self.messages[mid] = msg
        return FakeResponse(201, self._public(msg))

    def _public(self, msg, select=None, prefer=""):
        out = {k: v for k, v in msg.items() if k != "folder"}
        if "internetMessageHeaders" not in (select or "internetMessageHeaders"):
            out.pop("internetMessageHeaders", None)
        if select:
            out = {k: v for k, v in out.items() if k == "id" or k in select.split(",")}
        if "body" in out and 'outlook.body-content-type="text"' in prefer and out["body"]["contentType"] == "html":
            out = {**out, "body": {"contentType": "text", "content": re.sub(r"<[^>]+>", "", out["body"]["content"])}}
        return out

    def _matches(self, msg, filter_):
        for clause in filter_.split(" and ") if filter_ else []:
            m = re.fullmatch(r"(\w+) (eq|ge) (.+)", clause.strip())
            field, op, value = m.groups()
            value = value.strip("'")
            actual = msg.get(field)
            if op == "eq" and str(actual).lower() != value.lower():
                return False
            if op == "ge" and (actual or "") < value:
                return False
        return True
