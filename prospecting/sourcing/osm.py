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

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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


# OSM relation 62149 (United Kingdom) as an Overpass area id.
UK_AREA_ID = 3600062149
UK_BBOX = (49.8, -8.7, 60.9, 1.9)


def build_overpass_query(
    bbox: tuple[float, float, float, float],
    tags: list[tuple[str, str]],
    area_id: int | None = None,
    name_pattern: str | None = None,
    name_keys: tuple[str, ...] = ("shop", "craft", "office"),
    timeout: int = 90,
) -> str:
    """nwr, not node: many businesses are mapped as building outlines (ways),
    which a node-only query silently misses. area_id clips a bbox tile to a
    country so tiles along the border don't pull in Ireland/France.

    name_pattern (case-insensitive regex) catches businesses whose tag is
    generic or missing but whose name gives them away ("Smith Windows Ltd"
    tagged craft=builder), restricted to things tagged as a business at all.
    """
    south, west, north, east = bbox
    bbox_filter = f"({south},{west},{north},{east})"
    area_decl = f"area(id:{area_id})->.region;\n" if area_id else ""
    area_filter = "(area.region)" if area_id else ""

    clauses = [f'  nwr["{key}"="{value}"]{area_filter}{bbox_filter};' for key, value in tags]
    if name_pattern:
        clauses += [f'  nwr["name"~"{name_pattern}",i]["{key}"]{area_filter}{bbox_filter};' for key in name_keys]
    body = "\n".join(clauses)
    return f"[out:json][timeout:{timeout}];\n{area_decl}(\n{body}\n);\nout center tags;"


def tile_bbox(bbox: tuple[float, float, float, float], step: float) -> list[tuple[float, float, float, float]]:
    south, west, north, east = bbox
    tiles = []
    lat = south
    while lat < north:
        lon = west
        while lon < east:
            tiles.append((round(lat, 4), round(lon, 4), round(min(lat + step, north), 4), round(min(lon + step, east), 4)))
            lon += step
        lat += step
    return tiles


def _element_to_lead(element: dict, lead_source: str) -> dict | None:
    tags = element.get("tags", {})
    name = tags.get("name")
    if not name:
        return None

    address_parts = [tags.get(k) for k in ("addr:housenumber", "addr:street", "addr:city") if tags.get(k)]
    category_key = next((k for k in ("shop", "craft", "office") if tags.get(k)), None)
    center = element.get("center") or {}

    return {
        "company_name": name,
        "website": tags.get("website") or tags.get("contact:website"),
        "email": tags.get("email") or tags.get("contact:email"),
        "phone": tags.get("phone") or tags.get("contact:phone"),
        "postcode": tags.get("addr:postcode"),
        "address": " ".join(address_parts) or None,
        "city": tags.get("addr:city"),
        "industry": tags.get(category_key) if category_key else None,
        "osm_category": f"{category_key}={tags[category_key]}" if category_key else None,
        # OSM marks chain branches with brand/brand:wikidata - free chain detection.
        "brand": tags.get("brand") or (tags.get("name") if tags.get("brand:wikidata") else None),
        "lat": element.get("lat") or center.get("lat"),
        "lon": element.get("lon") or center.get("lon"),
        "lead_source": lead_source,
        "osm_id": f"{element.get('type', 'node')}/{element.get('id')}",
        # every tag as mapped (opening_hours, operator, fhrs:id, check_date...),
        # kept so nothing is lost to the fields we happen to use today
        "osm_tags": tags,
    }


_TRANSIENT_STATUS_CODES = {429, 502, 503, 504}


def run_overpass(
    query: str,
    user_agent: str,
    session: requests.Session,
    rate_limiter: RateLimiter,
    max_retries: int = 3,
    sleep=time.sleep,
) -> list[dict]:
    """The public Overpass instance is shared, free infrastructure and
    genuinely flaky under load - confirmed live (a 406, then a 504, then
    success, on the same query seconds apart; 429s when sourcing 10 cities
    back to back). Retries exist because of that observed behavior.
    """
    # Overpass's server does Apache content negotiation and returns 406 on
    # requests with no explicit Accept header - found by testing live.
    headers = {"Accept": "*/*", "User-Agent": user_agent}

    response = None
    for attempt in range(max_retries + 1):
        rate_limiter.acquire()
        response = session.post(OVERPASS_BASE, data={"data": query}, headers=headers, timeout=180)
        if response.status_code not in _TRANSIENT_STATUS_CODES:
            break
        if attempt < max_retries:
            retry_after = response.headers.get("Retry-After")
            sleep(float(retry_after) if retry_after else 2**attempt)

    response.raise_for_status()
    return response.json().get("elements", [])


def _elements_to_leads(elements: list[dict], lead_source: str) -> list[dict]:
    leads = [_element_to_lead(el, lead_source) for el in elements]
    return [lead for lead in leads if lead is not None]


def find_businesses(
    place_name: str,
    tags: list[tuple[str, str]],
    user_agent: str,
    session: requests.Session | None = None,
    rate_limiter: RateLimiter | None = None,
    lead_source: str = "osm_scrape",
    max_retries: int = 3,
    sleep=time.sleep,
    name_pattern: str | None = None,
) -> list[dict]:
    """tags: list of (osm_key, osm_value) pairs to match, e.g.
    [("shop", "doors"), ("craft", "carpenter")]. See
    https://wiki.openstreetmap.org/wiki/Map_features for the tag vocabulary.
    """
    session = session or requests.Session()
    rate_limiter = rate_limiter or RateLimiter(max_requests=1, window_seconds=1.0)

    rate_limiter.acquire()
    bbox = geocode_bbox(place_name, user_agent, session)
    query = build_overpass_query(bbox, tags, name_pattern=name_pattern)
    elements = run_overpass(query, user_agent, session, rate_limiter, max_retries, sleep)
    return _elements_to_leads(elements, lead_source)


def find_businesses_in_region(
    tags: list[tuple[str, str]],
    user_agent: str,
    bbox: tuple[float, float, float, float] = UK_BBOX,
    area_id: int | None = UK_AREA_ID,
    name_pattern: str | None = None,
    tile_step: float = 0.5,
    lead_source: str = "osm_scrape",
    max_retries: int = 4,
    sleep=time.sleep,
    on_tile=None,
    workers: int = 2,
    cache_dir: Path | None = None,
    session_factory=requests.Session,
) -> list[dict]:
    """Whole-country sourcing in small tiles. Learned live: 1-degree tiles
    with the name regex timed out on the public server (London never came
    back); 0.5-degree tiles are ~4x lighter. Overpass allows 2 concurrent
    slots per client, hence 2 workers. Each finished tile is cached to
    cache_dir, so a re-run only retries the tiles that failed.
    """
    tiles = tile_bbox(bbox, tile_step)
    local = threading.local()

    def cache_file(tile) -> Path | None:
        return cache_dir / ("tile_" + "_".join(f"{v:.4f}" for v in tile) + ".json") if cache_dir else None

    def fetch(tile):
        path = cache_file(tile)
        if path and path.exists():
            return tile, json.loads(path.read_text(encoding="utf-8"))
        if not hasattr(local, "session"):
            local.session = session_factory()
            local.limiter = RateLimiter(max_requests=1, window_seconds=2.0)
        query = build_overpass_query(tile, tags, area_id=area_id, name_pattern=name_pattern)
        try:
            elements = run_overpass(query, user_agent, local.session, local.limiter, max_retries, sleep)
        except requests.RequestException as exc:
            return tile, exc
        if path:
            path.write_text(json.dumps(elements), encoding="utf-8")
        return tile, elements

    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)

    by_osm_id: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for tile, result in pool.map(fetch, tiles):
            if isinstance(result, Exception):
                if on_tile:
                    on_tile(tile, result)
                continue
            leads = _elements_to_leads(result, lead_source)
            for lead in leads:
                by_osm_id.setdefault(lead["osm_id"], lead)
            if on_tile:
                on_tile(tile, len(leads))
    return list(by_osm_id.values())
