import csv
import io
import zipfile
from datetime import date

from data.supabase_store import company_row
from lib.normalization.normalize import normalize_lead, normalize_postcode
from prospecting.enrichment.domain_finder import COUNTRY_TLDS, DomainFinder, candidate_domains
from prospecting.sourcing.cro_bulk import iter_companies, match_reason, parse_town_county, row_to_lead

HEADER = ["company_num", "company_name", "company_status_code", "company_status", "company_type_code", "company_type",
          "company_reg_date", "last_ar_date", "company_address_1", "company_address_2", "company_address_3",
          "company_address_4", "comp_dissolved_date", "nard", "last_accounts_date", "company_status_date",
          "nace_v2_code", "eircode", "company_name_eff_date", "company_type_eff_date", "princ_object_code"]


def _row(name, nace="", status="Normal ", company_type="LTD - Private Company Limited by Shares", address4="TRALEE, KERRY, Ireland",
         eircode="V92 ER04", number="612345"):
    return {
        "company_num": number, "company_name": name, "company_status": status, "company_type": company_type,
        "company_reg_date": "2015-03-02", "company_address_1": "UNIT 4", "company_address_2": "MONAVALLEY IND EST",
        "company_address_3": "", "company_address_4": address4, "nace_v2_code": nace, "eircode": eircode,
    }


def test_only_live_companies_of_corporate_types_count():
    assert match_reason(_row("CASTLE ROOFING LIMITED"), "roofing") == "name"
    assert match_reason(_row("CASTLE ROOFING LIMITED", status="Dissolved"), "roofing") is None
    assert match_reason(_row("CASTLE ROOFING LIMITED", status="Strike Off Listed"), "roofing") is None
    assert match_reason(_row("CASTLE ROOFING CLG", company_type="CLG - Company Limited by Guarantee"), "roofing") is None
    assert match_reason(_row("CASTLE ROOFING LIMITED", company_type="External company"), "roofing") is None


def test_nace_alone_name_alone_and_name_vetoed_by_other_sector():
    # specific activity code alone
    assert match_reason(_row("DARCO LIMITED", nace="4391.0"), "roofing") == "nace:4391"
    assert match_reason(_row("FORMA LIMITED", nace="3102.0"), "kitchens") == "nace:3102"
    assert match_reason(_row("DOLETA LIMITED", nace="4332.0"), "windows") == "nace:4332"
    # name + no NACE (a third of the register) or a construction NACE
    assert match_reason(_row("SEAN DOYLE WINDOWS LIMITED"), "windows") == "name"
    assert match_reason(_row("PRO-FIT KITCHENS LIMITED", nace="4332.0"), "kitchens") == "name+nace"
    # painting AND glazing share NACE 4334: the name has to say glazing
    assert match_reason(_row("BRENNAN GLAZING SERVICES LIMITED", nace="4334.0"), "windows") == "name+nace:4334"
    assert match_reason(_row("BRENNAN PAINTERS LIMITED", nace="4334.0"), "windows") is None
    # takeaways and gyms with "kitchen" in the name are vetoed by their NACE
    assert match_reason(_row("JOHN'S KITCHEN CHINESE TAKEAWAY LIMITED", nace="5610.0"), "kitchens") is None
    assert match_reason(_row("FITNESS KITCHEN LIMITED", nace="9319.0"), "kitchens") is None
    # "door" alone is too vague without a trade NACE
    assert match_reason(_row("NEXT DOOR LETTINGS LIMITED"), "windows") is None
    assert match_reason(_row("MUNSTER ROLLER DOOR LIMITED", nace="4120.0"), "windows") == "door+nace"


def test_row_to_lead_maps_cro_fields_to_the_store_shape():
    lead = row_to_lead(_row("DOLETA WINDOWS & DOORS LIMITED", nace="4332.0"))
    assert lead["company_number"] == "612345"
    assert lead["country"] == "IE"
    assert lead["lead_source"] == "cro"
    assert lead["sic_codes"] == "43320" and lead["nace_code"] == "4332"
    assert lead["industry"] == "Joinery installation"
    assert lead["city"] == "Tralee" and lead["county"] == "Kerry"
    assert lead["postcode"] == "V92 ER04"
    assert lead["address"] == "UNIT 4, MONAVALLEY IND EST"
    assert lead["incorporation_date"] == "02/03/2015"
    assert lead["accounts_category"] is None
    assert lead["company_category"] == "LTD - Private Company Limited by Shares"
    assert lead["cro_raw"]["company_name"] == "DOLETA WINDOWS & DOORS LIMITED"

    # glazing shares NACE 4334 with painting; the UK SIC equivalent is glazing
    assert row_to_lead(_row("X GLAZING LIMITED", nace="4334.0"))["sic_codes"] == "43342"
    assert row_to_lead(_row("X LIMITED"))["sic_codes"] == "" and row_to_lead(_row("X LIMITED"))["nace_code"] is None


def test_town_and_county_parsing():
    assert parse_town_county({"company_address_4": "Bettystown,MEATH"}) == ("Bettystown", "Meath")
    assert parse_town_county({"company_address_4": ",Dublin 22"}) == ("Dublin 22", None)
    assert parse_town_county({"company_address_4": "CO. MEATH., MEATH, IRELAND"}) == ("Co. Meath.", "Meath")
    assert parse_town_county({"company_address_4": "", "company_address_3": "BLACKROCK CO. DUBLIN"}) == ("Blackrock Co. Dublin", None)
    assert parse_town_county({"company_address_4": "Ireland"}) == (None, None)


def test_eircode_survives_normalisation_and_uk_postcodes_are_unchanged():
    assert normalize_postcode("a92d720") == "A92 D720"
    assert normalize_postcode("D6W XY12") == "D6W XY12"
    assert normalize_postcode("l25 9qa") == "L25 9QA"
    assert normalize_lead(row_to_lead(_row("X WINDOWS LIMITED", eircode="V92ER04")))["postcode"] == "V92 ER04"


def test_company_row_carries_country_and_iso_dates():
    lead = normalize_lead(row_to_lead(_row("DOLETA WINDOWS & DOORS LIMITED", nace="4332.0")))
    row = company_row(lead, "windows", "v1", country="IE")
    assert row["country"] == "IE"
    assert row["source_key"] == "ch:612345"
    assert row["incorporation_date"] == date(2015, 3, 2)
    assert row["sic_codes"] == ["43320"]
    assert row["postcode"] == "V92 ER04"
    assert company_row(lead, "windows", "v1")["country"] == "UK"


def test_iter_companies_reads_the_zip_and_strips_header_spaces(tmp_path):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=HEADER, extrasaction="ignore")
    writer.writeheader()
    writer.writerow(_row("CASTLE ROOFING LIMITED", nace="4391.0"))
    writer.writerow(_row("YPSILON PUBLISHING LIMITED", nace="5819.0", status="Strike Off Listed"))
    writer.writerow(_row("KINSELLA ROOFING LIMITED", number="700001"))
    zip_path = tmp_path / "companies.csv.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("companies.csv", buffer.getvalue().replace("company_num,", " company_num,", 1))

    found = list(iter_companies(zip_path, "roofing"))

    assert [(lead["company_name"], reason) for lead, reason in found] == [
        ("CASTLE ROOFING LIMITED", "nace:4391"), ("KINSELLA ROOFING LIMITED", "name"),
    ]


def test_domain_finder_uses_irish_tlds_for_ireland():
    assert candidate_domains("HENNELLY & SON GLAZING LIMITED", COUNTRY_TLDS["IE"])[:2] == [
        "hennellyandsonglazing.ie", "hennellyandsonglazing.com",
    ]
    assert "hennellysonglazing.ie" in candidate_domains("HENNELLY & SON GLAZING LIMITED", COUNTRY_TLDS["IE"])
    assert not any(d.endswith(".co.uk") for d in candidate_domains("HENNELLY & SON GLAZING LIMITED", COUNTRY_TLDS["IE"]))
    assert candidate_domains("HALEWOOD WINDOWS LIMITED")[0] == "halewoodwindows.co.uk"

    class Provider:
        def enrich(self, lead):
            return {"website_status": "ok", "website_title": "Hennelly & Son Glazing, Headford, Galway"}

    tried = []
    finder = DomainFinder("test", ["glazing"], resolve=lambda d: tried.append(d) or d.endswith(".ie"),
                          provider=Provider(), tlds=COUNTRY_TLDS["IE"])
    found = finder.find({"company_name": "HENNELLY & SON GLAZING LIMITED", "city": "Headford"})
    assert found["website"] == "https://hennellyandsonglazing.ie"
    assert all(d.endswith((".ie", ".com")) for d in tried)


def test_dot_com_guess_needs_irish_evidence_but_dot_ie_does_not():
    from prospecting.enrichment.domain_finder import COUNTRY_MARKERS, COUNTRY_STRICT_TLDS

    class Provider:
        def __init__(self, text):
            self.text = text

        def enrich(self, lead):
            return {"website_status": "ok", "website_title": "Atlas Roofing", "website_text": self.text}

    lead = {"company_name": "ATLAS ROOFING LIMITED", "city": "Tralee", "county": "Kerry"}

    def find(text, tlds=("ie", "com"), resolves=lambda d: d.endswith(".com")):
        finder = DomainFinder("test", ["roofing"], resolve=resolves, provider=Provider(text), tlds=tlds,
                              strict_tlds=COUNTRY_STRICT_TLDS["IE"], local_markers=COUNTRY_MARKERS["IE"])
        return finder.find(lead).get("website")

    assert find("Atlas Roofing shingles and underlayments, Florida") is None
    assert find("Atlas Roofing, roofers across Ireland") == "https://atlasroofing.com"
    assert find("Atlas Roofing, based in Tralee") == "https://atlasroofing.com"
    assert find("Atlas Roofing. Call +353 66 123 4567") == "https://atlasroofing.com"
    # .ie is Irish by definition, no extra evidence needed
    assert find("Atlas Roofing shingles", resolves=lambda d: d.endswith(".ie")) == "https://atlasroofing.ie"
