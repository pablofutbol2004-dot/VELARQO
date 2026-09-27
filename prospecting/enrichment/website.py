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
_MAX_TEXT_CHARS = 6000


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta_description = ""
        self.text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.mailtos: set[str] = set()
        self._skip_depth = 0
        self._in_title = False
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "noscript", "svg"):
            self._skip_depth += 1
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
        elif tag == "title":
            self._in_title = False
        elif tag == "a" and self._anchor_href:
            self.links.append((self._anchor_href, " ".join(self._anchor_text)))
            self._anchor_href = None

    def handle_data(self, data):
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


def _normalize_url(website: str) -> str | None:
    website = website.strip()
    if not website:
        return None
    url = website if "://" in website else f"https://{website}"
    parsed = urlparse(url)
    return url if parsed.hostname else None


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def _extract_emails(page: _PageParser) -> set[str]:
    candidates = set(page.mailtos) | set(_EMAIL_RE.findall(page.text))
    emails = set()
    for candidate in candidates:
        email = normalize_email(candidate)
        if not email or email.endswith(_JUNK_EMAIL_SUFFIXES):
            continue
        if email.split("@", 1)[1] in _JUNK_EMAIL_DOMAINS:
            continue
        emails.add(email)
    return emails


def _is_same_domain(email: str, site_domain: str) -> bool:
    domain = email.split("@", 1)[1]
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
            return None
        if response.status_code >= 400:
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
        response = self._get(url)
        if response is None or "html" not in response.headers.get("Content-Type", "html").lower():
            return None
        page = _PageParser()
        try:
            page.feed(response.text)
        except Exception:
            return None
        return page, getattr(response, "url", url) or url

    def enrich(self, lead: dict) -> dict:
        website = lead.get("website")
        base_url = _normalize_url(website) if isinstance(website, str) else None
        if not base_url:
            return {}

        if not self._allowed(base_url):
            return {"website_status": "robots_disallowed"}

        fetched = self._fetch_page(base_url)
        if fetched is None:
            return {"website_status": "unreachable"}
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

        result = {
            "website_status": "ok",
            "website_title": re.sub(r"\s+", " ", home.title).strip() or None,
            "website_text": " ".join(t for t in texts if t)[:_MAX_TEXT_CHARS],
            "emails_found": sorted(emails),
        }
        best = pick_best_email(emails, site_domain)
        if best and not lead.get("email"):
            result["email"] = best
            result["email_source"] = "website"
        return result
