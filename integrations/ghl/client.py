"""GHL API v3 client. See docs/ghl/api/AUTH.md, RATE_LIMITS.md,
product/contacts.md, product/opportunities.md.

No credentials are wired up anywhere in this repo yet — this client is
built and unit-tested against a fake HTTP session, not exercised against
a real GHL account. Do not point it at a real Location without a Private
Integration Token supplied explicitly by whoever operates that account.
"""

import random
import time

import requests

from lib.rate_limiter import RateLimiter

BASE_URL = "https://services.leadconnectorhq.com"
API_VERSION = "v3"


class GHLRateLimitError(Exception):
    pass


class GHLTemporaryError(Exception):
    """5xx or network failure that survived the retries: safe to try again later."""


class GHLClient:
    def __init__(
        self,
        api_token: str,
        location_id: str,
        base_url: str = BASE_URL,
        session: requests.Session | None = None,
        rate_limiter: RateLimiter | None = None,
        max_retries: int = 3,
        sleep=time.sleep,
    ):
        self.api_token = api_token
        self.location_id = location_id
        self.base_url = base_url
        self.session = session or requests.Session()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.max_retries = max_retries
        self._sleep = sleep

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Version": API_VERSION,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, json: dict | None = None, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"

        for attempt in range(self.max_retries + 1):
            self.rate_limiter.acquire()
            try:
                response = self.session.request(method, url, headers=self._headers(), json=json, params=params, timeout=30)
            except (requests.Timeout, requests.ConnectionError) as exc:
                if attempt == self.max_retries:
                    raise GHLTemporaryError(f"{method} {path}: {type(exc).__name__}") from exc
                self._sleep(self._backoff(attempt))
                continue

            if response.status_code == 429:
                if attempt == self.max_retries:
                    raise GHLRateLimitError(f"Rate limited after {self.max_retries} retries: {method} {path}")
                retry_after = float(response.headers.get("Retry-After", 2**attempt))
                self._sleep(retry_after)
                continue
            if response.status_code >= 500:
                if attempt == self.max_retries:
                    raise GHLTemporaryError(f"{method} {path}: HTTP {response.status_code}")
                self._sleep(self._backoff(attempt))
                continue

            response.raise_for_status()  # 4xx: our request is wrong; retrying won't help
            return response.json()

        raise GHLRateLimitError(f"Rate limited after {self.max_retries} retries: {method} {path}")

    @staticmethod
    def _backoff(attempt: int) -> float:
        """2s, 4s, 8s... with +/-50% jitter so retries don't line up."""
        return 2 ** (attempt + 1) * random.uniform(0.5, 1.5)

    def add_tags(self, contact_id: str, tags: list[str]) -> dict:
        return self._request("POST", f"/contacts/{contact_id}/tags", json={"tags": tags})

    def upsert_contact(self, contact: dict) -> dict:
        body = {**contact, "locationId": self.location_id}
        return self._request("POST", "/contacts/upsert", json=body)

    def upsert_opportunity(self, opportunity: dict) -> dict:
        body = {**opportunity, "locationId": self.location_id}
        return self._request("POST", "/opportunities/upsert", json=body)

    def get_pipelines(self) -> dict:
        return self._request("GET", "/opportunities/pipelines", params={"locationId": self.location_id})

    def search_contacts(self, query: dict) -> dict:
        body = {**query, "locationId": self.location_id}
        return self._request("POST", "/contacts/search", json=body)
