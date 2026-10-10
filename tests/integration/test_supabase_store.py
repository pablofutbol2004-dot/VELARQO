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


import os

import pytest


@pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")
def test_rebuild_keeps_verified_data_and_never_mixes_two_sites():
    """Real database, rolled back: a rebuild that guessed a different site
    must not attach that site's email or status, and a rebuild from fewer
    sources must not wipe phone/osm data."""
    import json
    import uuid

    import psycopg

    from data.supabase_store import connect, push_universe

    icp = json.load(open("config/templates/icp-template.json"))
    conn = connect()
    number = f"T{uuid.uuid4().hex[:7].upper()}"
    try:
        with conn.transaction():
            base = {"company_name": "TEST GLAZING LTD", "legal_name": "TEST GLAZING LTD", "company_number": number,
                    "website": "https://verified.example", "email": "info@verified.example", "phone": "+441130000000",
                    "osm_ids": ["node/1"], "sources": ["osm", "companies_house"], "tier": "A", "icp_score": 90,
                    "website_status": "ok", "website_title": "Verified Glazing"}
            push_universe(conn, [dict(base)], "windows", icp)
            rebuild = {"company_name": "TEST GLAZING LTD", "legal_name": "TEST GLAZING LTD", "company_number": number,
                       "website": "https://guessed.example", "email": "sales@guessed.example", "phone": None,
                       "sources": ["companies_house"], "tier": "C", "icp_score": 40,
                       "website_status": "unreachable", "website_title": "Guessed"}
            push_universe(conn, [rebuild], "windows", icp)
            row = conn.execute("select website, email, phone, osm_ids, sources, tier, website_status, website_title "
                               "from companies where company_number = %s", (number,)).fetchone()
            assert row[0] == "https://verified.example" and row[1] == "info@verified.example"
            assert row[2] == "+441130000000" and "node/1" in row[3] and {"osm", "companies_house"} <= set(row[4])
            assert row[5] == "A" and row[6] == "ok" and row[7] == "Verified Glazing"
            raise psycopg.Rollback()
    finally:
        conn.close()
