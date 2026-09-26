from lib.normalization.normalize import normalize_email, normalize_phone


def check_record(record: dict, required_fields: list[str]) -> list[str]:
    issues = []

    for field in required_fields:
        if not record.get(field):
            issues.append(f"missing_{field}")

    email = record.get("email")
    if email and not normalize_email(email):
        issues.append("invalid_email")

    phone = record.get("phone")
    if phone and not normalize_phone(phone):
        issues.append("invalid_phone")

    return issues


def run_quality_report(records: list[dict], required_fields: list[str]) -> dict:
    total = len(records)
    issue_counts: dict[str, int] = {}
    clean_count = 0

    for record in records:
        issues = check_record(record, required_fields)
        if not issues:
            clean_count += 1
        for issue in issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

    return {
        "total_records": total,
        "clean_records": clean_count,
        "records_with_issues": total - clean_count,
        "issue_counts": issue_counts,
    }
