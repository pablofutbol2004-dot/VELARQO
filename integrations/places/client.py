"""Google Places API (New) text search, locked to the free allowance.

The website field puts every call in Google's "Text Search Enterprise" SKU:
1,000 free calls per month, then paid. Pablo's rule: never pay. Two locks:
- Google Cloud quota: SearchTextRequest capped at 32/day (set in the console).
- This client: refuses once DAILY_LIMIT or MONTHLY_LIMIT calls are counted in
  the api_usage table, before the request is sent.

Google's terms allow storing the place ID only. Names, addresses and websites
returned here are used to find and verify the company's own site, not stored
as Google data.
"""

from datetime import date

import requests

API = "places_text_search_enterprise"
URL = "https://places.googleapis.com/v1/places:searchText"
FIELDS = "places.id,places.displayName,places.formattedAddress,places.websiteUri"
DAILY_LIMIT = 32
MONTHLY_LIMIT = 950


class FreeAllowanceUsed(Exception):
    pass


def usage(conn, today: date | None = None) -> tuple[int, int]:
    today = today or date.today()
    day, month = conn.execute(
        "select coalesce(sum(calls) filter (where day = %s), 0), coalesce(sum(calls), 0) "
        "from api_usage where api = %s and day >= date_trunc('month', %s::date)",
        (today, API, today),
    ).fetchone()
    return int(day), int(month)


def _claim_call(conn, today: date) -> None:
    """Counts the call before sending it, in one transaction, so a crash can
    only over-count (safe), never under-count."""
    with conn.transaction():
        conn.execute("select pg_advisory_xact_lock(hashtext(%s))", (API,))
        day, month = usage(conn, today)
        if day >= DAILY_LIMIT or month >= MONTHLY_LIMIT:
            raise FreeAllowanceUsed(f"{API}: {day} today, {month} this month")
        conn.execute(
            "insert into api_usage (day, api, calls) values (%s, %s, 1) "
            "on conflict (day, api) do update set calls = api_usage.calls + 1",
            (today, API),
        )


class PlacesClient:
    def __init__(self, api_key: str, conn, session: requests.Session | None = None):
        self.api_key, self.conn = api_key, conn
        self.session = session or requests.Session()

    def text_search(self, query: str, page_size: int = 3) -> list[dict]:
        _claim_call(self.conn, date.today())
        response = self.session.post(
            URL,
            json={"textQuery": query, "regionCode": "GB", "pageSize": page_size},
            headers={"X-Goog-Api-Key": self.api_key, "X-Goog-FieldMask": FIELDS},
            timeout=20,
        )
        response.raise_for_status()
        return response.json().get("places", [])
