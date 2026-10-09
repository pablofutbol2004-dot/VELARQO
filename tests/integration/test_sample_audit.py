from datetime import date

from client_onboarding.sample_audit import audit, report_markdown

TODAY = date(2026, 10, 10)


def _rows():
    return [
        {"Quote Date": "15/09/2026", "Job Type": "Windows", "Status": "Quoted", "Value": "£4,200"},   # 0 months: too recent
        {"Quote Date": "01/05/2026", "Job Type": "Windows", "Status": "No reply", "Value": "3,000"},  # 5 months: chase
        {"Quote Date": "20/11/2025", "Job Type": "Doors", "Status": "Lost", "Value": "1500"},        # 10 months: chase
        {"Quote Date": "01/03/2025", "Job Type": "Windows", "Status": "Sold", "Value": "6000"},      # won
        {"Quote Date": "01/01/2023", "Job Type": "Windows", "Status": "Lost", "Value": "2000"},      # too old
        {"Quote Date": "01/06/2025", "Job Type": "Windows", "Status": "Lost", "Value": "", "Do Not Contact": "Yes"},
        {"Quote Date": "", "Job Type": "Roof", "Status": "Lost", "Value": "900"},                   # no date
    ]


def test_sample_is_sorted_into_chase_and_reasons():
    result = audit(_rows(), TODAY)
    assert result["total"] == 7
    assert result["verdicts"]["worth chasing"] == 2
    assert result["verdicts"]["already won/booked"] == 1
    assert result["verdicts"]["opted out"] == 1
    assert result["verdicts"]["too recent (under 3 months)"] == 1
    assert result["verdicts"]["too old (over 24 months)"] == 1
    assert result["verdicts"]["no usable date"] == 1
    assert result["chase_by_product"] == {"windows": 1, "doors": 1}
    assert sorted(result["chase_values"]) == [1500.0, 3000.0]


def test_dates_are_read_day_first_like_uk_exports():
    # 01/05/2026 is 1 May (5 months ago), not 5 January.
    result = audit([{"Date": "01/05/2026", "Status": "Lost"}], TODAY)
    assert result["ages"]["3-6 months"] == 1


def test_report_has_counts_but_no_homeowner_details():
    rows = [{**r, "Customer Name": "Jane Smith", "Phone": "07700900123"} for r in _rows()]
    text = report_markdown(audit(rows, TODAY), "Acme Windows")
    assert "2 of 7 quotes" in text
    assert "Jane Smith" not in text and "07700900123" not in text
