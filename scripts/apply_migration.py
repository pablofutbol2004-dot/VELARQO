"""Apply a migration file to Velarqo's Postgres (the velarqo-postgres Docker
container), as the admin user. Replaces Supabase's apply_migration.

    .venv/Scripts/python.exe scripts/apply_migration.py supabase/migrations/20261006000000_x.sql

Runs in one transaction; stops at the first error. Applied files are
recorded in public.schema_migrations so nothing runs twice.
"""

import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).parents[1]
CONTAINER = "velarqo-postgres"


def psql(args: list[str], password: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "exec", "-e", f"PGPASSWORD={password}", CONTAINER, "psql", "-U", "postgres", "-d", "velarqo",
         "-v", "ON_ERROR_STOP=1", "-q", "-At", *args],
        capture_output=True, text=True,
    )


def main(path: str) -> None:
    password = dotenv_values(ROOT / ".env")["VELARQO_PG_ADMIN_PASSWORD"]
    name = Path(path).name
    psql(["-c", "create table if not exists public.schema_migrations (name text primary key, applied_at timestamptz not null default now())"], password)
    done = psql(["-c", f"select 1 from public.schema_migrations where name = '{name}'"], password)
    if done.stdout.strip() == "1":
        print(f"{name}: already applied")
        return
    subprocess.run(["docker", "cp", str(Path(path).resolve()), f"{CONTAINER}:/tmp/{name}"], check=True)
    result = psql(["--single-transaction", "-f", f"/tmp/{name}",
                   "-c", f"insert into public.schema_migrations (name) values ('{name}')"], password)
    if result.returncode:
        raise SystemExit(f"{name}: FAILED, nothing applied\n{result.stderr[-2000:]}")
    print(f"{name}: applied")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_migration.py <file.sql>")
    main(sys.argv[1])
