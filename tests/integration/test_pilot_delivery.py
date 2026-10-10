import os
import uuid
from datetime import date

import psycopg
import pytest

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
    assert eligibility({**base, "phone": None}, ["LS"], set(), TODAY)[0] == "no phone or email"
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
            assert again["new"] == 0 and again["already_imported"] == 41          # re-import changes nothing

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
