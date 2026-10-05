from datetime import date

import pytest

from integrations.places import client
from prospecting.enrichment.places_websites import clean_url, search_name


class FakeConn:
    """Just enough of psycopg for _claim_call: counts calls in memory."""

    def __init__(self, day=0, month=0):
        self.day, self.month = day, month

    def transaction(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if sql.startswith("insert"):
            self.day += 1
            self.month += 1
        return self

    def fetchone(self):
        return self.day, self.month


def test_claim_counts_calls_under_the_limits():
    conn = FakeConn(day=3, month=100)
    client._claim_call(conn, date(2026, 10, 5))
    assert (conn.day, conn.month) == (4, 101)


@pytest.mark.parametrize("day,month", [(client.DAILY_LIMIT, 0), (0, client.MONTHLY_LIMIT)])
def test_claim_refuses_past_the_free_allowance(day, month):
    conn = FakeConn(day=day, month=month)
    with pytest.raises(client.FreeAllowanceUsed):
        client._claim_call(conn, date(2026, 10, 5))
    assert (conn.day, conn.month) == (day, month)


def test_limits_stay_inside_googles_free_1000_a_month():
    assert client.MONTHLY_LIMIT < 1000 and client.DAILY_LIMIT * 31 < 1000


def test_search_name_and_clean_url():
    assert search_name("WORTLEY WINDOWS & DOORS LIMITED") == "WORTLEY WINDOWS & DOORS"
    assert search_name("Acme Glazing Ltd.") == "Acme Glazing"
    assert clean_url("https://www.quadrantwindows.co.uk/?utm_source=google&utm_medium=organic") == "https://www.quadrantwindows.co.uk/"


def test_postcodes_are_found_on_a_page():
    from prospecting.enrichment.places_sweep import _POSTCODE
    assert _POSTCODE.findall("UNIT 4 BARRAS ST, LEEDS LS12 4JS. ALSO M1 2AB") == ["LS12 4JS", "M1 2AB"]


def test_only_active_limited_companies_are_added_from_companies_house():
    from prospecting.enrichment.ch_add import lead_from_profile
    profile = {"company_status": "active", "type": "ltd", "company_name": "ACME WINDOWS LIMITED",
               "company_number": "01234567", "sic_codes": ["43342"], "date_of_creation": "2010-01-01",
               "accounts": {"last_accounts": {"type": "micro-entity"}},
               "registered_office_address": {"address_line_1": "1 High St", "locality": "Leeds", "postal_code": "LS1 1AA"}}
    lead = lead_from_profile(profile, "https://acme.co.uk", {"email": "info@acme.co.uk"}, "places_sweep")
    assert lead["company_category"] == "Private Limited Company"
    assert lead["accounts_category"] == "MICRO ENTITY"
    assert lead["email"] == "info@acme.co.uk" and lead["city"] == "Leeds"
    assert lead_from_profile({**profile, "company_status": "dissolved"}, "x", {}, "s") is None
    assert lead_from_profile({**profile, "type": "limited-partnership"}, "x", {}, "s") is None
