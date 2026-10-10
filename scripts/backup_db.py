"""Daily backup of Velarqo's Postgres (velarqo-postgres container).

    .venv/Scripts/python.exe scripts/backup_db.py            # make one now
    .venv/Scripts/python.exe scripts/backup_db.py --check    # prove the newest backup restores

Writes data/backups/velarqo_<UTC timestamp>.dump (pg_dump custom format,
compressed), keeps the newest KEEP files, and deletes older ones. Runs
pg_dump inside the container as the local postgres user, so no password is
passed on any command line.

These files sit on the same PC as the database: copy the newest one off the
machine (Google Drive / external disk) regularly. On the VPS, ship it off-box
nightly instead.
"""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUT = ROOT / "data" / "backups"
KEEP = 14
CONTAINER = "velarqo-postgres"


def make_backup() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"velarqo_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.dump"
    with path.open("wb") as f:
        result = subprocess.run(["docker", "exec", CONTAINER, "pg_dump", "-U", "postgres", "-Fc", "velarqo"],
                                stdout=f, stderr=subprocess.PIPE)
    if result.returncode or path.stat().st_size < 1000:
        path.unlink(missing_ok=True)
        raise SystemExit(f"backup FAILED: {result.stderr.decode(errors='replace')[-500:]}")
    for old in sorted(OUT.glob("velarqo_*.dump"))[:-KEEP]:
        old.unlink()
    return path


def check_latest() -> None:
    """Lists the newest backup's contents; a corrupt file fails here."""
    newest = sorted(OUT.glob("velarqo_*.dump"))[-1]
    with newest.open("rb") as f:
        result = subprocess.run(["docker", "exec", "-i", CONTAINER, "pg_restore", "--list"], stdin=f, capture_output=True)
    tables = result.stdout.decode(errors="replace").count(" TABLE DATA ")
    if result.returncode or tables < 10:
        raise SystemExit(f"backup check FAILED for {newest.name}: {result.stderr.decode(errors='replace')[-300:]}")
    print(f"{newest.name}: readable, {tables} tables")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check_latest()
    else:
        path = make_backup()
        print(f"{datetime.now():%Y-%m-%d %H:%M} backup ok: {path.name} ({path.stat().st_size // 1_000_000} MB)")
