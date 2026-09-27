from pathlib import Path

from lib.ai.research import research_lead
from outreach.personalization.generator import generate_campaign_emails
from pipelines.cold_outreach.pipeline import load_icp

ICP = load_icp(Path(__file__).parents[2] / "config" / "templates" / "icp-template.json")


def _researched(name, **fields):
    lead = {
        "id": name, "display_name": name, "company_name": name,
        "email": "info@x.co.uk", "qualified": True, "tier": "A", "icp_score": 90.0, **fields,
    }
    return research_lead(lead, ICP)


def test_greets_a_person_not_the_company_and_keeps_real_name():
    lead = _researched("Empire Doors & Windows", osm_category="shop=doors", city="Manchester")
    email = generate_campaign_emails([lead], ICP)[0]

    assert email["body"].startswith("Hi there,")
    assert "Hi Empire" not in email["body"]
    assert "Empire Doors & Windows" in email["body"] or "Empire Doors & Windows" in email["subject"]


def test_raw_data_never_leaks_into_copy():
    lead = _researched("Jade Windows", osm_category="craft=window_construction")
    body = generate_campaign_emails([lead], ICP)[0]["body"]

    assert "window_construction" not in body
    assert "craft=" not in body
    assert "Score" not in body  # research_summary is for us, not for them
    assert "\n\n\n" not in body


def test_three_real_variants_rotate():
    leads = [_researched(f"Firm {i} Windows") for i in range(3)]
    emails = generate_campaign_emails(leads, ICP)

    assert [e["variant_index"] for e in emails] == [0, 1, 2]
    assert len({e["subject"].replace(f"Firm {i} Windows", "") for i, e in enumerate(emails)}) == 3


def test_angle_uses_website_evidence_only_when_site_was_actually_checked():
    quoted = _researched("Acme Windows", website_status="ok", website_text="Get a free quote today")
    unchecked = _researched("Acme Windows", website="acme.co.uk", website_text="Get a free quote today")

    assert quoted["angle_key"] == "quote_driven"
    assert unchecked["angle_key"] == "default"


def test_accreditation_mentioned_in_observation():
    lead = _researched("Acme Windows", website_status="ok", website_text="We are FENSA registered installers", city="Leeds")
    assert lead["observation"] == "Came across Acme Windows while looking at windows and doors firms in Leeds and saw you're FENSA registered."
