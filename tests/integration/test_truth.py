from datetime import date, timedelta

import yaml

from lib import truth

OFFER_STATUSES = {"live", "test", "retired", truth.TODO}
NICHE_STATUSES = {"live", "test", "paused", "retired", truth.TODO}


def _all_files():
    return sorted(truth.TRUTH.rglob("*.yaml"))


def test_every_truth_file_parses_and_declares_its_side():
    for path in _all_files():
        data = yaml.safe_load(path.read_text())
        if path.parent.name == "compliance" and path.parent.parent == truth.TRUTH:
            assert "rules" in data, path
            continue
        expected = "velarqo" if "velarqo" in path.parts else "client"
        assert data.get("side") == expected, f"{path} must declare side: {expected}"


def test_niches_point_at_real_icps_and_live_offers():
    offers = {o["id"]: o for o in truth.velarqo()["offers"]["offers"]}
    for n in truth.velarqo()["niches"]["niches"]:
        assert (truth.ROOT / n["icp_template"]).is_file(), n["id"]
        assert n["status"] in NICHE_STATUSES, n["id"]
        assert n["offer"] in offers, f"{n['id']} uses unknown offer {n['offer']}"
        assert offers[n["offer"]]["status"] != "retired", f"{n['id']} uses a retired offer"


def test_icp_offer_lines_match_the_approved_pitch():
    # Copy drift: change the offer in truth/velarqo/offers.yaml and this tells
    # you which ICP templates still say the old thing.
    for n in truth.velarqo()["niches"]["niches"]:
        assert truth.niche_icp(n["id"])["offer_line"] == truth.niche_pitch(n["id"]), n["id"]


def test_offer_statuses_are_known():
    for o in truth.velarqo()["offers"]["offers"]:
        assert o["status"] in OFFER_STATUSES, o["id"]


def test_compliance_references_real_rules_for_the_right_side():
    laws = truth.laws()
    for rule in laws.values():
        assert rule["source"].startswith("https://"), rule["id"]
        assert set(rule["sides"]) <= {"velarqo", "client"}, rule["id"]

    sides = {"velarqo": truth.velarqo()["compliance"]}
    sides.update({cid: truth.client(cid)["compliance"] for cid in ["_template", *truth.client_ids()]})
    for name, compliance in sides.items():
        side = "velarqo" if name == "velarqo" else "client"
        for rule_id in compliance["applies"]:
            assert rule_id in laws, f"{name} cites unknown rule {rule_id}"
            assert side in laws[rule_id]["sides"], f"{rule_id} doesn't apply to side {side}"


def test_rule_ids_are_unique_across_jurisdictions():
    ids = [r["id"] for p in sorted((truth.TRUTH / "compliance").glob("*.yaml")) for r in yaml.safe_load(p.read_text())["rules"]]
    assert len(ids) == len(set(ids))


def test_cold_email_decision_is_explicit_and_traceable():
    c = truth.velarqo()["compliance"]
    assert c["cold_email_status"] in ("allowed", "blocked_pending_legal_advice")
    if c["cold_email_status"] == "allowed":
        # Any law we knowingly don't follow must be a real rule, with who decided and when.
        for risk in c.get("accepted_risks", []):
            assert risk["rule"] in truth.laws() and risk["decided"] and risk["by"]
    else:
        assert c["cold_email_blocker"] in truth.laws()


def test_suppression_lists_are_never_shared_between_sides():
    assert truth.velarqo()["compliance"]["requirements"]["opt_out"]["list"] == "velarqo"
    for cid in ["_template", *truth.client_ids()]:
        assert truth.client(cid)["compliance"]["opt_out"]["list"] == "client", cid


def test_client_offers_only_target_that_clients_segments():
    for cid in ["_template", *truth.client_ids()]:
        c = truth.client(cid)
        segment_ids = {s["id"] for s in c["segments"]["segments"]}
        for o in c["offers"]["offers"]:
            assert set(o["segments"]) <= segment_ids, f"{cid}:{o['id']}"


def test_signed_clients_have_no_todos_and_a_dpa():
    # _template is allowed TODOs; a real client folder is not.
    for cid in truth.client_ids():
        c = truth.client(cid)
        assert truth.todos(c) == [], f"client {cid} still has TODOs: {truth.todos(c)}"
        assert c["client"]["agreements"]["dpa_signed"], cid


def test_checked_laws_are_not_stale():
    cutoff = date.today() - timedelta(days=183)
    for rule in truth.laws().values():
        checked = rule["last_checked"]
        if checked != truth.TODO:
            assert date.fromisoformat(str(checked)) >= cutoff, f"{rule['id']} last checked {checked}; re-verify"


def test_todos_finds_nested_placeholders():
    assert truth.todos({"a": "TODO", "b": [{"c": "x"}, {"d": "TODO"}]}) == ["a", "b[1].d"]
