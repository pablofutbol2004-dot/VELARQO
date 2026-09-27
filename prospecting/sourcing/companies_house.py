"""UK Companies House API: free official company registry data (name, SIC
code = industry classification, incorporation date, size band via SIC/
company type). Requires a free API key - register at
https://developer.company-information.service.gov.uk/ (no cost, just an
account).

Auth: HTTP Basic, API key as username, empty password.

Only the two long-stable, well-documented endpoints are implemented here
(free-text search, full company profile). Companies House also publishes
an /advanced-search/companies endpoint that supports filtering by SIC
code server-side - deliberately not implemented here since its exact
parameters weren't verified against live docs (unlike the GHL pack, there
was no vendored doc source for this API). Filtering by SIC code is done
client-side instead (search, then fetch each profile, then filter) -
slower and more API calls, but every call is against a well-established
endpoint. Revisit if request volume makes that inefficient.

Rate limit: Companies House publishes 600 requests / 5 minutes per API
key. Re-verify before raising the default. Source:
https://developer.company-information.service.gov.uk/api/docs/index/gettingStarted/rateLimiting.html
"""

import time

import requests

from lib.rate_limiter import RateLimiter

API_BASE = "https://api.company-information.service.gov.uk"
DEFAULT_MAX_REQUESTS = 600
DEFAULT_WINDOW_SECONDS = 300.0


class CompaniesHouseClient:
    def __init__(
        self,
        api_key: str,
        session: requests.Session | None = None,
        rate_limiter: RateLimiter | None = None,
        sleep=time.sleep,
    ):
        self.api_key = api_key
        self.session = session or requests.Session()
        self.rate_limiter = rate_limiter or RateLimiter(DEFAULT_MAX_REQUESTS, DEFAULT_WINDOW_SECONDS)
        self._sleep = sleep

    def _get(self, path: str, params: dict | None = None) -> dict:
        self.rate_limiter.acquire()
        response = self.session.get(
            f"{API_BASE}{path}", params=params, auth=(self.api_key, ""), timeout=30
        )
        response.raise_for_status()
        return response.json()

    def search_companies(self, query: str, items_per_page: int = 20) -> list[dict]:
        data = self._get("/search/companies", params={"q": query, "items_per_page": items_per_page})
        return data.get("items", [])

    def get_company_profile(self, company_number: str) -> dict:
        return self._get(f"/company/{company_number}")

    def find_companies_by_sic_prefix(self, query: str, sic_prefixes: list[str], max_results: int = 20) -> list[dict]:
        """Free-text search, then fetch each profile and keep only companies
        whose sic_codes start with one of sic_prefixes. See
        https://resources.companieshouse.gov.uk/sic/ for the SIC list -
        e.g. "43320" is Joinery installation, useful for a windows/doors ICP.
        """
        candidates = self.search_companies(query, items_per_page=max_results)
        matches = []
        for candidate in candidates:
            company_number = candidate.get("company_number")
            if not company_number:
                continue
            profile = self.get_company_profile(company_number)
            sic_codes = profile.get("sic_codes", [])
            if any(code.startswith(tuple(sic_prefixes)) for code in sic_codes):
                matches.append(profile)
        return matches


def profile_to_lead(profile: dict, lead_source: str = "companies_house") -> dict:
    address = profile.get("registered_office_address", {})
    address_parts = [address.get(k) for k in ("address_line_1", "address_line_2", "locality") if address.get(k)]

    return {
        "company_name": profile.get("company_name"),
        "website": None,
        "email": None,
        "phone": None,
        "postcode": address.get("postal_code"),
        "address": ", ".join(address_parts) or None,
        "industry": ", ".join(profile.get("sic_codes", [])) or None,
        "lead_source": lead_source,
        "company_number": profile.get("company_number"),
        "date_of_creation": profile.get("date_of_creation"),
        "company_status": profile.get("company_status"),
    }
