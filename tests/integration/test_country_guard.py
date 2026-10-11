"""The send list must stay UK-only until Ireland is switched on on purpose.
Every migration that restates the outreach_queue view copies the whole
body, so a rewrite that forgets the country filter would silently put
Irish rows (CRO data, different law) into the UK send list."""

import re
from pathlib import Path

MIGRATIONS = Path(__file__).parents[2] / "supabase" / "migrations"


def test_newest_outreach_queue_rewrite_keeps_the_uk_filter():
    touching = [p for p in sorted(MIGRATIONS.glob("*.sql"))
                if re.search(r"(create (or replace )?view public\.outreach_queue|public\.outreach_queue.*as\b)",
                             p.read_text(encoding="utf-8"), re.IGNORECASE | re.DOTALL)
                and "outreach_queue" in p.read_text(encoding="utf-8")]
    rewrites = [p for p in touching if re.search(r"create (or replace )?view public\.outreach_queue|'create view public\.outreach_queue",
                                                 p.read_text(encoding="utf-8"), re.IGNORECASE)]
    assert rewrites, "no outreach_queue definition found"
    newest = rewrites[-1]
    text = newest.read_text(encoding="utf-8")
    assert "country" in text and "'UK'" in text, (
        f"{newest.name} redefines outreach_queue without the country = 'UK' filter; "
        "copy the base CTE filter from 20261012020000_country.sql's intent: where c.country = 'UK' and ..."
    )
