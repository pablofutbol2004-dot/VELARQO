from pathlib import Path

import click
import pandas as pd

from client_onboarding.data_quality.quality_check import run_quality_report
from client_onboarding.field_mapping.mapper import apply_mapping, build_column_mapping

DEFAULT_REQUIRED_FIELDS = ["email"]


def load_csv(csv_path: Path) -> list[dict]:
    df = pd.read_csv(csv_path)
    df = df.astype(object).where(df.notna(), None)
    return df.to_dict(orient="records")


def run_intake(csv_path: Path, required_fields: list[str] = None) -> dict:
    required_fields = required_fields or DEFAULT_REQUIRED_FIELDS
    raw_records = load_csv(csv_path)

    headers = list(raw_records[0].keys()) if raw_records else []
    mapping = build_column_mapping(headers)
    mapped_records = apply_mapping(raw_records, mapping)

    unmapped_headers = [h for h in headers if h not in mapping]
    quality_report = run_quality_report(mapped_records, required_fields)

    return {
        "mapping": mapping,
        "unmapped_headers": unmapped_headers,
        "records": mapped_records,
        "quality_report": quality_report,
    }


@click.command()
@click.argument("csv_path", type=click.Path(exists=True, path_type=Path))
def main(csv_path: Path) -> None:
    result = run_intake(csv_path)

    click.echo("=== Column Mapping ===")
    for original, canonical in result["mapping"].items():
        click.echo(f"  {original!r:30} -> {canonical}")
    if result["unmapped_headers"]:
        click.echo(f"\nUnmapped headers (kept as-is): {result['unmapped_headers']}")

    report = result["quality_report"]
    click.echo(f"\n=== Data Quality ===")
    click.echo(f"Total records: {report['total_records']}")
    click.echo(f"Clean records: {report['clean_records']}")
    click.echo(f"Records with issues: {report['records_with_issues']}")
    for issue, count in report["issue_counts"].items():
        click.echo(f"  {issue}: {count}")


if __name__ == "__main__":
    main()
