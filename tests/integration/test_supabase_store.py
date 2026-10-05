"""Pure-function tests for the Supabase loader (no database needed)."""

from datetime import date

from data.supabase_store import company_row, icp_version, source_key
from prospecting.deduplication.merge import merge_sources


def test_source_key_prefers_company_number_then_osm_then_name():
    assert source_key({"company_number": "01234567", "osm_ids": ["node/1"]}) == "ch:01234567"
    assert source_key({"osm_ids": ["way/9", "node/3"]}) == "osm:node/3"
    assert source_key({"company_name": "Halewood Windows Ltd", "postcode": "L25 9QA"}) == "name:halewood windows|L25"


def test_icp_version_changes_only_when_config_changes():
    assert icp_version({"a": 1, "b": 2}) == icp_version({"b": 2, "a": 1})
    assert icp_version({"a": 1}) != icp_version({"a": 2})


def test_company_row_maps_merged_lead_and_keeps_raw_out_of_the_main_row():
    lead = merge_sources([
        {"company_name": "Halewood Windows", "lead_source": "osm_scrape", "osm_id": "node/5",
         "osm_tags": {"name": "Halewood Windows", "opening_hours": "Mo-Fr 09:00-17:00"}, "lat": "53.3", "lon": "-2.8"},
        {"company_name": "HALEWOOD WINDOWS LIMITED", "lead_source": "companies_house", "company_number": "01234567",
         "sic_codes": "43342 43320", "incorporation_date": "11/09/2012", "ch_raw": {"CompanyName": "HALEWOOD WINDOWS LIMITED"}},
    ])[0]

    row = company_row(lead, "windows", "v1")

    assert row["source_key"] == "ch:01234567"
    assert row["osm_ids"] == ["node/5"]
    assert row["sources"] == ["companies_house", "osm"]
    assert row["sic_codes"] == ["43342", "43320"]
    assert row["incorporation_date"] == date(2012, 9, 11)
    assert row["lat"] == 53.3
    assert "osm_tags" not in lead and "ch_raw" not in lead

    raw = {r["source"]: r for r in lead["raw_sources"]}
    assert raw["osm"]["payload"]["opening_hours"] == "Mo-Fr 09:00-17:00"
    assert raw["companies_house"]["source_id"] == "01234567"


def test_rebuild_keeps_verified_website_email_tier_and_extra():
    from data.supabase_store import _update_expr
    assert _update_expr("email") == "coalesce(email, %(email)s)"
    assert _update_expr("website") == "coalesce(website, %(website)s)"
    assert "tier in ('A', 'B') then tier" in _update_expr("tier")
    assert _update_expr("extra") == "extra || %(extra)s::jsonb"
    assert _update_expr("city") == "%(city)s"
