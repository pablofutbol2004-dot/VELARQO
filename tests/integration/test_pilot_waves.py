"""Wave sending against a fake GoHighLevel, on the real database (rolled back).
Run with VELARQO_DB_TESTS=1."""

import os
import uuid
from datetime import date

import psycopg
import pytest
import requests

from integrations.ghl.client import GHLTemporaryError

pytestmark = pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")


class FakeGHL:
    def __init__(self, fail_once=(), bad=(), on_upsert=None):
        self.contacts, self.tags, self.upserts = {}, {}, 0
        self.fail_once, self.bad, self.on_upsert = set(fail_once), set(bad), on_upsert

    def upsert_contact(self, contact):
        self.upserts += 1
        if self.on_upsert:
            self.on_upsert(self.upserts)
        phone = contact["phone"]
        if phone in self.bad:
            response = requests.Response()
            response.status_code = 422
            raise requests.HTTPError("invalid phone", response=response)
        if phone in self.fail_once:
            self.fail_once.discard(phone)
            self.contacts.setdefault(phone, f"c-{phone}")    # GHL created it, then the reply timed out
            raise GHLTemporaryError("timeout")
        return {"contact": {"id": self.contacts.setdefault(phone, f"c-{phone}")}}  # dedupe by phone

    def add_tags(self, contact_id, tags):
        self.tags.setdefault(contact_id, set()).update(tags)
        return {}


@pytest.fixture()
def pilot():
    from data.supabase_store import connect
    from delivery.pilot import freeze_pilot, import_records

    conn = connect()
    pilot_id = f"test-{uuid.uuid4().hex[:8]}"
    run = uuid.uuid4()
    tx = conn.transaction()
    tx.__enter__()
    conn.execute("insert into pilots (id, client_slug, vertical, holdout_fraction, state) values (%s, 'test', 'windows', 0.2, 'data_received')",
                 (pilot_id,))
    records = [{"Ref": f"Q{i}", "Quote Date": "01/05/2026", "Status": "Lost", "Phone": f"07700900{i:03d}", "Name": f"Home Owner{i}"}
               for i in range(20)]
    import_records(conn, pilot_id, records, set(), run, date(2026, 10, 10))
    freeze_pilot(conn, pilot_id, run)                       # 16 treatment, 4 holdout
    conn.execute("update pilots set state = 'canary_running' where id = %s", (pilot_id,))
    yield conn, pilot_id
    try:
        tx.__exit__(psycopg.Rollback, psycopg.Rollback(), None)
    finally:
        conn.close()


def states(conn, pilot_id):
    return dict(conn.execute("select state, count(*) from pilot_homeowners where pilot_id = %s group by 1", (pilot_id,)).fetchall())


def test_wave_enrols_treatment_only_and_claiming_is_idempotent(pilot):
    from delivery.ghl_push import claim_wave, send_wave
    conn, pilot_id = pilot
    assert claim_wave(conn, pilot_id, "w1", 5) == 5
    assert claim_wave(conn, pilot_id, "w1", 5) == 0          # re-running doesn't grow the wave
    ghl = FakeGHL()
    assert send_wave(conn, ghl, pilot_id, "w1")["enrolled"] == 5
    assert all(tags == {"vq-w1"} for tags in ghl.tags.values()) and len(ghl.tags) == 5
    assert states(conn, pilot_id) == {"enrolled": 5, "treatment": 11, "holdout": 4}
    assert send_wave(conn, ghl, pilot_id, "w1")["enrolled"] == 0   # a second run sends nothing


def test_timeout_after_ghl_created_the_contact_recovers_without_duplicates(pilot):
    from delivery.ghl_push import claim_wave, send_wave
    conn, pilot_id = pilot
    claim_wave(conn, pilot_id, "w1", 3)
    phones = [p for (p,) in conn.execute("select phone from pilot_homeowners where pilot_id = %s and wave_id = 'w1'", (pilot_id,))]
    ghl = FakeGHL(fail_once={phones[0]})
    first = send_wave(conn, ghl, pilot_id, "w1")
    assert first["enrolled"] == 2 and first["left_for_retry"] == 1
    assert states(conn, pilot_id)["pushing"] == 1             # parked, not lost
    second = send_wave(conn, ghl, pilot_id, "w1")
    assert second["enrolled"] == 1
    assert len(ghl.contacts) == 3 and len(ghl.tags) == 3      # one contact, one tag each


def test_bad_data_is_marked_push_failed_with_the_error(pilot):
    from delivery.ghl_push import claim_wave, send_wave
    conn, pilot_id = pilot
    claim_wave(conn, pilot_id, "w1", 2)
    phone = conn.execute("select phone from pilot_homeowners where pilot_id = %s and wave_id = 'w1' limit 1", (pilot_id,)).fetchone()[0]
    result = send_wave(conn, FakeGHL(bad={phone}), pilot_id, "w1")
    assert result == {"enrolled": 1, "push_failed": 1, "left_for_retry": 0, "stopped": False}
    error = conn.execute("select push_error from pilot_homeowners where pilot_id = %s and phone = %s", (pilot_id, phone)).fetchone()[0]
    assert "422" in error


def test_pausing_mid_wave_stops_further_sends(pilot):
    from delivery.ghl_push import claim_wave, send_wave
    conn, pilot_id = pilot
    claim_wave(conn, pilot_id, "w1", 5)

    def pause_after_two(n):
        if n == 2:
            conn.execute("update pilots set state = 'paused' where id = %s", (pilot_id,))

    result = send_wave(conn, FakeGHL(on_upsert=pause_after_two), pilot_id, "w1")
    assert result["stopped"] and result["enrolled"] == 2
    assert states(conn, pilot_id)["queued"] == 3


def test_opt_out_after_queueing_is_never_sent(pilot):
    from delivery.ghl_push import claim_wave, send_wave
    conn, pilot_id = pilot
    claim_wave(conn, pilot_id, "w1", 3)
    key = conn.execute("select homeowner_key from pilot_homeowners where pilot_id = %s and wave_id = 'w1' limit 1", (pilot_id,)).fetchone()[0]
    conn.execute("update pilot_homeowners set state = 'opted_out' where pilot_id = %s and homeowner_key = %s", (pilot_id, key))
    ghl = FakeGHL()
    assert send_wave(conn, ghl, pilot_id, "w1")["enrolled"] == 2
    assert ghl.upserts == 2


def test_waves_refuse_to_start_unless_the_pilot_is_sending(pilot):
    from delivery.ghl_push import WaveError, claim_wave
    conn, pilot_id = pilot
    conn.execute("update pilots set state = 'paused' where id = %s", (pilot_id,))
    with pytest.raises(WaveError):
        claim_wave(conn, pilot_id, "w1", 5)
