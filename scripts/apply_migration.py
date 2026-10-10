"""Apply a migration file to Velarqo's Postgres (the velarqo-postgres Docker
container), as the admin user. Replaces Supabase's apply_migration.

    .venv/Scripts/python.exe scripts/apply_migration.py supabase/migrations/20261006000000_x.sql

Runs in one transaction; stops at the first error. Applied files are
recorded in public.schema_migrations so nothing runs twice. psql runs
inside the container as the local postgres user, so no password ever
appears on a command line.
"""

import subprocess
import sys
from pathlib import Path

CONTAINER = "velarqo-postgres"


def psql(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "exec", CONTAINER, "psql", "-U", "postgres", "-d", "velarqo", "-v", "ON_ERROR_STOP=1", "-q", "-At", *args],
        capture_output=True, text=True,
    )


def main(path: str) -> None:
    name = Path(path).name
    setup = psql(["-c", "create table if not exists public.schema_migrations "
                        "(name text primary key, applied_at timestamptz not null default now())"])
    if setup.returncode:
        raise SystemExit(f"can't reach the database: {setup.stderr[-500:]}")
    done = psql(["-c", f"select 1 from public.schema_migrations where name = '{name}'"])
    if done.returncode:
        raise SystemExit(f"can't read schema_migrations: {done.stderr[-500:]}")
    if done.stdout.strip() == "1":
        print(f"{name}: already applied")
        return
    subprocess.run(["docker", "cp", str(Path(path).resolve()), f"{CONTAINER}:/tmp/{name}"], check=True)
    result = psql(["--single-transaction", "-f", f"/tmp/{name}",
                   "-c", f"insert into public.schema_migrations (name) values ('{name}')"])
    if result.returncode:
        raise SystemExit(f"{name}: FAILED, nothing applied\n{result.stderr[-2000:]}")
    print(f"{name}: applied")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_migration.py <file.sql>")
    main(sys.argv[1])
