import uuid
from datetime import datetime, timezone
from pathlib import Path

import click
import pandas as pd

from database_reactivation.campaign_generator.recommend import recommend_campaigns
from database_reactivation.segmentation.suppression import apply_suppression
from integrations.ghl.export import export_for_ghl
from lib.normalization.normalize_contact import normalize_record
from lib.scoring.recovery_score import score_records
from lib.segmentation.segment import segment_records
from prospecting.deduplication.dedupe import deduplicate

DEFAULT_OUTPUT_PATH = Path(__file__).parents[2] / "data" / "reactivation_export.csv"


def load_records_from_csv(csv_path: Path) -> list[dict]:
    df = pd.read_csv(csv_path)
    df = df.astype(object).where(df.notna(), None)
    records = df.to_dict(orient="records")
    for record in records:
        record["id"] = str(uuid.uuid4())
        record.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    return records


def run_pipeline(csv_path: Path) -> list[dict]:
    records = load_records_from_csv(csv_path)
    records = [normalize_record(r) for r in records]
    records = deduplicate(records, name_field="name")
    records = segment_records(records)
    records = score_records(records)
    records = recommend_campaigns(records)
    records = apply_suppression(records)
    return records


@click.command()
@click.argument("csv_path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=DEFAULT_OUTPUT_PATH)
def main(csv_path: Path, output_path: Path) -> None:
    records = run_pipeline(csv_path)

    total = len(records)
    duplicates = sum(1 for r in records if r.get("duplicate_of"))
    suppressed_non_duplicate = sum(
        1 for r in records if r.get("suppressed") and not r.get("duplicate_of")
    )
    eligible = total - duplicates - suppressed_non_duplicate

    click.echo(f"Processed {total} records")
    click.echo(f"  Duplicates: {duplicates}")
    click.echo(f"  Suppressed (other reasons): {suppressed_non_duplicate}")
    click.echo(f"  Eligible for campaign: {eligible}\n")

    by_segment: dict[str, int] = {}
    for r in records:
        if r.get("duplicate_of") or r.get("suppressed"):
            continue
        by_segment[r["segment"]] = by_segment.get(r["segment"], 0) + 1
    click.echo("By segment:")
    for segment, count in sorted(by_segment.items()):
        click.echo(f"  {segment:10} {count}")
    click.echo("")

    ranked = sorted(
        (r for r in records if not r.get("duplicate_of") and not r.get("suppressed")),
        key=lambda r: r["economic_priority"],
        reverse=True,
    )
    for r in ranked:
        click.echo(
            f"  [{r['segment']:8}] {r['name']:15} recovery={r['recovery_score']:5.1f} "
            f"priority={r['economic_priority']:8.1f} offer={r['recommended_offer']}"
        )

    exported = export_for_ghl(records, output_path)
    click.echo(f"\nExported {exported} records to {output_path}")


if __name__ == "__main__":
    main()
