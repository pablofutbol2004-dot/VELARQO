"""Proves the core architectural claim: switching vertical is a config
swap, not a code change. Same run_pipeline_on_leads/run_pipeline code,
same lib/scoring and lib/normalization modules, only the ICP JSON file
changes between a windows campaign and a kitchens campaign.
"""

from pathlib import Path

from pipelines.cold_outreach.pipeline import load_icp, run_pipeline

WINDOWS_ICP = Path(__file__).parents[2] / "config" / "templates" / "icp-template.json"
KITCHENS_ICP = Path(__file__).parents[2] / "config" / "templates" / "icp-kitchens-uk.json"
KITCHENS_FIXTURE = Path(__file__).parents[1] / "fixtures" / "synthetic_leads_kitchens.csv"


def test_kitchens_icp_qualifies_kitchen_companies_not_other_verticals():
    icp = load_icp(KITCHENS_ICP)
    assert icp["vertical"] == "kitchens"

    leads = run_pipeline(KITCHENS_FIXTURE, icp_path=KITCHENS_ICP)
    qualified = {lead["company_name"] for lead in leads if lead.get("qualified")}

    assert qualified == {"Bespoke Kitchens", "Worktop Wizards"}
    assert "Acme Windows" not in qualified
    assert "Solar Solutions" not in qualified
    assert "Premier Roofing" not in qualified


def test_same_lead_list_qualifies_differently_under_each_icp():
    """The exact same raw leads produce a different qualified set purely
    from which ICP file is passed in - no code path differs between runs.
    """
    windows_leads = run_pipeline(KITCHENS_FIXTURE, icp_path=WINDOWS_ICP)
    kitchens_leads = run_pipeline(KITCHENS_FIXTURE, icp_path=KITCHENS_ICP)

    windows_qualified = {lead["company_name"] for lead in windows_leads if lead.get("qualified")}
    kitchens_qualified = {lead["company_name"] for lead in kitchens_leads if lead.get("qualified")}

    assert windows_qualified == {"Acme Windows"}
    assert kitchens_qualified == {"Bespoke Kitchens", "Worktop Wizards"}
    assert windows_qualified.isdisjoint(kitchens_qualified)
