from prospecting.deduplication.merge import match_name, merge_sources, tidy_display_name
from prospecting.sourcing.companies_house_bulk import match_reason


def _osm(name, **fields):
    return {"company_name": name, "lead_source": "osm_scrape", **fields}


def _ch(name, **fields):
    return {"company_name": name, "lead_source": "companies_house", **fields}


def test_name_normalisation():
    assert match_name("HALEWOOD WINDOWS LIMITED") == match_name("Halewood Windows") == "halewood windows"
    assert match_name("A&D Glass Ltd") == "a and d glass"
    assert tidy_display_name("SHEFFIELD UPVC WINDOWS LTD") == "Sheffield uPVC Windows"
    assert tidy_display_name("Empire Doors & Windows") == "Empire Doors & Windows"


def test_osm_and_companies_house_records_merge_with_each_sources_strengths():
    merged = merge_sources([
        _osm("Halewood Windows", website="https://halewoodwindows.com", phone="+441514000000", postcode="L25 9QA", city="Liverpool"),
        # registered office at an accountant elsewhere - name is unique on both sides
        _ch("HALEWOOD WINDOWS LIMITED", company_number="01234567", sic_codes="43342", postcode="WA1 1AA", city="Warrington"),
    ])

    assert len(merged) == 1
    lead = merged[0]
    assert lead["lead_source"] == "companies_house+osm"
    assert lead["merge_confidence"] == "name"
    assert lead["website"] == "https://halewoodwindows.com"
    assert lead["postcode"] == "L25 9QA"  # trading premises, not the accountant
    assert lead["registered_postcode"] == "WA1 1AA"
    assert lead["company_number"] == "01234567"
    assert lead["sic_codes"] == "43342"
    assert lead["display_name"] == "Halewood Windows"


def test_common_names_in_different_towns_are_not_merged():
    merged = merge_sources([
        _osm("Premier Windows", postcode="LS1 1AA"),
        _osm("Premier Windows", postcode="B1 1AA"),
        _ch("PREMIER WINDOWS LTD", postcode="M1 1AA"),
    ])
    assert len(merged) == 3


def test_same_name_same_district_merges_within_a_source():
    # OSM often has both a node and a building outline for one shop
    merged = merge_sources([
        _osm("Vogue Glass", osm_id="node/1", postcode="SK3 0UD"),
        _osm("Vogue Glass", osm_id="way/2", postcode="SK3 0UE", website="https://www.vogueglass.co.uk/"),
    ])
    assert len(merged) == 1
    assert merged[0]["website"] == "https://www.vogueglass.co.uk/"


def test_typo_level_name_variants_in_same_district_merge_but_different_names_dont():
    merged = merge_sources([
        _osm("Cityglass Window Systems", postcode="M1 2NP"),
        _ch("CITY GLASS WINDOW SYSTEMS LTD", postcode="M1 3AB"),
        _osm("Acme Windows & Doors", postcode="M1 4AA"),
        _ch("ACME WINDOWS LTD", postcode="M1 5AA"),
    ])
    assert len(merged) == 3


def test_companies_house_filter():
    base = {"CompanyStatus": "Active", "Accounts.AccountCategory": "MICRO ENTITY"}
    assert match_reason({**base, "CompanyName": "X LTD", "SICCode.SicText_1": "43342 - Glazing"}) == "sic:43342"
    assert match_reason({**base, "CompanyName": "BOB'S WINDOWS LTD", "SICCode.SicText_1": "43999 - Other"}) == "name"
    assert match_reason({**base, "CompanyName": "TOP DOORS LTD", "SICCode.SicText_1": "43390 - Other building completion"}) == "name+trade_sic"
    assert match_reason({**base, "CompanyName": "NEXT DOOR LETTINGS LTD", "SICCode.SicText_1": "68310 - Real estate agencies"}) is None
    assert match_reason({**base, "CompanyName": "OUTDOORS LTD", "SICCode.SicText_1": "43390 - Other"}) is None
    assert match_reason({**base, "CompanyStatus": "Dissolved", "CompanyName": "X WINDOWS LTD"}) is None
    assert match_reason({**base, "Accounts.AccountCategory": "DORMANT", "CompanyName": "X WINDOWS LTD"}) is None
