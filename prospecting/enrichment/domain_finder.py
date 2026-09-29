"""Find a company's website when no source lists one, by guessing domains
from its name and verifying the site is really that company.

"Halewood Windows Ltd" -> halewoodwindows.co.uk, halewood-windows.co.uk,
halewoodwindows.com, ... Each candidate must resolve in DNS, load, not be
a parked/for-sale page, and mention the company:
- names with a distinctive word ("Halewood") must show that word;
- generic names ("Premier Windows") must show the full name AND the
  company's town or postcode district - otherwise it's likely a different
  firm with the same generic name, and the guess is rejected.

Free and slow-ish: nothing is fetched until DNS says the domain exists.
"""

import json
import socket
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from lib.scoring.matching import find_terms, normalize_text
from prospecting.deduplication.merge import match_name
from prospecting.enrichment.website import WebsiteEnrichmentProvider

_TLDS = ("co.uk", "com", "uk")
# Phrases, not brand names: a real installer's footer can say "hosted by
# GoDaddy", and "coming soon" can be a new product range.
_PARKED_MARKERS = [
    "domain is for sale", "buy this domain", "this domain may be for sale", "domain parking",
    "parked free", "hugedomains", "future home of", "website coming soon", "site coming soon",
    "website under construction", "account suspended",
]
# Words that don't identify a company on their own.
_GENERIC_WORDS = {
    "and", "the", "of", "uk", "gb", "home", "homes", "house", "improvements", "services", "service",
    "solutions", "systems", "installations", "installation", "installers", "trade", "group", "company",
    "direct", "centre", "center", "north", "south", "east", "west", "northern", "southern", "central",
    "premier", "quality", "global", "national", "local", "city", "county", "professional", "express",
    "first", "best", "top", "prime", "elite", "star", "pro", "one", "a1", "ace",
}


def _is_generic(word: str, vertical_terms: list[str]) -> bool:
    return word in _GENERIC_WORDS or len(word) <= 2 or bool(find_terms(word, vertical_terms))


def candidate_domains(company_name: str) -> list[str]:
    words = match_name(company_name).split()
    if not words:
        return []
    joined = "".join(words)
    if len(joined) < 5:
        return []
    labels = [joined, "-".join(words), f"{joined}ltd"]
    without_and = [w for w in words if w != "and"]
    if len(without_and) != len(words):
        labels.append("".join(without_and))
    labels = [l for l in dict.fromkeys(labels) if len(l) <= 63]
    return [f"{label}.{tld}" for label in labels for tld in _TLDS]


def _resolves(domain: str) -> bool:
    try:
        socket.getaddrinfo(domain, 443, proto=socket.IPPROTO_TCP)
        return True
    except (socket.gaierror, UnicodeError, OSError):
        return False


def verify_site(lead: dict, site: dict, vertical_terms: list[str]) -> str | None:
    """'high' / 'medium' confidence that this fetched site is this company, or None."""
    if site.get("website_status") != "ok":
        return None
    text = f"{site.get('website_title') or ''} {site.get('website_text') or ''}"
    normalized = f" {normalize_text(text)} "
    if any(f" {normalize_text(m)} " in normalized for m in _PARKED_MARKERS):
        return None

    words = match_name(lead.get("company_name")).split()
    distinctive = [w for w in words if not _is_generic(w, vertical_terms)]
    district = str(lead.get("postcode") or "").upper().split(" ")[0]
    town = normalize_text(lead.get("city"))
    local = (district and district.lower() in normalized.split()) or (town and f" {town} " in normalized)

    if distinctive:
        if not all(f" {w} " in normalized for w in distinctive):
            return None
        return "high" if local or len(distinctive) >= 2 else "medium"

    full_name = " ".join(words)
    if f" {full_name} " in normalized and local:
        return "medium"
    return None


class DomainFinder:
    def __init__(self, user_agent: str, vertical_terms: list[str], resolve=_resolves, provider: WebsiteEnrichmentProvider | None = None):
        self.vertical_terms = vertical_terms
        self._resolve = resolve
        self._provider = provider or WebsiteEnrichmentProvider(user_agent=user_agent, fetch_contact_page=True)

    def find(self, lead: dict) -> dict:
        tried = []
        for domain in candidate_domains(lead.get("legal_name") or lead.get("company_name") or ""):
            if not self._resolve(domain):
                continue
            tried.append(domain)
            site = self._provider.enrich({"website": domain})
            confidence = verify_site(lead, site, self.vertical_terms)
            if confidence:
                return {
                    **site,
                    "website": f"https://{domain}",
                    "website_source": "domain_guess",
                    "website_confidence": confidence,
                    "domains_tried": tried,
                }
        return {"domains_tried": tried} if tried else {}


def _cache_key(lead: dict) -> str:
    return lead.get("company_number") or f"{match_name(lead.get('company_name'))}|{lead.get('postcode') or ''}"


def find_websites(
    leads: list[dict],
    user_agent: str,
    vertical_terms: list[str],
    workers: int = 16,
    cache_path: Path | None = None,
    on_progress=None,
) -> list[dict]:
    """Runs DomainFinder for every lead that has no website yet. One finder
    per worker thread (each has its own session/robots cache). Results -
    including "nothing found" - are cached on disk, so an interrupted run
    resumes where it stopped and re-runs don't repeat the work."""
    cache: dict[str, dict] = {}
    if cache_path and cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                cache[entry["key"]] = entry["found"]

    todo = [
        i for i, lead in enumerate(leads)
        if not lead.get("website") and not lead.get("duplicate_of") and _cache_key(lead) not in cache
    ]
    finders: dict[int, DomainFinder] = {}
    lock = threading.Lock()

    def run(i: int) -> tuple[int, dict]:
        key = threading.get_ident()
        if key not in finders:
            finders[key] = DomainFinder(user_agent, vertical_terms)
        try:
            return i, finders[key].find(leads[i])
        except Exception as exc:  # one odd company must not stop a 12k-lead batch
            return i, {"domain_finder_error": type(exc).__name__}

    cache_file = cache_path.open("a", encoding="utf-8") if cache_path else None
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for done, (i, found) in enumerate(pool.map(run, todo), start=1):
                with lock:
                    cache[_cache_key(leads[i])] = found
                    if cache_file:
                        cache_file.write(json.dumps({"key": _cache_key(leads[i]), "found": found}) + "\n")
                        cache_file.flush()
                if on_progress and (done % 250 == 0 or done == len(todo)):
                    on_progress(done, len(todo))
    finally:
        if cache_file:
            cache_file.close()

    results = []
    for lead in leads:
        found = dict(cache.get(_cache_key(lead)) or {}) if not lead.get("website") else {}
        email = found.pop("email", None)
        found.pop("email_source", None)
        merged = {**lead, **found}
        if email and not lead.get("email"):
            merged["email"] = email
            merged["email_source"] = "website"
        results.append(merged)
    return results
