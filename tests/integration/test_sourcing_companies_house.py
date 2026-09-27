from lib.rate_limiter import RateLimiter
from prospecting.sourcing.companies_house import CompaniesHouseClient, profile_to_lead


class FakeResponse:
    def __init__(self, json_data):
        self._json = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


class FakeSession:
    def __init__(self, responses_by_url):
        self.responses_by_url = responses_by_url
        self.calls = []

    def get(self, url, params=None, auth=None, timeout=None):
        self.calls.append({"url": url, "params": params, "auth": auth})
        for pattern, response in self.responses_by_url.items():
            if pattern in url:
                return response
        raise AssertionError(f"No fake response configured for {url}")


def _no_op_rate_limiter():
    return RateLimiter(clock=lambda: 0.0, sleep=lambda _: None)


def test_search_companies_uses_basic_auth_with_api_key():
    session = FakeSession({"/search/companies": FakeResponse({"items": [{"company_number": "123"}]})})
    client = CompaniesHouseClient(api_key="my-key", session=session, rate_limiter=_no_op_rate_limiter())

    results = client.search_companies("acme windows")

    assert results == [{"company_number": "123"}]
    assert session.calls[0]["auth"] == ("my-key", "")
    assert session.calls[0]["params"]["q"] == "acme windows"


def test_find_companies_by_sic_prefix_filters_correctly():
    session = FakeSession({
        "/search/companies": FakeResponse({"items": [
            {"company_number": "111"},
            {"company_number": "222"},
        ]}),
        "/company/111": FakeResponse({"company_number": "111", "company_name": "Acme Windows Ltd", "sic_codes": ["43320"]}),
        "/company/222": FakeResponse({"company_number": "222", "company_name": "Acme Bakery Ltd", "sic_codes": ["10710"]}),
    })
    client = CompaniesHouseClient(api_key="my-key", session=session, rate_limiter=_no_op_rate_limiter())

    matches = client.find_companies_by_sic_prefix("acme", sic_prefixes=["4332"])

    assert len(matches) == 1
    assert matches[0]["company_name"] == "Acme Windows Ltd"


def test_profile_to_lead_maps_fields():
    profile = {
        "company_name": "Acme Windows Ltd",
        "sic_codes": ["43320"],
        "company_number": "111",
        "date_of_creation": "2015-03-01",
        "company_status": "active",
        "registered_office_address": {
            "address_line_1": "1 Baker Street",
            "locality": "London",
            "postal_code": "SW1A 1AA",
        },
    }

    lead = profile_to_lead(profile)

    assert lead["company_name"] == "Acme Windows Ltd"
    assert lead["postcode"] == "SW1A 1AA"
    assert lead["lead_source"] == "companies_house"
    assert lead["email"] is None
    assert "43320" in lead["industry"]
