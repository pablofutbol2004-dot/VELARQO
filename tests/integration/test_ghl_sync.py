from pathlib import Path

from integrations.ghl.client import GHLClient
from integrations.ghl.rate_limiter import RateLimiter
from integrations.ghl.sync import sync_leads, sync_reactivation_records
from pipelines.cold_outreach.pipeline import run_pipeline as run_cold_outreach
from pipelines.database_reactivation.pipeline import run_pipeline as run_reactivation

COLD_OUTREACH_FIXTURE = Path(__file__).parents[1] / "fixtures" / "synthetic_leads.csv"
REACTIVATION_FIXTURE = Path(__file__).parents[1] / "fixtures" / "synthetic_reactivation.csv"


class FakeGHLResponse:
    def __init__(self, contact_id):
        self._contact_id = contact_id

    def raise_for_status(self):
        pass

    def json(self):
        return {"new": True, "contact": {"id": self._contact_id}}

    status_code = 200
    headers = {}


class FakeGHLSession:
    def __init__(self):
        self.calls = []
        self._counter = 0

    def request(self, method, url, headers=None, json=None, params=None, timeout=None):
        self.calls.append({"method": method, "url": url, "json": json})
        self._counter += 1
        return FakeGHLResponse(f"ghl-contact-{self._counter}")


def _fake_client():
    return GHLClient(
        api_token="fake",
        location_id="loc-1",
        session=FakeGHLSession(),
        rate_limiter=RateLimiter(clock=lambda: 0.0, sleep=lambda _: None),
    )


def test_sync_leads_assigns_ghl_contact_id_to_qualified_non_duplicates():
    client = _fake_client()
    leads = run_cold_outreach(COLD_OUTREACH_FIXTURE)
    synced = sync_leads(client, leads)

    for lead in synced:
        if lead.get("duplicate_of"):
            assert "ghl_contact_id" not in lead or lead.get("ghl_contact_id") is None
        elif lead.get("email"):
            assert lead["ghl_contact_id"].startswith("ghl-contact-")


def test_sync_reactivation_records_skips_suppressed_and_duplicates():
    client = _fake_client()
    records = run_reactivation(REACTIVATION_FIXTURE)
    synced = sync_reactivation_records(client, records)

    for record in synced:
        if record.get("duplicate_of") or record.get("suppressed"):
            assert record.get("ghl_contact_id") is None
        else:
            assert record["ghl_contact_id"].startswith("ghl-contact-")
