"""Pushes Velarqo records to GHL and stores the returned contact id back
onto the record. Optional at every call site — nothing in the pipelines
requires a GHLClient; this is only exercised once a real client passes one
in (see docs/ghl/GHL_FOR_VELARQO.md, seam point 3).
"""

from integrations.ghl.client import GHLClient
from integrations.ghl.mapping import lead_to_ghl_contact, reactivation_record_to_ghl_contact


def sync_lead(client: GHLClient, lead: dict) -> dict:
    if lead.get("duplicate_of"):
        return lead

    contact = lead_to_ghl_contact(lead)
    if not contact.get("email") and not contact.get("phone"):
        return lead

    response = client.upsert_contact(contact)
    return {**lead, "ghl_contact_id": response["contact"]["id"]}


def sync_leads(client: GHLClient, leads: list[dict]) -> list[dict]:
    return [sync_lead(client, lead) for lead in leads]


def sync_reactivation_record(client: GHLClient, record: dict) -> dict:
    if record.get("duplicate_of") or record.get("suppressed"):
        return record

    contact = reactivation_record_to_ghl_contact(record)
    if not contact.get("email") and not contact.get("phone"):
        return record

    response = client.upsert_contact(contact)
    return {**record, "ghl_contact_id": response["contact"]["id"]}


def sync_reactivation_records(client: GHLClient, records: list[dict]) -> list[dict]:
    return [sync_reactivation_record(client, record) for record in records]
