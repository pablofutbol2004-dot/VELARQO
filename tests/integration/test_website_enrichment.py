from lib.rate_limiter import RateLimiter
from prospecting.enrichment.website import WebsiteEnrichmentProvider, pick_best_email


class FakeResponse:
    def __init__(self, text, status_code=200, content_type="text/html; charset=utf-8", url=None):
        self.text = text
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self.url = url


class FakeSession:
    def __init__(self, pages: dict[str, FakeResponse]):
        self.pages = pages
        self.requested = []

    def get(self, url, headers=None, timeout=None, allow_redirects=True):
        self.requested.append(url)
        response = self.pages.get(url)
        if response is None:
            return FakeResponse("", status_code=404)
        response.url = response.url or url
        return response


def _provider(pages):
    session = FakeSession(pages)
    provider = WebsiteEnrichmentProvider(
        user_agent="velarqo-test/0.1",
        session=session,
        rate_limiter=RateLimiter(clock=lambda: 0.0, sleep=lambda _: None),
    )
    return provider, session


HOME_WITH_EMAIL = """
<html><head><title>Acme Windows | uPVC Windows Manchester</title>
<meta name="description" content="Double glazing installers since 1998"></head>
<body><script>var x = "not@visible.com";</script>
<p>Contact us: sales@acmewindows.co.uk or <a href="mailto:info@acmewindows.co.uk">email</a></p>
<footer>Website by <a href="https://webco.com">WebCo</a> - hello@webco.com</footer>
</body></html>
"""

HOME_NO_EMAIL = """
<html><head><title>Bee Glazing</title></head>
<body><p>FENSA registered glaziers.</p><a href="/get-in-touch">Contact Us</a></body></html>
"""

CONTACT_PAGE = "<html><body><p>Email: enquiries@beeglazing.co.uk</p></body></html>"


def test_extracts_same_domain_email_preferring_info():
    provider, _ = _provider({"https://acmewindows.co.uk": FakeResponse(HOME_WITH_EMAIL)})
    result = provider.enrich({"website": "acmewindows.co.uk"})

    assert result["website_status"] == "ok"
    assert result["email"] == "info@acmewindows.co.uk"
    assert result["email_source"] == "website"
    assert "Double glazing installers" in result["website_text"]
    assert "not@visible.com" not in result["website_text"]
    assert result["website_title"] == "Acme Windows | uPVC Windows Manchester"


def test_ignores_web_designer_email_on_another_domain():
    assert pick_best_email({"hello@webco.com"}, "acmewindows.co.uk") is None
    assert pick_best_email({"hello@webco.com", "bob@gmail.com"}, "acmewindows.co.uk") == "bob@gmail.com"


def test_follows_contact_page_when_homepage_has_no_email():
    provider, session = _provider({
        "https://beeglazing.co.uk": FakeResponse(HOME_NO_EMAIL),
        "https://beeglazing.co.uk/get-in-touch": FakeResponse(CONTACT_PAGE),
    })
    result = provider.enrich({"website": "https://beeglazing.co.uk"})

    assert result["email"] == "enquiries@beeglazing.co.uk"
    assert "https://beeglazing.co.uk/get-in-touch" in session.requested


def test_respects_robots_txt():
    provider, session = _provider({
        "https://private.co.uk/robots.txt": FakeResponse("User-agent: *\nDisallow: /", content_type="text/plain"),
        "https://private.co.uk": FakeResponse(HOME_WITH_EMAIL),
    })
    result = provider.enrich({"website": "https://private.co.uk"})

    assert result == {"website_status": "robots_disallowed"}
    assert "https://private.co.uk" not in session.requested


def test_does_not_overwrite_existing_email():
    provider, _ = _provider({"https://acmewindows.co.uk": FakeResponse(HOME_WITH_EMAIL)})
    result = provider.enrich({"website": "acmewindows.co.uk", "email": "owner@acmewindows.co.uk"})

    assert "email" not in result
    assert "info@acmewindows.co.uk" in result["emails_found"]


def test_falls_back_to_http_when_schemeless_https_fails():
    # Found live: warmseal.co.uk / repglass.com have broken https certs.
    provider, session = _provider({"http://acmewindows.co.uk": FakeResponse(HOME_WITH_EMAIL)})
    result = provider.enrich({"website": "acmewindows.co.uk"})

    assert result["email"] == "info@acmewindows.co.uk"
    assert session.requested.index("https://acmewindows.co.uk") < session.requested.index("http://acmewindows.co.uk")


def test_falls_back_to_homepage_when_deep_link_is_dead():
    # Found live: an OSM website pointing at a /leeds-windowrepair/ page that now 404s.
    provider, _ = _provider({"https://acmewindows.co.uk/": FakeResponse(HOME_WITH_EMAIL)})
    result = provider.enrich({"website": "https://acmewindows.co.uk/old-landing-page/"})

    assert result["website_status"] == "ok"
    assert result["email"] == "info@acmewindows.co.uk"


def test_bot_protected_site_is_blocked_not_dead():
    # Found live: seal-lite.co.uk returns 403. Up, just not welcoming bots.
    provider, _ = _provider({"https://guarded.co.uk": FakeResponse("denied", status_code=403)})
    assert provider.enrich({"website": "https://guarded.co.uk"}) == {"website_status": "blocked"}


def test_unreachable_site_and_no_website():
    provider, _ = _provider({})
    assert provider.enrich({"website": "https://down.co.uk"}) == {"website_status": "unreachable"}
    assert provider.enrich({"website": None}) == {}
