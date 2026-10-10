"""Wave sending against a fake GoHighLevel, committing for real on the local
database (each test deletes its pilot afterwards). Run with VELARQO_DB_TESTS=1."""

import threading

import pytest
import requests

from integrations.ghl.client import GHLAuthError, GHLTemporaryError
from tests.integration.pilot_fixtures import DB, autocommit, pilot, records

pytestmark = DB


class FakeGHL:
    def __init__(self, fail_once=(), bad=(), auth_fail=False, on_upsert=None, slow=0.0):
        self.contacts, self.tags, self.upserts, self.dnd, self.removed = {}, {}, 0, set(), {}
        self.fail_once, self.bad, self.auth_fail, self.on_upsert, self.slow = set(fail_once), set(bad), auth_fail, on_upsert, slow
        self.lock = threading.Lock()

    def upsert_contact(self, contact):
        import time
        with self.lock:
            self.upserts += 1
            n = self.upserts
        if self.slow:
            time.sleep(self.slow)
        if self.on_upsert:
            self.on_upsert(n)
        if self.auth_fail:
            raise GHLAuthError("HTTP 401")
        phone = contact["phone"]
        if phone in self.bad:
            response = requests.Response()
            response.status_code = 422
            raise requests.HTTPError("invalid phone", response=response)
        with self.lock:
            if phone in self.fail_once:
                self.fail_once.discard(phone)
                self.contacts.setdefault(phone, f"c-{phone}")    # GHL created it, then the reply timed out
                raise GHLTemporaryError("timeout")
            return {"contact": {"id": self.contacts.setdefault(phone, f"c-{phone}")}}

    def add_tags(self, contact_id, tags):
        with self.lock:
            self.tags.setdefault(contact_id, []).extend(tags)
        return {}

    def set_dnd(self, contact_id):
        self.dnd.add(contact_id)

    def remove_tags(self, contact_id, tags):
        self.removed[contact_id] = tags


def states(pilot_id):
    """Read from a SECOND connection: proves the work was committed."""
    other = autocommit()
    try:
        return dict(other.execute("select state, count(*) from pilot_homeowners where pilot_id = %s group by 1", (pilot_id,)).fetchall())
    finally:
        other.close()


def test_wave_is_committed_enrols_treatment_only_and_claiming_is_idempotent():
    from delivery.ghl_push import claim_wave, send_wave
    with pilot(20) as (conn, pilot_id, _, _):                 # 16 treatment, 4 holdout
        assert claim_wave(conn, pilot_id, "w1", 5) == 5
        assert claim_wave(conn, pilot_id, "w1", 5) == 0
        ghl = FakeGHL()
        assert send_wave(conn, ghl, pilot_id, "w1")["enrolled"] == 5
        assert all(tags == ["vq-w1"] for tags in ghl.tags.values()) and len(ghl.tags) == 5
        assert states(pilot_id) == {"enrolled": 5, "treatment": 11, "holdout": 4}
        assert send_wave(conn, ghl, pilot_id, "w1")["enrolled"] == 0


def test_cli_send_wave_commits(monkeypatch):
    """The original bug: the CLI ran inside an uncommitted transaction."""
    from click.testing import CliRunner

    from delivery import pilot as pilot_module
    with pilot(20) as (conn, pilot_id, location, _):
        ghl = FakeGHL()
        monkeypatch.setattr(pilot_module, "ghl_client_for", lambda c, p: (ghl, None))
        result = CliRunner().invoke(pilot_module.cli, ["send-wave", pilot_id, "w1", "--size", "4"])
        assert result.exit_code == 0, result.output
        assert states(pilot_id).get("enrolled") == 4


def test_timeout_after_ghl_created_the_contact_recovers_without_duplicates():
    from delivery.ghl_push import claim_wave, send_wave
    with pilot(20) as (conn, pilot_id, _, _):
        claim_wave(conn, pilot_id, "w1", 3)
        phones = [p for (p,) in conn.execute("select phone from pilot_homeowners where pilot_id = %s and wave_id = 'w1'", (pilot_id,))]
        ghl = FakeGHL(fail_once={phones[0]})
        first = send_wave(conn, ghl, pilot_id, "w1")
        assert first["enrolled"] == 2 and first["left_for_retry"] == 1
        assert states(pilot_id)["pushing"] == 1
        assert send_wave(conn, ghl, pilot_id, "w1")["enrolled"] == 1
        assert len(ghl.contacts) == 3 and all(len(t) == 1 for t in ghl.tags.values())


def test_two_runs_at_once_never_double_send():
    from delivery.ghl_push import claim_wave, send_wave
    with pilot(20) as (conn, pilot_id, _, _):
        claim_wave(conn, pilot_id, "w1", 6)
        ghl = FakeGHL(slow=0.2)
        second_conn = autocommit()
        results = []
        t = threading.Thread(target=lambda: results.append(send_wave(second_conn, ghl, pilot_id, "w1")))
        t.start()
        import time
        time.sleep(0.1)
        results.append(send_wave(conn, ghl, pilot_id, "w1"))
        t.join()
        second_conn.close()
        assert sorted(r["enrolled"] for r in results) == [0, 6]
        assert any(r.get("reason") == "another run is sending" for r in results)
        assert all(len(t) == 1 for t in ghl.tags.values()) and len(ghl.tags) == 6


def test_bad_data_is_push_failed_but_an_expired_token_touches_nobody():
    from delivery.ghl_push import claim_wave, send_wave
    with pilot(20) as (conn, pilot_id, _, _):
        claim_wave(conn, pilot_id, "w1", 3)
        assert send_wave(conn, FakeGHL(auth_fail=True), pilot_id, "w1")["stopped"]
        assert states(pilot_id).get("push_failed") is None                   # token problem: rows not blamed
        phone = conn.execute("select phone from pilot_homeowners where pilot_id = %s and wave_id = 'w1' limit 1", (pilot_id,)).fetchone()[0]
        result = send_wave(conn, FakeGHL(bad={phone}), pilot_id, "w1")
        assert result["enrolled"] == 2 and result["push_failed"] == 1
        assert "422" in conn.execute("select push_error from pilot_homeowners where pilot_id = %s and phone = %s",
                                     (pilot_id, phone)).fetchone()[0]


def test_pausing_mid_wave_stops_further_sends():
    from delivery.ghl_push import claim_wave, send_wave
    with pilot(20) as (conn, pilot_id, _, _):
        claim_wave(conn, pilot_id, "w1", 5)
        other = autocommit()

        def pause_after_two(n):
            if n == 2:
                other.execute("update pilots set state = 'paused' where id = %s", (pilot_id,))

        ghl = FakeGHL(on_upsert=pause_after_two)
        result = send_wave(conn, ghl, pilot_id, "w1")
        other.close()
        # the pause landed while GHL was upserting #2: its tag (= texts) is not added
        assert result["stopped"] and result["enrolled"] == 1 and result["skipped"] == 1 and len(ghl.tags) == 1
        assert states(pilot_id)["queued"] == 3 and states(pilot_id)["pushing"] == 1
        why = conn.execute("select payload->>'why' from pilot_events where pilot_id = %s and type = 'tag_skipped'",
                           (pilot_id,)).fetchone()[0]
        assert "paused" in why


def test_opt_out_after_queueing_is_never_sent():
    from delivery.ghl_push import claim_wave, send_wave
    with pilot(20) as (conn, pilot_id, _, _):
        claim_wave(conn, pilot_id, "w1", 3)
        conn.execute("update pilot_homeowners set state = 'opted_out' where pilot_id = %s and homeowner_key = "
                     "(select homeowner_key from pilot_homeowners where pilot_id = %s and wave_id = 'w1' limit 1)", (pilot_id, pilot_id))
        ghl = FakeGHL()
        assert send_wave(conn, ghl, pilot_id, "w1")["enrolled"] == 2 and ghl.upserts == 2


def test_waves_refuse_unless_sending_and_canary_is_capped():
    from delivery.ghl_push import WaveError, claim_wave
    with pilot(60) as (conn, pilot_id, _, _):
        with pytest.raises(WaveError):
            claim_wave(conn, pilot_id, "w1", 31)                     # canary max 30
        conn.execute("update pilots set state = 'paused' where id = %s", (pilot_id,))
        with pytest.raises(WaveError):
            claim_wave(conn, pilot_id, "w1", 5)


def test_same_person_with_two_quotes_is_one_person():
    from delivery.ghl_push import claim_wave
    rows = records(10)
    rows.append({**rows[0], "Ref": "Q-older", "Quote Date": "01/02/2026"})          # same phone, older quote
    rows.append({**rows[1], "Ref": "Q-sold", "Status": "Sold"})                     # same person bought once
    with pilot(rows=rows, holdout=0.0) as (conn, pilot_id, _, _):
        by_reason = dict(conn.execute("select exclusion_reason, count(*) from pilot_homeowners where pilot_id = %s "
                                      "and state = 'excluded' group by 1", (pilot_id,)).fetchall())
        assert by_reason == {"another quote for the same person": 1, "already won/booked": 2}   # Ann1 excluded on both quotes
        assert claim_wave(conn, pilot_id, "w1", 30) == 9                                       # 12 rows, 9 people contactable


def test_opt_outs_are_pushed_to_ghl_once():
    from delivery.ghl_push import push_opt_outs
    from delivery.pilot import opt_out_people
    import uuid
    with pilot(20, wave_size=5) as (conn, pilot_id, _, contacts):
        phone = conn.execute("select phone from pilot_homeowners where ghl_contact_id = %s", (contacts[0],)).fetchone()[0]
        with conn.transaction():
            assert opt_out_people(conn, pilot_id, {phone}, uuid.uuid4(), "test") == 1
        ghl = FakeGHL()
        assert push_opt_outs(conn, ghl, pilot_id) == {"confirmed": 1, "failed": 0}
        assert ghl.dnd == {contacts[0]} and ghl.removed[contacts[0]] == [f"vq-w1"]
        assert push_opt_outs(conn, ghl, pilot_id) == {"confirmed": 0, "failed": 0}           # done once


# ---------- second review (2026-10-11) ----------

def test_finding2_two_quotes_sharing_an_email_are_never_claimed_together():
    from delivery.ghl_push import claim_wave
    rows = [
        {"Ref": "A", "Quote Date": "01/05/2026", "Status": "Lost", "Phone": "07700900001", "Email": "fam@x.com", "Postcode": "LS1 1AA"},
        {"Ref": "B", "Quote Date": "01/06/2026", "Status": "Lost", "Phone": None, "Email": "fam@x.com", "Postcode": "LS1 1AA"},
    ]
    with pilot(rows=rows, holdout=0.0) as (conn, pilot_id, _, _):
        assert claim_wave(conn, pilot_id, "w1", 30) == 1
        assert claim_wave(conn, pilot_id, "w2", 30) == 0


def test_finding5_opt_out_while_ghl_upserts_never_gets_the_wave_tag():
    import uuid

    from delivery.ghl_push import claim_wave, push_opt_outs, send_wave
    from delivery.pilot import opt_out_people
    with pilot(20) as (conn, pilot_id, _, _):
        claim_wave(conn, pilot_id, "w1", 3)
        phones = [p for (p,) in conn.execute("select phone from pilot_homeowners where pilot_id = %s and wave_id = 'w1' "
                                             "order by homeowner_key", (pilot_id,))]
        other = autocommit()

        def opt_out_first(n):              # the STOP lands while GHL is creating contact #1
            if n == 1:
                with other.transaction():
                    opt_out_people(other, pilot_id, {phones[0]}, uuid.uuid4(), "installer")

        ghl = FakeGHL(on_upsert=opt_out_first)
        result = send_wave(conn, ghl, pilot_id, "w1")
        other.close()
        assert result["enrolled"] == 2 and result["skipped"] == 1 and not result["stopped"]
        assert f"c-{phones[0]}" not in ghl.tags                                     # never enrolled = never texted
        assert conn.execute("select payload->>'why' from pilot_events where pilot_id = %s and type = 'tag_skipped'",
                            (pilot_id,)).fetchone()[0] == "homeowner is now 'opted_out'"
        # the contact id was kept, so GHL still gets the do-not-disturb
        assert push_opt_outs(conn, ghl, pilot_id)["confirmed"] == 1 and ghl.dnd == {f"c-{phones[0]}"}


def test_canary_claims_at_most_30_people_across_all_waves():
    from delivery.ghl_push import claim_wave
    with pilot(60, holdout=0.0) as (conn, pilot_id, _, _):
        assert claim_wave(conn, pilot_id, "w1", 20) == 20
        assert claim_wave(conn, pilot_id, "w2", 20) == 10
        assert claim_wave(conn, pilot_id, "w3", 5) == 0
        conn.execute("update pilots set state = 'live' where id = %s", (pilot_id,))
        assert claim_wave(conn, pilot_id, "w4", 20) == 20                           # live: no canary cap


def test_finding6_opt_outs_are_pushed_for_a_completed_pilot_and_check_keeps_going(monkeypatch):
    import uuid

    from click.testing import CliRunner

    from delivery import monitor
    from delivery import pilot as pilot_module
    from delivery.pilot import opt_out_people, pilots_with_pending_dnd, run_checks
    with pilot(20, wave_size=5) as (conn, pilot_id, _, contacts):
        phone = conn.execute("select phone from pilot_homeowners where pilot_id = %s and ghl_contact_id = %s",
                             (pilot_id, contacts[0])).fetchone()[0]
        with conn.transaction():
            opt_out_people(conn, pilot_id, {phone}, uuid.uuid4(), "after the pilot ended")
        conn.execute("update pilots set state = 'completed' where id = %s", (pilot_id,))
        assert pilot_id in pilots_with_pending_dnd(conn)
        ghl = FakeGHL()
        monkeypatch.setattr(pilot_module, "ghl_client_for", lambda c, p: (ghl, None))
        result = CliRunner().invoke(pilot_module.cli, ["check", "--pilot", pilot_id])
        assert result.exit_code == 0, result.output
        assert ghl.dnd == {contacts[0]} and pilot_id not in pilots_with_pending_dnd(conn)

        # one pilot failing doesn't skip the stop checks of the others; still a non-zero exit
        checked = []

        def fake_check(c, pid):
            checked.append(pid)
            if pid == "boom":
                raise RuntimeError("database hiccup")
            return []

        monkeypatch.setattr(monitor, "check_pilot", fake_check)
        lines = []
        paused, failed = run_checks(conn, ["boom", pilot_id], lines.append)
        assert checked == ["boom", pilot_id] and failed and not paused
        assert any(line.startswith("ok " + pilot_id) for line in lines)
