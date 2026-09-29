from prospecting.enrichment.domain_finder import DomainFinder, candidate_domains, verify_site

VERTICAL = ["window", "glazing", "glazier", "door", "glass", "frame", "upvc", "double glazing"]


def _site(text, title=""):
    return {"website_status": "ok", "website_title": title, "website_text": text}


def test_candidate_domains():
    domains = candidate_domains("HALEWOOD WINDOWS LIMITED")
    assert domains[:3] == ["halewoodwindows.co.uk", "halewoodwindows.com", "halewoodwindows.uk"]
    assert "halewood-windows.co.uk" in domains
    assert "halewoodwindowsltd.co.uk" in domains
    assert "adglass.co.uk" in candidate_domains("A & D GLASS LTD")
    assert candidate_domains("AB LTD") == []


def test_distinctive_name_must_appear():
    lead = {"company_name": "HALEWOOD WINDOWS LIMITED", "postcode": "L25 9QA", "city": "Liverpool"}
    assert verify_site(lead, _site("Halewood Windows - uPVC installers in Liverpool"), VERTICAL) == "high"
    assert verify_site(lead, _site("Halewood Windows - family run installers"), VERTICAL) == "medium"
    assert verify_site(lead, _site("Other Windows Ltd, Liverpool"), VERTICAL) is None


def test_generic_name_needs_location_to_count():
    lead = {"company_name": "PREMIER WINDOWS LTD", "postcode": "LS1 1AA", "city": "Leeds"}
    assert verify_site(lead, _site("Premier Windows, serving Leeds since 1990"), VERTICAL) == "medium"
    assert verify_site(lead, _site("Premier Windows, serving Bristol since 1990"), VERTICAL) is None


def test_parked_pages_rejected():
    lead = {"company_name": "HALEWOOD WINDOWS LIMITED"}
    assert verify_site(lead, _site("halewoodwindows.co.uk - this domain may be for sale"), VERTICAL) is None
    assert verify_site({"company_name": "X"}, {"website_status": "unreachable"}, VERTICAL) is None


class FakeProvider:
    def __init__(self, sites):
        self.sites = sites

    def enrich(self, lead):
        return self.sites.get(lead["website"], {"website_status": "unreachable"})


def test_finder_skips_unresolvable_and_returns_first_verified():
    lead = {"company_name": "HALEWOOD WINDOWS LIMITED", "city": "Liverpool"}
    finder = DomainFinder(
        "test",
        VERTICAL,
        resolve=lambda d: d in {"halewoodwindows.com", "halewood-windows.co.uk"},
        provider=FakeProvider({
            "halewoodwindows.com": _site("Buy this domain today"),
            "halewood-windows.co.uk": {**_site("Halewood Windows Liverpool"), "email": "info@halewood-windows.co.uk"},
        }),
    )
    found = finder.find(lead)

    assert found["website"] == "https://halewood-windows.co.uk"
    assert found["website_confidence"] == "high"
    assert found["website_source"] == "domain_guess"
    assert found["domains_tried"] == ["halewoodwindows.com", "halewood-windows.co.uk"]
