def segment_record(record: dict) -> str:
    quote_status = (record.get("quote_status") or "").lower()
    appointment_status = (record.get("appointment_status") or "").lower()

    if appointment_status == "no_show":
        return "no_show"
    if quote_status == "lost":
        return "lost"
    if quote_status == "expired":
        return "expired"
    if quote_status == "quoted":
        return "quoted"
    if quote_status == "won":
        return "won"
    return "unknown"


def segment_records(records: list[dict]) -> list[dict]:
    for record in records:
        if not record.get("duplicate_of"):
            record["segment"] = segment_record(record)
    return records
