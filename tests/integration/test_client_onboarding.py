from pathlib import Path

from client_onboarding.field_mapping.mapper import build_column_mapping
from client_onboarding.intake.intake import run_intake

FIXTURE = Path(__file__).parents[1] / "fixtures" / "messy_client_export.csv"


def test_build_column_mapping_handles_exact_and_fuzzy_aliases():
    mapping = build_column_mapping([
        "Business Name", "Contact Email", "Tel", "Zip Code", "Industry",
        "Deal Value", "Opportunity Status", "Meeting Status", "Loss Reason",
    ])
    assert mapping["Business Name"] == "company_name"
    assert mapping["Contact Email"] == "email"
    assert mapping["Tel"] == "phone"
    assert mapping["Zip Code"] == "postcode"
    assert mapping["Industry"] == "industry"
    assert mapping["Deal Value"] == "quote_value"
    assert mapping["Opportunity Status"] == "quote_status"
    assert mapping["Meeting Status"] == "appointment_status"
    assert mapping["Loss Reason"] == "lost_reason"


def test_build_column_mapping_leaves_unrecognized_headers_unmapped():
    mapping = build_column_mapping(["Company", "Some Totally Unrelated Field"])
    assert mapping["Company"] == "company_name"
    assert "Some Totally Unrelated Field" not in mapping


def test_run_intake_maps_and_flags_quality_issues():
    result = run_intake(FIXTURE)

    assert result["mapping"]["Business Name"] == "company_name"
    assert result["records"][0]["company_name"] == "Windowcraft Ltd"

    report = result["quality_report"]
    assert report["total_records"] == 3
    assert report["clean_records"] == 2
    assert report["issue_counts"]["invalid_email"] == 1
