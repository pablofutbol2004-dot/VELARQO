from pathlib import Path

from pipelines.database_reactivation.pipeline import run_pipeline

FIXTURE = Path(__file__).parents[1] / "fixtures" / "synthetic_reactivation.csv"


def test_pipeline_dedupes_exact_matches():
    records = run_pipeline(FIXTURE)
    duplicates = [r for r in records if r.get("duplicate_of")]
    assert len(duplicates) == 1
    assert duplicates[0]["name"] == "John Smith"


def test_pipeline_segments_records():
    records = run_pipeline(FIXTURE)
    by_name = {r["name"]: r["segment"] for r in records if not r.get("duplicate_of")}
    assert by_name["John Smith"] == "lost"
    assert by_name["Jane Doe"] == "no_show"
    assert by_name["Alice Brown"] == "quoted"
    assert by_name["Carol Evans"] == "expired"
    assert by_name["Eve Adams"] == "won"


def test_pipeline_suppresses_invalid_and_unsubscribed_and_recent():
    records = run_pipeline(FIXTURE)
    by_name = {r["name"]: r for r in records if not r.get("duplicate_of")}

    assert by_name["Dave Green"]["suppressed"] is True
    assert by_name["Dave Green"]["suppression_reason"] == "invalid_email"

    assert by_name["Eve Adams"]["suppressed"] is True
    assert by_name["Eve Adams"]["suppression_reason"] == "unsubscribed"

    assert by_name["Jane Doe"]["suppressed"] is True
    assert by_name["Jane Doe"]["suppression_reason"] == "recently_contacted"


def test_pipeline_scores_recovery_and_priority():
    records = run_pipeline(FIXTURE)
    by_name = {r["name"]: r for r in records if not r.get("duplicate_of")}

    john = by_name["John Smith"]
    assert 0 <= john["recovery_score"] <= 100
    assert john["economic_priority"] == round((john["recovery_score"] / 100) * john["quote_value"], 2)


def test_pipeline_recommends_campaign_per_segment():
    records = run_pipeline(FIXTURE)
    by_name = {r["name"]: r for r in records if not r.get("duplicate_of")}

    assert by_name["John Smith"]["recommended_offer"] == "Updated pricing"
    assert by_name["Bob Wilson"]["recommended_offer"] == "Feature comparison"
    assert by_name["Jane Doe"]["recommended_offer"] == "Easy reschedule"
