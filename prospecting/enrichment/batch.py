"""Website enrichment at scale: concurrent across sites, cached on disk so
re-runs (and crashes halfway through thousands of sites) don't refetch.

Each worker thread gets its own WebsiteEnrichmentProvider (own session,
robots cache and rate limiter), and each lead is one site, so any single
host still sees at most ~2 requests/second.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from prospecting.enrichment.website import WebsiteEnrichmentProvider


def _load_cache(path: Path | None) -> dict[str, dict]:
    cache: dict[str, dict] = {}
    if path and path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                cache[entry["website"]] = entry["result"]
    return cache


def enrich_websites(
    leads: list[dict],
    user_agent: str,
    workers: int = 8,
    cache_path: Path | None = None,
    on_progress=None,
) -> list[dict]:
    cache = _load_cache(cache_path)
    websites = sorted({
        lead["website"].strip() for lead in leads
        if isinstance(lead.get("website"), str) and lead["website"].strip()
        and not lead.get("duplicate_of") and not lead.get("website_status")
    })
    todo = [w for w in websites if w not in cache]

    local = threading.local()
    lock = threading.Lock()

    def enrich_one(website: str) -> tuple[str, dict]:
        if not hasattr(local, "provider"):
            local.provider = WebsiteEnrichmentProvider(user_agent=user_agent)
        fetched_at = datetime.now(timezone.utc).isoformat()
        try:
            result = local.provider.enrich({"website": website})
        except Exception as exc:  # one malformed site must not kill a multi-hour batch
            result = {"website_status": "error", "website_error": type(exc).__name__}
        return website, {**result, "website_fetched_at": fetched_at}

    cache_file = cache_path.open("a", encoding="utf-8") if cache_path else None
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(enrich_one, w) for w in todo]
            for done, future in enumerate(as_completed(futures), start=1):
                website, result = future.result()
                with lock:
                    cache[website] = result
                    if cache_file:
                        cache_file.write(json.dumps({"website": website, "result": result}) + "\n")
                        cache_file.flush()
                if on_progress:
                    on_progress(done, len(todo))
    finally:
        if cache_file:
            cache_file.close()

    enriched = []
    for lead in leads:
        if lead.get("website_status"):  # already fetched (e.g. by the domain finder)
            enriched.append(lead)
            continue
        website = lead.get("website").strip() if isinstance(lead.get("website"), str) else None
        result = dict(cache.get(website) or {})
        if lead.get("email"):
            result.pop("email", None)
            result.pop("email_source", None)
        if lead.get("phone"):
            result.pop("phone", None)
            result.pop("phone_source", None)
        enriched.append({**lead, **result, "enriched": bool(result)})
    return enriched
