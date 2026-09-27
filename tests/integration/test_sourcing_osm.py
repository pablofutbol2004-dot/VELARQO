from pathlib import Path

import pytest
import requests

from lib.rate_limiter import RateLimiter
from pipelines.cold_outreach.pipeline import load_icp, run_pipeline_on_leads
from prospecting.sourcing.osm import find_businesses, geocode_bbox

ICP_PATH = Path(__file__).parents[2] / "config" / "templates" / "icp-template.json"


class FakeResponse:
    def __init__(self, json_data, status_code=200, headers=None):
        self._json = json_data
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


class FakeSession:
    def __init__(self, get_response=None, post_response=None, post_responses=None):
        self._get_response = get_response
        self._post_responses = list(post_responses) if post_responses is not None else [post_response]
        self.get_calls = []
        self.post_calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.get_calls.append({"url": url, "params": params, "headers": headers})
        return self._get_response

    def post(self, url, data=None, headers=None, timeout=None):
        self.post_calls.append({"url": url, "data": data, "headers": headers})
        return self._post_responses.pop(0) if len(self._post_responses) > 1 else self._post_responses[0]


NOMINATIM_RESPONSE = [{"boundingbox": ["53.3401044", "53.5445923", "-2.3199185", "-2.1468288"]}]

OVERPASS_RESPONSE = {
    "elements": [
        {
            "id": 1,
            "tags": {
                "name": "Acme Windows",
                "shop": "window_blind",
                "website": "acmewindows.co.uk",
                "phone": "+44 20 7946 0958",
                "addr:postcode": "SW1A 1AA",
                "addr:street": "Baker Street",
            },
        },
        {"id": 2, "tags": {"shop": "window_blind"}},  # no name -> skipped
    ]
}


def _no_op_rate_limiter():
    return RateLimiter(clock=lambda: 0.0, sleep=lambda _: None)


def test_geocode_bbox_parses_nominatim_response():
    session = FakeSession(get_response=FakeResponse(NOMINATIM_RESPONSE))
    bbox = geocode_bbox("Manchester, UK", user_agent="velarqo-test/0.1", session=session)

    assert bbox == (53.3401044, -2.3199185, 53.5445923, -2.1468288)
    assert session.get_calls[0]["headers"]["User-Agent"] == "velarqo-test/0.1"


def test_find_businesses_maps_elements_and_skips_unnamed():
    session = FakeSession(
        get_response=FakeResponse(NOMINATIM_RESPONSE),
        post_response=FakeResponse(OVERPASS_RESPONSE),
    )

    leads = find_businesses(
        "Manchester, UK",
        tags=[("shop", "window_blind")],
        user_agent="velarqo-test/0.1",
        session=session,
        rate_limiter=_no_op_rate_limiter(),
    )

    assert len(leads) == 1
    lead = leads[0]
    assert lead["company_name"] == "Acme Windows"
    assert lead["website"] == "acmewindows.co.uk"
    assert lead["postcode"] == "SW1A 1AA"
    assert lead["lead_source"] == "osm_scrape"

    overpass_query = session.post_calls[0]["data"]["data"]
    assert '"shop"="window_blind"' in overpass_query
    assert "53.3401044,-2.3199185,53.5445923,-2.1468288" in overpass_query
    assert session.post_calls[0]["headers"]["Accept"] == "*/*"


def test_find_businesses_retries_on_transient_5xx_then_succeeds():
    sleeps = []
    session = FakeSession(
        get_response=FakeResponse(NOMINATIM_RESPONSE),
        post_responses=[
            FakeResponse({}, status_code=504),
            FakeResponse(OVERPASS_RESPONSE, status_code=200),
        ],
    )

    leads = find_businesses(
        "Manchester, UK",
        tags=[("shop", "window_blind")],
        user_agent="velarqo-test/0.1",
        session=session,
        rate_limiter=_no_op_rate_limiter(),
        sleep=sleeps.append,
    )

    assert len(leads) == 1
    assert sleeps == [1]
    assert len(session.post_calls) == 2


def test_find_businesses_respects_retry_after_header_on_429():
    sleeps = []
    session = FakeSession(
        get_response=FakeResponse(NOMINATIM_RESPONSE),
        post_responses=[
            FakeResponse({}, status_code=429, headers={"Retry-After": "5"}),
            FakeResponse(OVERPASS_RESPONSE, status_code=200),
        ],
    )

    leads = find_businesses(
        "Manchester, UK",
        tags=[("shop", "window_blind")],
        user_agent="velarqo-test/0.1",
        session=session,
        rate_limiter=_no_op_rate_limiter(),
        sleep=sleeps.append,
    )

    assert len(leads) == 1
    assert sleeps == [5.0]


def test_find_businesses_gives_up_after_max_retries():
    session = FakeSession(
        get_response=FakeResponse(NOMINATIM_RESPONSE),
        post_responses=[FakeResponse({}, status_code=504) for _ in range(5)],
    )

    with pytest.raises(requests.HTTPError):
        find_businesses(
            "Manchester, UK",
            tags=[("shop", "window_blind")],
            user_agent="velarqo-test/0.1",
            session=session,
            rate_limiter=_no_op_rate_limiter(),
            max_retries=2,
            sleep=lambda _: None,
        )

    assert len(session.post_calls) == 3


def test_osm_sourced_leads_flow_into_cold_outreach_pipeline():
    session = FakeSession(
        get_response=FakeResponse(NOMINATIM_RESPONSE),
        post_response=FakeResponse(OVERPASS_RESPONSE),
    )
    leads = find_businesses(
        "Manchester, UK",
        tags=[("shop", "window_blind")],
        user_agent="velarqo-test/0.1",
        session=session,
        rate_limiter=_no_op_rate_limiter(),
    )

    icp = load_icp(ICP_PATH)
    processed = run_pipeline_on_leads(leads, icp)

    assert processed[0]["company_name"] == "Acme Windows"
    assert processed[0]["id"]
    assert processed[0]["created_at"]
