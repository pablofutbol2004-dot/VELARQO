"""Lead enrichment. Ships with a no-op stub so the pipeline runs without API keys.

To wire a real provider (Clearbit, Apollo, Hunter.io, LinkedIn), implement
EnrichmentProvider and pass it into enrich_lead/enrich_leads.
"""

from typing import Protocol


class EnrichmentProvider(Protocol):
    def enrich(self, lead: dict) -> dict: ...


class NoopEnrichmentProvider:
    """Fills enrichment fields from data already present on the lead."""

    def enrich(self, lead: dict) -> dict:
        return {
            "recent_news": None,
            "linkedin_url": None,
            "verified_email": lead.get("email") is not None,
        }


def enrich_lead(lead: dict, provider: EnrichmentProvider | None = None) -> dict:
    provider = provider or NoopEnrichmentProvider()
    enrichment_data = provider.enrich(lead)
    return {**lead, **enrichment_data, "enriched": True}


def enrich_leads(leads: list[dict], provider: EnrichmentProvider | None = None) -> list[dict]:
    return [
        enrich_lead(lead, provider) if not lead.get("duplicate_of") else lead
        for lead in leads
    ]
