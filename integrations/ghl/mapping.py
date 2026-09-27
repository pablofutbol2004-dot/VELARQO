"""Maps Velarqo's internal schemas onto GHL's Contact/Opportunity upsert
DTOs. See docs/ghl/product/contacts.md and opportunities.md for the field
mapping tables this implements.
"""


def lead_to_ghl_contact(lead: dict) -> dict:
    tags = []
    if lead.get("qualified"):
        tags.append("qualified")
    if lead.get("icp_score") is not None:
        tags.append(f"icp-score-{int(lead['icp_score'])}")

    contact = {
        "companyName": lead.get("company_name"),
        "email": lead.get("email"),
        "phone": lead.get("phone"),
        "postalCode": lead.get("postcode"),
        "website": lead.get("website"),
        "source": lead.get("lead_source"),
        "tags": tags,
    }
    return {k: v for k, v in contact.items() if v not in (None, "", [])}


def reactivation_record_to_ghl_contact(record: dict) -> dict:
    tags = []
    if record.get("segment"):
        tags.append(record["segment"])
    if record.get("recommended_offer"):
        tags.append(f"offer-{record['recommended_offer']}".lower().replace(" ", "-"))

    contact = {
        "name": record.get("name"),
        "email": record.get("email"),
        "phone": record.get("phone"),
        "postalCode": record.get("postcode"),
        "source": record.get("lead_source"),
        "tags": tags,
    }
    return {k: v for k, v in contact.items() if v not in (None, "", [])}


def experiment_result_to_ghl_opportunity(experiment: dict, pipeline_id: str, pipeline_stage_id: str) -> dict:
    opportunity = {
        "pipelineId": pipeline_id,
        "pipelineStageId": pipeline_stage_id,
        "name": experiment.get("company_name"),
        "monetaryValue": experiment.get("quote_value") or experiment.get("revenue"),
        "status": "won" if experiment.get("sale_closed") else "open",
    }
    return {k: v for k, v in opportunity.items() if v not in (None, "", [])}
