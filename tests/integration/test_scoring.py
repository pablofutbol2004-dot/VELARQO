"""Cases taken from the real OSM leads sourced across 9 UK cities, where
the old substring scorer got it wrong."""

from pathlib import Path

from lib.scoring.icp_score import evaluate_lead
from lib.scoring.matching import find_terms, find_terms_in_domain
from pipelines.cold_outreach.pipeline import load_icp

ICP = load_icp(Path(__file__).parents[2] / "config" / "templates" / "icp-template.json")


def _lead(name, **fields):
    return {"display_name": name, "company_name": name, **fields}


def test_matching_handles_inflections_but_not_unrelated_prefixes():
    assert find_terms("Cardiff Glazing", ["glazing"]) == ["glazing"]
    assert find_terms("Halewood Windows", ["window"]) == ["window"]
    assert find_terms("Hawkes Garage Doors", ["garage door"]) == ["garage door"]
    assert find_terms("Cardiff Glazing", ["car"]) == []


def test_domain_matching_handles_run_together_words():
    assert find_terms_in_domain("repairmywindowsanddoors.co.uk", ["window"]) == ["window"]


def test_glazier_now_counts_as_in_vertical():
    # Old scorer: 0 - "glazing" wasn't one of its 5 literal keywords.
    result = evaluate_lead(_lead("Cardiff Glazing", email="info@cardiffglazing.co.uk", postcode="CF11 9AH"), ICP)
    assert result["vertical_fit"] >= 0.9
    assert result["qualified"]


def test_off_target_businesses_rejected_even_when_name_says_window():
    for name in ["Window Films 2000", "Westwood Security Shutters", "Hawkes Garage Doors", "Trade Window Supplies"]:
        result = evaluate_lead(_lead(name, email="x@example.co.uk"), ICP)
        assert result["tier"] == "reject", name


def test_generic_listing_names_rejected():
    assert evaluate_lead(_lead("Blinds", email="x@example.co.uk"), ICP)["tier"] == "reject"


def test_national_chains_penalised():
    local = evaluate_lead(_lead("Halewood Windows", email="info@halewoodwindows.com"), ICP)
    chain = evaluate_lead(_lead("Anglian Windows", email="info@anglian.co.uk"), ICP)
    osm_branded = evaluate_lead(_lead("Some Windows", brand="Some Windows", email="info@x.co.uk"), ICP)
    assert chain["vertical_fit"] < local["vertical_fit"]
    assert osm_branded["vertical_fit"] < local["vertical_fit"]


def test_perfect_fit_without_email_is_tier_c_not_qualified():
    result = evaluate_lead(_lead("Halewood Windows", website="https://www.halewoodwindows.com/"), ICP)
    assert result["tier"] == "C"
    assert not result["qualified"]
    assert any("needs email" in r for r in result["reasons"])


def test_osm_category_is_evidence_even_when_name_is_not():
    result = evaluate_lead(_lead("Benchmark Ltd", osm_category="craft=window_construction", email="info@benchmark.co.uk"), ICP)
    assert result["vertical_fit"] >= 0.9


def test_website_content_is_evidence():
    without_site = evaluate_lead(_lead("Pope and Parr", email="info@popeandparr.co.uk"), ICP)
    with_site = evaluate_lead(_lead(
        "Pope and Parr",
        email="info@popeandparr.co.uk",
        website_status="ok",
        website_text="Family run uPVC windows and doors installers. Double glazing, sash windows, FENSA registered.",
    ), ICP)
    assert without_site["tier"] == "reject"
    assert with_site["qualified"]


def test_every_score_is_explained():
    result = evaluate_lead(_lead("Premier Doors", osm_category="shop=doors", phone="+441142000000"), ICP)
    assert result["reasons"]
    assert set(result["breakdown"]) >= {"vertical_fit", "contactability", "data_quality"}
