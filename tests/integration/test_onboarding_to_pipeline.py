"""Proves the seam actually connects: a client's raw, arbitrarily-headed
CSV export goes through client_onboarding's mapping, then straight into
the cold-outreach pipeline's core processing - no manual re-shaping in
between. Before this, onboarding and the pipelines only ran side by side.
"""

from pathlib import Path

from client_onboarding.intake.intake import run_intake
from pipelines.cold_outreach.pipeline import load_icp, run_pipeline_on_leads

FIXTURE = Path(__file__).parents[1] / "fixtures" / "messy_client_export.csv"
ICP_PATH = Path(__file__).parents[2] / "config" / "templates" / "icp-template.json"


def test_messy_client_csv_flows_through_onboarding_into_cold_outreach():
    intake_result = run_intake(FIXTURE, required_fields=["email"])
    icp = load_icp(ICP_PATH)

    # intake maps "Business Name" -> company_name, "Contact Email" -> email, etc.
    # run_pipeline_on_leads never sees the client's original column names.
    leads = run_pipeline_on_leads(intake_result["records"], icp)

    by_name = {lead["company_name"]: lead for lead in leads}
    assert "Windowcraft" in by_name
    assert by_name["Windowcraft"]["qualified"] is True
    assert by_name["Windowcraft"]["research_summary"]

    # the row with an invalid email should still flow through (data quality
    # is a report, not a hard filter) but fail normalization/qualification
    # on its own terms rather than crashing the pipeline. "Co" is stripped
    # as a company suffix by normalize_company_name, same as "Ltd".
    assert "Bad Data" in by_name
    assert by_name["Bad Data"]["email"] is None
