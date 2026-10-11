"""A stand-in for GHLClient that never touches the network. Every call that
would have gone to GoHighLevel is appended to a JSONL file instead, so a dry
run shows exactly what would have been sent (contacts, tags = texts
starting, do-not-disturb) without texting anyone.

Only pilots whose GHL location id starts with "dry-" may use it: the wave
code marks homeowners "enrolled" after a successful call, and a real pilot
run against this fake would record texts that never went out.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

DRY_PREFIX = "dry-"


class DryRunRefused(Exception):
    pass


class DryRunGHL:
    def __init__(self, log_path: Path, location_id: str):
        if not str(location_id).startswith(DRY_PREFIX):
            raise DryRunRefused(f"dry-run GHL only for pilots whose location id starts with '{DRY_PREFIX}' (got {location_id!r})")
        self.log_path, self.location_id = Path(log_path), location_id
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.calls: list[dict] = []

    def _log(self, call: str, **payload) -> None:
        entry = {"at": datetime.now(timezone.utc).isoformat(), "call": call, **payload}
        self.calls.append(entry)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def upsert_contact(self, contact: dict) -> dict:
        basis = contact.get("phone") or contact.get("email") or json.dumps(contact, sort_keys=True)
        contact_id = DRY_PREFIX + hashlib.sha1(f"{self.location_id}:{basis}".encode()).hexdigest()[:12]
        self._log("upsert_contact", contact=contact, contact_id=contact_id)
        return {"contact": {"id": contact_id}}

    def add_tags(self, contact_id: str, tags: list[str]) -> dict:
        self._log("add_tags", contact_id=contact_id, tags=tags, note="this is where the GHL workflow would start texting")
        return {}

    def remove_tags(self, contact_id: str, tags: list[str]) -> dict:
        self._log("remove_tags", contact_id=contact_id, tags=tags)
        return {}

    def set_dnd(self, contact_id: str) -> dict:
        self._log("set_dnd", contact_id=contact_id)
        return {}
