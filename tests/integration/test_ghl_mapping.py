from integrations.ghl.mapping import (
    experiment_result_to_ghl_opportunity,
    lead_to_ghl_contact,
    reactivation_record_to_ghl_contact,
)


def test_lead_to_ghl_contact_maps_fields_and_tags():
    lead = {
        "company_name": "Acme Windows",
        "email": "info@acme.co.uk",
        "phone": "+441234567890",
        "postcode": "SW1A 1AA",
        "website": "acme.co.uk",
        "lead_source": "csv_import",
        "qualified": True,
        "icp_score": 100.0,
    }

    contact = lead_to_ghl_contact(lead)

    assert contact["companyName"] == "Acme Windows"
    assert contact["email"] == "info@acme.co.uk"
    assert contact["postalCode"] == "SW1A 1AA"
    assert "qualified" in contact["tags"]
    assert "icp-score-100" in contact["tags"]


def test_lead_to_ghl_contact_drops_empty_fields():
    contact = lead_to_ghl_contact({"company_name": "Acme", "email": None, "phone": ""})
    assert "email" not in contact
    assert "phone" not in contact
    assert contact["companyName"] == "Acme"


def test_reactivation_record_to_ghl_contact_tags_segment_and_offer():
    record = {
        "name": "John Smith",
        "email": "john@example.com",
        "segment": "lost",
        "recommended_offer": "Updated pricing",
    }

    contact = reactivation_record_to_ghl_contact(record)

    assert contact["name"] == "John Smith"
    assert "lost" in contact["tags"]
    assert "offer-updated-pricing" in contact["tags"]


def test_experiment_result_to_ghl_opportunity_maps_won_status():
    won = experiment_result_to_ghl_opportunity(
        {"company_name": "Acme", "revenue": 4500.0, "sale_closed": True},
        pipeline_id="pipe-1",
        pipeline_stage_id="stage-won",
    )
    assert won["status"] == "won"
    assert won["monetaryValue"] == 4500.0

    open_opp = experiment_result_to_ghl_opportunity(
        {"company_name": "Acme", "quote_value": 3000.0, "sale_closed": False},
        pipeline_id="pipe-1",
        pipeline_stage_id="stage-open",
    )
    assert open_opp["status"] == "open"
    assert open_opp["monetaryValue"] == 3000.0
