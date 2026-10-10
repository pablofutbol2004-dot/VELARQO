"""Free enrichment from a lead's own website: emails, page title, visible
text (fed into scoring and copy). Fetches the homepage, plus the contact
page if the homepage has no same-domain email.

Only fetches what robots.txt allows for our User-Agent, identifies itself
honestly, and rate-limits. This is reading a business's own public
contact details from its own site - not scraping a directory/aggregator.
"""

import re
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

from lib.normalization.normalize import normalize_email
from lib.rate_limiter import RateLimiter
from lib.scoring.matching import FREEMAIL_DOMAINS

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_JUNK_EMAIL_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js")
_JUNK_EMAIL_DOMAINS = {"example.com", "domain.com", "yourdomain.com", "email.com", "sentry.io", "wixpress.com"}
_PREFERRED_LOCAL_PARTS = ["info", "enquiries", "enquiry", "sales", "hello", "contact", "office", "admin"]
_CONTACT_LINK_HINTS = ("contact", "get-in-touch", "getintouch", "enquir")
# Tried in order, at most _MAX_EXTRA_PAGES, only while no same-domain email is found.
_FALLBACK_PATHS = ("/contact", "/contact-us", "/about", "/about-us")
_MAX_EXTRA_PAGES = 2
# Signs the installer pays for enquiries: ad tracking tags in the page code,
# or links to paid lead/directory sites. A tag means the advertiser set up
# tracking, not that an ad is live today; tags hidden inside Google Tag
# Manager are not visible, so a missing tag proves nothing.
_AD_TAG_PATTERNS = {
    "meta_pixel": re.compile(r"connect\.facebook\.net/[^\"']*fbevents|fbq\(\s*['\"]init|facebook\.com/tr\?", re.I),
    "google_ads": re.compile(r"googleadservices\.com|googleads\.g\.doubleclick\.net|['\"]AW-\d{6,}", re.I),
    "checkatrade": re.compile(r"checkatrade\.com", re.I),
    "mybuilder": re.compile(r"mybuilder\.com", re.I),
    "ratedpeople": re.compile(r"ratedpeople\.com", re.I),
    "trustatrader": re.compile(r"trustatrader\.com", re.I),
    "bark": re.compile(r"\bbark\.com", re.I),
}
_MAX_TEXT_CHARS = 6000
_BLOCKED_STATUS_CODES = {401, 403, 429, 503}


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta_description = ""
        self.text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.mailtos: set[str] = set()
        self.cf_encoded: set[str] = set()
        self.ad_tags: set[str] = set()
        self._skip_depth = 0
        self._in_script = False
        self._in_title = False
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("data-cfemail"):
            self.cf_encoded.add(attrs["data-cfemail"])
        href = (attrs.get("href") or "") if tag == "a" else ""
        if "/cdn-cgi/l/email-protection#" in href:
            self.cf_encoded.add(href.rsplit("#", 1)[1])
        self._scan_ad_tags(" ".join(v for k, v in attrs.items() if k in ("src", "href") and v))
        if tag in ("script", "style", "noscript", "svg"):
            self._skip_depth += 1
            self._in_script = tag == "script"
        elif tag == "title":
            self._in_title = True
        elif tag == "meta" and (attrs.get("name") or "").lower() == "description":
            self.meta_description = attrs.get("content") or ""
        elif tag == "a" and attrs.get("href"):
            href = attrs["href"].strip()
            if href.lower().startswith("mailto:"):
                self.mailtos.add(href[7:].split("?")[0])
            else:
                self._anchor_href, self._anchor_text = href, []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self._skip_depth:
            self._skip_depth -= 1
            self._in_script = False
        elif tag == "title":
            self._in_title = False
        elif tag == "a" and self._anchor_href:
            self.links.append((self._anchor_href, " ".join(self._anchor_text)))
            self._anchor_href = None

    def _scan_ad_tags(self, code: str):
        if code:
            self.ad_tags |= {name for name, pattern in _AD_TAG_PATTERNS.items() if pattern.search(code)}

    def handle_data(self, data):
        if self._in_script:
            self._scan_ad_tags(data)
        if self._skip_depth:
            return
        if self._in_title:
            self.title += data
            return
        text = data.strip()
        if text:
            self.text_parts.append(text)
            if self._anchor_href:
                self._anchor_text.append(text)

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


def _candidate_urls(website: str) -> list[str]:
    """URLs to try in order. Found live: schemeless OSM websites that only
    work over http (broken https cert), and deep links that now 404 while
    the homepage is fine."""
    website = website.strip()
    if not website:
        return []
    urls = [website] if "://" in website else [f"https://{website}", f"http://{website}"]
    for url in list(urls):
        parsed = urlparse(url)
        if not parsed.hostname:
            return []
        if parsed.path not in ("", "/"):
            urls.append(f"{parsed.scheme}://{parsed.netloc}/")
    return list(dict.fromkeys(urls))


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


# Spaces are only allowed around bracketed/word markers, never around a
# real "." - otherwise "acme.co.uk. Meet us" swallows the next sentence.
_AT = r"(?:\s*@\s*|\s*\[at\]\s*|\s*\(at\)\s*|\s*\{at\}\s*|\s+at\s+)"
_DOT = r"(?:\.|\s*\[dot\]\s*|\s*\(dot\)\s*|\s*\{dot\}\s*|\s+dot\s+)"
_OBFUSCATED_RE = re.compile(
    rf"([A-Za-z0-9._%+-]+){_AT}([A-Za-z0-9-]+(?:{_DOT}[A-Za-z0-9-]+)*{_DOT}[A-Za-z]{{2,}})", re.IGNORECASE
)
_DOT_SPLIT_RE = re.compile(_DOT, re.IGNORECASE)


def decode_cfemail(encoded: str) -> str | None:
    """Cloudflare email protection: hex string, first byte is the XOR key."""
    try:
        data = bytes.fromhex(encoded)
        return "".join(chr(b ^ data[0]) for b in data[1:]) if len(data) > 1 else None
    except ValueError:
        return None


def _deobfuscate(text: str) -> set[str]:
    """'info [at] acme [dot] co [dot] uk' -> 'info@acme.co.uk'. Only matches
    when an explicit at-marker is present, so ordinary prose is left alone."""
    found = set()
    for local, domain in _OBFUSCATED_RE.findall(text):
        if "@" in f"{local}{domain}":
            continue
        found.add(f"{local}@{'.'.join(_DOT_SPLIT_RE.split(domain))}")
    return found


def _extract_emails(page: _PageParser) -> set[str]:
    candidates = set(page.mailtos) | set(_EMAIL_RE.findall(page.text)) | _deobfuscate(page.text)
    candidates |= {e for e in (decode_cfemail(x) for x in page.cf_encoded) if e}
    emails = set()
    for candidate in candidates:
        email = normalize_email(candidate)
        if not email or email.endswith(_JUNK_EMAIL_SUFFIXES):
            continue
        if email.split("@", 1)[1] in _JUNK_EMAIL_DOMAINS:
            continue
        emails.add(email)
    return emails


# Website builders and blog hosts: a site at acme.wordpress.com doesn't make
# x@wordpress.com the company's address.
_HOSTING_PLATFORMS = ("wordpress.com", "wixsite.com", "wix.com", "blogspot.com", "squarespace.com", "weebly.com",
                      "godaddysites.com", "webs.com", "jimdo.com", "site123.me", "yolasite.com", "business.site")


def _is_same_domain(email: str, site_domain: str) -> bool:
    domain = email.split("@", 1)[1]
    if domain in _HOSTING_PLATFORMS:
        return False
    return domain == site_domain or domain.endswith(f".{site_domain}") or site_domain.endswith(f".{domain}")


def pick_best_email(emails: set[str], site_domain: str) -> str | None:
    """Same-domain addresses first (preferring generic inboxes like info@),
    then freemail (small trades often use gmail). Other domains are skipped:
    those are usually the web designer's footer credit, not the business."""
    def rank(email: str) -> tuple[int, int, str]:
        local = email.split("@", 1)[0]
        preference = _PREFERRED_LOCAL_PARTS.index(local) if local in _PREFERRED_LOCAL_PARTS else len(_PREFERRED_LOCAL_PARTS)
        return (0 if _is_same_domain(email, site_domain) else 1), preference, email

    usable = [e for e in emails if _is_same_domain(e, site_domain) or e.split("@", 1)[1] in FREEMAIL_DOMAINS]
    return min(usable, key=rank) if usable else None


def _find_contact_url(links: list[tuple[str, str]], base_url: str) -> str | None:
    base_host = _host(base_url)
    for href, text in links:
        haystack = f"{href} {text}".lower()
        if any(hint in haystack for hint in _CONTACT_LINK_HINTS):
            url = urljoin(base_url, href)
            if _host(url) == base_host and url.startswith(("http://", "https://")):
                return url
    return None


class WebsiteEnrichmentProvider:
    def __init__(
        self,
        user_agent: str,
        session: requests.Session | None = None,
        rate_limiter: RateLimiter | None = None,
        timeout: float = 10.0,
        fetch_contact_page: bool = True,
    ):
        self.user_agent = user_agent
        self.session = session or requests.Session()
        self.rate_limiter = rate_limiter or RateLimiter(max_requests=2, window_seconds=1.0)
        self.timeout = timeout
        self.fetch_contact_page = fetch_contact_page
        self._robots: dict[str, RobotFileParser | None] = {}
        self._last_failure: str | None = None

    def _get(self, url: str) -> requests.Response | None:
        self.rate_limiter.acquire()
        try:
            response = self.session.get(
                url,
                headers={"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"},
                timeout=self.timeout,
                allow_redirects=True,
            )
        except requests.RequestException:
            self._last_failure = "unreachable"
            return None
        if response.status_code in _BLOCKED_STATUS_CODES:
            # Bot protection/rate limiting: the site is up, we're just not
            # welcome. Not a sign the business closed, and not something to bypass.
            self._last_failure = "blocked"
            return None
        if response.status_code >= 400:
            self._last_failure = "unreachable"
            return None
        return response

    def _allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots:
            response = self._get(f"{origin}/robots.txt")
            if response is None:
                self._robots[origin] = None  # no robots.txt (or unreachable) = no restrictions
            else:
                parser = RobotFileParser()
                parser.parse(response.text.splitlines())
                self._robots[origin] = parser
        parser = self._robots[origin]
        return parser is None or parser.can_fetch(self.user_agent, url)

    def _fetch_page(self, url: str) -> tuple[_PageParser, str] | None:
        if not self._allowed(url):
            return None
        self._last_failure = None
        response = self._get(url)
        if response is None:
            return None
        if "html" not in response.headers.get("Content-Type", "html").lower():
            self._last_failure = "unreachable"
            return None
        page = _PageParser()
        try:
            page.feed(response.text)
        except Exception:
            return None
        return page, getattr(response, "url", url) or url

    def enrich(self, lead: dict) -> dict:
        website = lead.get("website")
        candidates = _candidate_urls(website) if isinstance(website, str) else []
        if not candidates:
            return {}

        fetched = None
        failures = set()
        for url in candidates:
            if not self._allowed(url):
                failures.add("robots_disallowed")
                continue
            if fetched := self._fetch_page(url):
                break
            failures.add(self._last_failure or "unreachable")
        if fetched is None:
            status = next(s for s in ("robots_disallowed", "blocked", "unreachable") if s in failures)
            return {"website_status": status}
        home, final_url = fetched
        site_domain = _host(final_url)

        emails = _extract_emails(home)
        texts = [home.meta_description, home.text]

        if self.fetch_contact_page and not any(_is_same_domain(e, site_domain) for e in emails):
            contact_url = _find_contact_url(home.links, final_url)
            if contact_url and (contact := self._fetch_page(contact_url)):
                contact_page, _ = contact
                emails |= _extract_emails(contact_page)
                texts.append(contact_page.text)

        tried = 0
        for path in _FALLBACK_PATHS:
            if not self.fetch_contact_page or tried >= _MAX_EXTRA_PAGES or any(_is_same_domain(e, site_domain) for e in emails):
                break
            url = urljoin(final_url, path)
            if url.rstrip("/") == final_url.rstrip("/"):
                continue
            tried += 1
            if extra := self._fetch_page(url):
                extra_page, _ = extra
                emails |= _extract_emails(extra_page)
                texts.append(extra_page.text)

        result = {
            "website_status": "ok",
            "website_title": re.sub(r"\s+", " ", home.title.replace("\x00", "")).strip() or None,
            # Postgres text can't hold NUL bytes; a few sites have them.
            "website_text": " ".join(t for t in texts if t).replace("\x00", "")[:_MAX_TEXT_CHARS],
            "emails_found": sorted(emails),
            "ad_tags": sorted(home.ad_tags),
        }
        best = pick_best_email(emails, site_domain)
        if best and not lead.get("email"):
            result["email"] = best
            result["email_source"] = "website"
        return result
