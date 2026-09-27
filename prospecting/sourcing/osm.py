"""Finds businesses via OpenStreetMap: Nominatim (geocoding a place name to
a bounding box) + Overpass (querying businesses within that box by OSM
tag). Both are free and keyless.

Both are shared public infrastructure, not Velarqo's own servers - be a
good citizen:
- Nominatim's usage policy caps at ~1 request/second and requires an
  identifying User-Agent (not a login, just a real one - set it via
  user_agent, don't ship a default that pretends to be a browser).
- Overpass API has no hard published per-key limit like Nominatim, but is
  a shared free resource; the default rate limiter here is deliberately
  conservative. For real production volume, self-host Overpass or use a
  paid geocoding/Overpass provider instead of hammering the public
  instance - that's a cost/ops tradeoff, not a code change.

Verify current usage policy before raising these defaults:
https://operations.osmfoundation.org/policies/nominatim/
https://wiki.openstreetmap.org/wiki/Overpass_API#Rate_limiting
"""

import time

import requests

from lib.rate_limiter import RateLimiter

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
OVERPASS_BASE = "https://overpass-api.de/api/interpreter"


class OSMSourcingError(Exception):
    pass


def geocode_bbox(place_name: str, user_agent: str, session: requests.Session | None = None) -> tuple[float, float, float, float]:
    """Returns (south, west, north, east) for the given place name."""
    session = session or requests.Session()
    response = session.get(
        f"{NOMINATIM_BASE}/search",
        params={"q": place_name, "format": "json", "limit": 1},
        headers={"User-Agent": user_agent},
        timeout=30,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        raise OSMSourcingError(f"No geocoding result for {place_name!r}")

    south, north, west, east = (float(v) for v in results[0]["boundingbox"])
    return south, west, north, east


def _build_overpass_query(bbox: tuple[float, float, float, float], tags: list[tuple[str, str]]) -> str:
    south, west, north, east = bbox
    bbox_str = f"{south},{west},{north},{east}"
    clauses = "".join(f'  node["{key}"="{value}"]({bbox_str});\n' for key, value in tags)
    return f"[out:json][timeout:25];\n(\n{clauses});\nout body;"


def _element_to_lead(element: dict, lead_source: str) -> dict | None:
    tags = element.get("tags", {})
    name = tags.get("name")
    if not name:
        return None

    address_parts = [tags.get(k) for k in ("addr:housenumber", "addr:street", "addr:city") if tags.get(k)]

    return {
        "company_name": name,
        "website": tags.get("website") or tags.get("contact:website"),
        "email": tags.get("email") or tags.get("contact:email"),
        "phone": tags.get("phone") or tags.get("contact:phone"),
        "postcode": tags.get("addr:postcode"),
        "address": " ".join(address_parts) or None,
        "industry": tags.get("shop") or tags.get("craft") or tags.get("office"),
        "lead_source": lead_source,
        "osm_id": element.get("id"),
    }


_TRANSIENT_STATUS_CODES = {502, 503, 504}


def find_businesses(
    place_name: str,
    tags: list[tuple[str, str]],
    user_agent: str,
    session: requests.Session | None = None,
    rate_limiter: RateLimiter | None = None,
    lead_source: str = "osm_scrape",
    max_retries: int = 3,
    sleep=time.sleep,
) -> list[dict]:
    """tags: list of (osm_key, osm_value) pairs to match, e.g.
    [("shop", "doors"), ("craft", "carpenter")]. See
    https://wiki.openstreetmap.org/wiki/Map_features for the tag vocabulary.

    The public Overpass instance is shared, free infrastructure and
    genuinely flaky under load - confirmed live while building this
    (a 406, then a 504, then success, on the exact same query seconds
    apart). max_retries/backoff exists because of that observed behavior,
    not speculatively.
    """
    session = session or requests.Session()
    rate_limiter = rate_limiter or RateLimiter(max_requests=1, window_seconds=1.0)

    rate_limiter.acquire()
    bbox = geocode_bbox(place_name, user_agent, session)

    query = _build_overpass_query(bbox, tags)
    # Overpass's server does Apache content negotiation and returns 406 on
    # requests with no explicit Accept header - not documented anywhere
    # obvious, found by testing live.
    headers = {"Accept": "*/*", "User-Agent": user_agent}

    response = None
    for attempt in range(max_retries + 1):
        rate_limiter.acquire()
        response = session.post(OVERPASS_BASE, data={"data": query}, headers=headers, timeout=60)
        if response.status_code not in _TRANSIENT_STATUS_CODES:
            break
        if attempt < max_retries:
            sleep(2**attempt)

    response.raise_for_status()

    elements = response.json().get("elements", [])
    leads = [_element_to_lead(el, lead_source) for el in elements]
    return [lead for lead in leads if lead is not None]
