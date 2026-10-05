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
