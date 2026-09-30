from pipelines.uk_universe.enrich_db import update_rows

FETCHED = "2026-09-30T10:00:00+00:00"


def test_new_phone_and_email_are_written_with_provenance():
    [row] = update_rows([{
        "id": "c1", "website": "https://acme.co.uk", "enriched": True, "website_status": "ok",
        "website_fetched_at": FETCHED, "phone": "+441234567890", "phone_source": "website",
        "phones_found": ["+441234567890"], "email": "info@acme.co.uk", "email_source": "website",
        "emails_found": ["info@acme.co.uk"],
    }])
    assert row["phone"] == "+441234567890" and row["phone_source"] == "website"
    assert row["email"] == "info@acme.co.uk"
    assert row["fetched_at"] == FETCHED


def test_existing_contact_details_are_not_passed_as_new():
    # batch.enrich_websites drops the found email/phone when the lead already had
    # one, so the lead's own values come through without a *_source from this run.
    [row] = update_rows([{
        "id": "c1", "website": "https://acme.co.uk", "enriched": True, "website_status": "ok",
        "website_fetched_at": FETCHED, "phone": "+441111111111", "email": "owner@acme.co.uk",
        "email_source": "source", "phones_found": ["+442222222222"],
    }])
    assert row["phone"] is None
    assert row["email"] is None
    assert row["phones_found"] == ["+442222222222"]


def test_unfetched_leads_are_skipped():
    assert update_rows([{"id": "c1", "website": "https://x.co.uk", "enriched": False}]) == []
