import os
import uuid
from datetime import date

import psycopg
import pytest

from tests.integration import pilot_fixtures  # noqa: F401 - sets the test key secret first
from delivery.pilot import eligibility, homeowner_key, postcode_area
from delivery.split import split
from delivery.states import allowed_pilot_moves, can_move_homeowner

TODAY = date(2026, 10, 10)


def test_pilot_moves_follow_the_flow_and_can_always_cancel():
    assert allowed_pilot_moves("draft") == {"sample_received", "cancelled"}
    assert "paused" in allowed_pilot_moves("live")
    assert allowed_pilot_moves("paused") == {"live", "completed", "cancelled"}
    assert allowed_pilot_moves("completed") == set()
    assert "live" not in allowed_pilot_moves("canary_ready")


def test_homeowners_only_move_forward_and_opt_out_wins():
    assert can_move_homeowner("enrolled", "replied")
    assert can_move_homeowner("replied", "booked")
    assert not can_move_homeowner("booked", "replied")        # late webhook can't go backwards
    assert not can_move_homeowner("won", "attended")
    assert can_move_homeowner("booked", "opted_out")
    assert not can_move_homeowner("opted_out", "enrolled")
    assert not can_move_homeowner("holdout", "queued")        # comparison group is never contacted
    assert can_move_homeowner("push_failed", "pushing")       # retry after fixing the error


def test_split_is_deterministic_stratified_and_the_right_size():
    homeowners = [(f"k{i}", "3-6 months" if i % 2 else "6-12 months") for i in range(200)]
    first = split("p1", homeowners, 0.15)
    assert first == split("p1", list(reversed(homeowners)), 0.15)   # same split whatever the order
    for stratum in ("3-6 months", "6-12 months"):
        keys = [k for k, s in homeowners if s == stratum]
        assert sum(first[k] == "holdout" for k in keys) == 15        # 15% of 100 in each age band
    assert split("p2", homeowners, 0.15) != first                    # each pilot gets its own draw


def test_homeowner_key_is_stable_and_prefers_the_record_id():
    a = homeowner_key("acme", {"record_id": "Q-1001", "phone": "07700 900123"})
    assert a == homeowner_key("acme", {"record_id": "Q-1001", "phone": "different"})
    assert a != homeowner_key("other-client", {"record_id": "Q-1001"})
    # no ID: same phone written two ways is the same person
    assert homeowner_key("acme", {"phone": "07700 900123"}) == homeowner_key("acme", {"phone": "+447700900123"})


def test_eligibility_adds_contact_area_and_do_not_contact_checks():
    base = {"quote_date": "01/05/2026", "quote_status": "Lost", "phone": "07700900123", "postcode": "LS12 4JS"}
    assert eligibility(base, ["LS"], set(), TODAY) == (None, 5)
    assert eligibility({**base, "phone": None}, ["LS"], set(), TODAY)[0] == "no UK mobile or email"
    assert eligibility(base, ["BD"], set(), TODAY)[0] == "outside service area"
    assert eligibility(base, [], {"+447700900123"}, TODAY)[0] == "on client's do-not-contact list"
    assert eligibility({**base, "quote_status": "Sold"}, [], set(), TODAY)[0] == "already won/booked"
    assert postcode_area("b6 7db") == "B" and postcode_area("SW1A 1AA") == "SW"


@pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1 to run against the database")
def test_import_freeze_and_the_database_blocks_contacting_the_holdout():
    from data.supabase_store import connect
    from delivery.pilot import advance_pilot, freeze_pilot, import_records

    conn = connect()
    run = uuid.uuid4()
    pilot_id = f"test-{uuid.uuid4().hex[:8]}"
    records = [{"Ref": f"Q{i}", "Quote Date": "01/05/2026", "Status": "Lost", "Phone": f"07700900{i:03d}",
                "Postcode": "LS1 1AA", "Job Type": "Windows"} for i in range(40)]
    records.append({"Ref": "Q999", "Quote Date": "01/05/2026", "Status": "Sold", "Phone": "07700900999", "Postcode": "LS1 1AA"})
    try:
        with conn.transaction():
            conn.execute("insert into pilots (id, client_slug, vertical, holdout_fraction) values (%s, 'test', 'windows', 0.25)", (pilot_id,))
            for state in ("sample_received", "audited"):
                advance_pilot(conn, pilot_id, state, run)
            with pytest.raises(Exception, match="agreement"):
                advance_pilot(conn, pilot_id, "agreement_signed", run)   # gate not approved yet
            conn.execute("insert into pilot_approvals (pilot_id, gate, decision, actor) values (%s, 'agreement', 'approved', 'test')", (pilot_id,))
            advance_pilot(conn, pilot_id, "agreement_signed", run)
            advance_pilot(conn, pilot_id, "data_received", run)

            stats = import_records(conn, pilot_id, records, set(), run, TODAY)
            assert stats["new"] == 41 and stats["eligible"] == 40 and stats["excluded"] == {"already won/booked": 1}
            again = import_records(conn, pilot_id, records, set(), run, TODAY)
            assert again["new"] == 0 and again["updated"] == 41 and again["eligible"] == 40   # re-import re-checks, adds nobody

            counts = freeze_pilot(conn, pilot_id, run)
            assert counts == {"treatment": 30, "holdout": 10}
            with pytest.raises(Exception, match="frozen|unfrozen"):
                freeze_pilot(conn, pilot_id, run)                                 # can't re-draw the split

            with pytest.raises(psycopg.errors.CheckViolation):
                with conn.transaction():
                    conn.execute("update pilot_homeowners set wave_id = 'w1', state = 'queued' "
                                 "where pilot_id = %s and arm = 'holdout'", (pilot_id,))
            raise psycopg.Rollback()
    finally:
        conn.close()


@pytest.mark.parametrize("source,excluded", [
    ("Checkatrade", True), ("bark.com", True), ("Bought leads", True), ("MyBuilder", True),
    ("Website form", False), ("Phone", False), ("Barking showroom", False), ("Yellow pages ad", False), (None, False),
])
def test_lead_site_and_bought_leads_are_excluded(source, excluded):
    base = {"quote_date": "01/05/2026", "quote_status": "Lost", "phone": "07700900123", "lead_source": source}
    reason, _ = eligibility(base, [], set(), TODAY)
    assert (reason == "came from a lead site or bought list") is excluded


@pytest.mark.parametrize("raw,expected", [
    ("07700 900123", "+447700900123"), ("7700900123", "+447700900123"), ("7700900123.0", "+447700900123"),
    (7700900123.0, "+447700900123"), ("+44 7700 900123", "+447700900123"), ("0044 7700 900123", "+447700900123"),
    ("447700900123", "+447700900123"), ("0113 318 8299", None), ("+1 415 555 0100", None), ("", None), (None, None),
    ("+44 (0)7700 900123", "+447700900123"), ("+44(0)7700900123", "+447700900123"), ("0044 (0) 7700 900123", "+447700900123"),
])
def test_only_uk_mobiles_count_as_textable(raw, expected):
    from delivery.contacts import uk_mobile
    assert uk_mobile(raw) == expected


@pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")
def test_reimport_with_a_do_not_contact_list_applies_it_and_optout_works_after_freeze():
    from tests.integration.pilot_fixtures import autocommit, cleanup, records
    from delivery.pilot import import_records, opt_out_people

    conn = autocommit()
    pilot_id = f"test-{uuid.uuid4().hex[:8]}"
    try:
        with conn.transaction():
            conn.execute("insert into pilots (id, client_slug, vertical, state) values (%s, 'test', 'windows', 'data_received')", (pilot_id,))
            first = import_records(conn, pilot_id, records(10), set(), uuid.uuid4(), TODAY)
            assert first["eligible"] == 10
            second = import_records(conn, pilot_id, records(10), {"+447700900003"}, uuid.uuid4(), TODAY)
            assert second["eligible"] == 9 and second["excluded"] == {"on client's do-not-contact list": 1}
        with conn.transaction():
            assert opt_out_people(conn, pilot_id, {"+447700900004"}, uuid.uuid4(), "test") == 1
        assert conn.execute("select state from pilot_homeowners where pilot_id = %s and phone = '+447700900004'",
                            (pilot_id,)).fetchone()[0] == "opted_out"
    finally:
        conn.close()
        cleanup(pilot_id)


@pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")
def test_purge_removes_personal_data_once_the_pilot_has_ended():
    from tests.integration.pilot_fixtures import pilot
    from delivery.pilot import PilotError, purge_pilot

    with pilot(10, state="live") as (conn, pilot_id, _, _):
        with pytest.raises(PilotError):
            with conn.transaction():
                purge_pilot(conn, pilot_id, uuid.uuid4())                       # still running: refused
        with conn.transaction():
            conn.execute("update pilots set state = 'completed' where id = %s", (pilot_id,))
            conn.execute("insert into pilot_events (pilot_id, type, payload, created_at) values (%s, 'state', %s, now())",
                         (pilot_id, '{"from": "live", "to": "completed"}'))
            purge_pilot(conn, pilot_id, uuid.uuid4())                           # allowed straight away after the end
        left = conn.execute("select count(*) from pilot_homeowners where pilot_id = %s and (name is not null or phone is not null)",
                            (pilot_id,)).fetchone()[0]
        assert left == 0
        # finding 8: the GHL sub-account is unlinked, so its webhooks stop being stored
        assert conn.execute("select ghl_location_id from pilots where id = %s", (pilot_id,)).fetchone()[0] is None
        from delivery.webhooks import handle_event
        assert handle_event(conn, {"type": "InboundMessage", "locationId": f"loc-{pilot_id}", "contactId": "c1",
                                   "body": "hi", "messageId": "after-purge"}) == "ignored: unknown location"


# ---------- second review (2026-10-11) ----------

def test_people_sharing_any_phone_or_email_are_one_person_even_through_a_chain():
    from delivery.contacts import group_people
    groups = group_people([
        ("a", "+447700900001", "a@x.com"),      # A: phone P + email E
        ("b", None, "a@x.com"),                 # B: email E only -> same person as A
        ("c", "+447700900001", None),           # C: phone P only -> same person
        ("d", "+447700900002", "a@x.com"),      # D: other phone, same email -> same person
        ("e", "+447700900009", None),           # someone else
        ("f", None, None),
    ])
    assert groups["a"] == groups["b"] == groups["c"] == groups["d"]
    assert groups["e"] == "+447700900009" and groups["f"] is None
    assert groups == group_people([("d", "+447700900002", "a@x.com"), ("c", "+447700900001", None), ("b", None, "a@x.com"),
                                   ("a", "+447700900001", "a@x.com"), ("e", "+447700900009", None), ("f", None, None)])


def test_homeowner_key_is_keyed_with_a_secret_not_a_plain_hash(monkeypatch, tmp_path):
    import hashlib

    from delivery import pilot as pilot_module
    record = {"phone": "07700 900123"}
    key = homeowner_key("acme", record)
    assert key != hashlib.sha256(b"acme:+447700900123").hexdigest()[:32]      # can't be reversed by trying every mobile
    monkeypatch.setenv("VELARQO_KEY_SECRET", "another-secret")
    assert homeowner_key("acme", record) != key
    # unset: one is generated once, saved to .env, and reused (stable keys across re-imports)
    monkeypatch.delenv("VELARQO_KEY_SECRET")
    env = tmp_path / ".env"
    env.write_text("OTHER=1\n", encoding="utf-8")
    monkeypatch.setattr(pilot_module, "ENV_PATH", env)
    first = homeowner_key("acme", record)
    saved = env.read_text(encoding="utf-8")
    assert "VELARQO_KEY_SECRET=" in saved and "OTHER=1" in saved
    monkeypatch.delenv("VELARQO_KEY_SECRET")                                     # new process: read back from .env
    assert homeowner_key("acme", record) == first
    assert env.read_text(encoding="utf-8") == saved                              # not regenerated


def _rows_for_person_tests():
    from tests.integration.pilot_fixtures import records
    return [
        {"Ref": "A", "Quote Date": "01/05/2026", "Status": "Lost", "Phone": "07700900901", "Email": "a@x.com",
         "Opted Out": "yes", "Name": "Ann A", "Postcode": "LS1 1AA"},
        {"Ref": "B", "Quote Date": "01/06/2026", "Status": "Lost", "Phone": None, "Email": "a@x.com",
         "Opted Out": None, "Name": "Ann A", "Postcode": "LS1 1AA"},
    ] + records(10)


@pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")
def test_finding1_opted_out_quote_excludes_the_same_persons_email_only_quote():
    from delivery.ghl_push import claim_wave
    from tests.integration.pilot_fixtures import pilot
    with pilot(rows=_rows_for_person_tests(), holdout=0.0) as (conn, pid, _, _):
        rows = dict(conn.execute("select source_record_id, (state, exclusion_reason, person_key) from pilot_homeowners "
                                 "where pilot_id = %s and source_record_id in ('A', 'B')", (pid,)).fetchall())
        assert rows["A"][2] == rows["B"][2]                                       # one person
        assert rows["B"][0] == "excluded" and rows["B"][1] == "opted out"
        assert claim_wave(conn, pid, "w1", 30) == 10
        assert conn.execute("select count(*) from pilot_homeowners where pilot_id = %s and source_record_id in ('A', 'B') "
                            "and wave_id is not null", (pid,)).fetchone()[0] == 0


@pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")
def test_finding1_claim_guard_blocks_person_wide_exclusions_and_claims_one_row_per_person():
    """Even if grouping were wrong, the claim itself refuses: a row sharing an
    email with an opted-out quote, and a second row of the same person."""
    from delivery.ghl_push import claim_wave
    from tests.integration.pilot_fixtures import pilot
    with pilot(rows=_rows_for_person_tests(), holdout=0.0) as (conn, pid, _, _):
        with conn.transaction():
            # B forced back to contactable with its own person_key: only the email links it to A
            conn.execute("update pilot_homeowners set state = 'treatment', arm = 'treatment', exclusion_reason = null, "
                         "person_key = 'b-alone' where pilot_id = %s and source_record_id = 'B'", (pid,))
            # Q0 and Q1 forced into one person (as if two quotes both stayed contactable)
            conn.execute("update pilot_homeowners set person_key = 'same-person' where pilot_id = %s "
                         "and source_record_id in ('Q0', 'Q1')", (pid,))
        assert claim_wave(conn, pid, "w1", 30) == 9                               # 10 people - B; Q0/Q1 count once
        claimed = {r for (r,) in conn.execute("select source_record_id from pilot_homeowners where pilot_id = %s "
                                              "and wave_id is not null", (pid,)).fetchall()}
        assert "B" not in claimed and len(claimed & {"Q0", "Q1"}) == 1
        assert claim_wave(conn, pid, "w2", 30) == 0                               # the other quote: person already claimed


@pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")
def test_finding1_installer_optout_reaches_every_quote_of_the_person():
    from delivery.pilot import opt_out_people
    from tests.integration.pilot_fixtures import pilot, records
    rows = records(5) + [{"Ref": "X1", "Quote Date": "01/05/2026", "Status": "Lost", "Phone": "07700900800",
                          "Email": "x@x.com", "Postcode": "LS1 1AA"},
                         {"Ref": "X2", "Quote Date": "01/04/2026", "Status": "Lost", "Phone": None,
                          "Email": "x@x.com", "Postcode": "LS1 1AA"}]
    with pilot(rows=rows, holdout=0.0) as (conn, pid, _, _):
        with conn.transaction():
            assert opt_out_people(conn, pid, {"+447700900800"}, uuid.uuid4(), "test") == 2   # by phone: both quotes
        assert {s for (s,) in conn.execute("select state from pilot_homeowners where pilot_id = %s "
                                           "and source_record_id in ('X1', 'X2')", (pid,)).fetchall()} == {"opted_out"}


def test_blank_source_is_excluded_only_when_the_export_has_a_source_column():
    base = {"quote_date": "01/05/2026", "quote_status": "Lost", "phone": "07700900123"}
    assert eligibility({**base, "lead_source": "  "}, [], set(), TODAY)[0] == "unknown source"
    assert eligibility({**base, "lead_source": "Website form"}, [], set(), TODAY)[0] is None
    assert eligibility(base, [], set(), TODAY)[0] is None          # no source column at all: confirmed on the intake form
