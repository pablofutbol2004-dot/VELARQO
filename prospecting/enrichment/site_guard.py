"""Shared checks before attaching a website to a company."""

from urllib.parse import urlsplit


def site_host(url: str | None) -> str:
    url = (url or "").strip()
    return (urlsplit(url if "://" in url else f"https://{url}").hostname or "").lower().removeprefix("www.")


def website_taken(conn, url: str, company_id) -> bool:
    """True if another company already has this website: two firms can't own
    one site, so the new match is the doubtful one (usually a competitor's
    site found through a shared town name)."""
    host = site_host(url)
    if not host:
        return False
    return conn.execute(
        """select 1 from companies
           where id <> %s and website is not null
             and lower(split_part(regexp_replace(website, '^https?://(www\\.)?', '', 'i'), '/', 1)) = %s
           limit 1""",
        (company_id, host),
    ).fetchone() is not None
