from pathlib import Path

from pipelines.cold_outreach.pipeline import run_pipeline

FIXTURE = Path(__file__).parents[1] / "fixtures" / "synthetic_leads.csv"


def test_pipeline_dedupes_exact_matches():
    leads = run_pipeline(FIXTURE)
    duplicates = [lead for lead in leads if lead.get("duplicate_of")]
    assert len(duplicates) == 1
    assert duplicates[0]["company_name"] == "Acme Windows"


def test_pipeline_qualifies_only_industry_matches():
    leads = run_pipeline(FIXTURE)
    qualified = {lead["company_name"] for lead in leads if lead.get("qualified")}
    assert qualified == {"Acme Windows", "Brightframe Installations", "Brite Frame Installations"}


def test_pipeline_rejects_invalid_email():
    leads = run_pipeline(FIXTURE)
    bad_lead = next(lead for lead in leads if lead["company_name"] == "Not A Real Company")
    assert bad_lead["email"] is None
