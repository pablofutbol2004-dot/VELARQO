import csv
from pathlib import Path

_GHL_COLUMNS = [
    "name", "email", "phone", "postcode", "segment",
    "recovery_score", "economic_priority", "recommended_offer", "angle",
    "ghl_contact_id",
]


def export_for_ghl(records: list[dict], output_path: Path) -> int:
    """Write suppressed-filtered, ready-to-import records to a GHL-compatible CSV."""
    eligible = [r for r in records if not r.get("suppressed") and not r.get("duplicate_of")]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_GHL_COLUMNS)
        writer.writeheader()
        for record in eligible:
            writer.writerow({col: record.get(col, "") for col in _GHL_COLUMNS})

    return len(eligible)
