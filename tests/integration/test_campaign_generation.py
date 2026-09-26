from pathlib import Path

from pipelines.cold_outreach.pipeline import build_campaign, load_icp, run_pipeline

FIXTURE = Path(__file__).parents[1] / "fixtures" / "synthetic_leads.csv"
ICP_PATH = Path(__file__).parents[2] / "config" / "templates" / "icp-template.json"


def test_qualified_leads_get_research_and_angle():
    leads = run_pipeline(FIXTURE)
    qualified = [lead for lead in leads if lead.get("qualified")]
    assert qualified
    for lead in qualified:
        assert lead["research_summary"]
        assert lead["angle"]


def test_unqualified_and_duplicate_leads_skip_research():
    leads = run_pipeline(FIXTURE)
    skipped = [lead for lead in leads if lead.get("duplicate_of") or not lead.get("qualified")]
    for lead in skipped:
        assert lead.get("research_summary") is None
        assert lead.get("angle") is None


def test_campaign_builds_one_email_per_qualified_lead():
    icp = load_icp(ICP_PATH)
    leads = run_pipeline(FIXTURE)
    campaign = build_campaign(leads, icp)

    qualified_count = sum(1 for lead in leads if lead.get("qualified"))
    assert len(campaign["queue"]) == qualified_count

    for item in campaign["queue"]:
        assert item["subject"]
        assert item["body"]
        assert item["send_time"]
        assert item["campaign_id"] == campaign["campaign_id"]
