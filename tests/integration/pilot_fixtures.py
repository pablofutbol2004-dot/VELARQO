"""Shared helpers for pilot tests that COMMIT for real (the delivery code needs
autocommit connections), then delete everything the test created."""

import os
import uuid
from contextlib import contextmanager
from datetime import date

import pytest

DB = pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")
TODAY = date(2026, 10, 10)


def autocommit():
    from data.supabase_store import connect

    conn = connect()
    conn.autocommit = True
    return conn


def cleanup(pilot_id: str) -> None:
    conn = autocommit()
    try:
        with conn.transaction():
            for table in ("invoice_lines", "invoices", "pilot_events", "pilot_approvals", "pilot_homeowners"):
                conn.execute(f"delete from {table} where pilot_id = %s", (pilot_id,))
            conn.execute("delete from pilots where id = %s", (pilot_id,))
    finally:
        conn.close()


def records(n: int, **extra) -> list[dict]:
    return [{"Ref": f"Q{i}", "Quote Date": "01/05/2026", "Status": "Lost", "Phone": f"07700900{i:03d}",
             "Name": f"Ann{i} Smith", "Postcode": "LS1 1AA", **extra} for i in range(n)]


@contextmanager
def pilot(n_records=30, holdout=0.2, state="canary_running", wave_size=None, rows=None, **pilot_cols):
    """A frozen pilot with `n_records` homeowners, moved to `state`, committed.
    Optionally claims `wave_size` into w1 and marks them enrolled with fake
    GHL contact ids. Yields (conn, pilot_id, location, contact_ids)."""
    from delivery.ghl_push import claim_wave
    from delivery.pilot import freeze_pilot, import_records

    conn = autocommit()
    pilot_id = f"test-{uuid.uuid4().hex[:8]}"
    location = f"loc-{pilot_id}"
    run = uuid.uuid4()
    try:
        columns = {"ghl_location_id": location, "ghl_calendar_id": "cal-1", **pilot_cols}
        with conn.transaction():
            conn.execute(
                f"insert into pilots (id, client_slug, vertical, holdout_fraction, state, {', '.join(columns)}) "
                f"values (%s, 'test', 'windows', %s, 'data_received', {', '.join(['%s'] * len(columns))})",
                (pilot_id, holdout, *columns.values()))
            import_records(conn, pilot_id, rows if rows is not None else records(n_records), set(), run, TODAY)
            freeze_pilot(conn, pilot_id, run)
            conn.execute("update pilots set state = %s where id = %s", (state, pilot_id))
        contacts = []
        if wave_size:
            claim_wave(conn, pilot_id, "w1", wave_size)
            with conn.transaction():
                conn.execute("update pilot_homeowners set state = 'enrolled', ghl_contact_id = 'c-' || phone "
                             "where pilot_id = %s and wave_id = 'w1'", (pilot_id,))
            contacts = [c for (c,) in conn.execute(
                "select ghl_contact_id from pilot_homeowners where pilot_id = %s and wave_id = 'w1' order by 1", (pilot_id,))]
        yield conn, pilot_id, location, contacts
    finally:
        conn.close()
        cleanup(pilot_id)
