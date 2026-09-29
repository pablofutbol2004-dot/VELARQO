"""Cross-source entity resolution: collapse records that are the same
business into one merged lead, combining each source's strengths.

OSM gives trading premises + website/phone; Companies House gives legal
name, company number, SIC codes, size band - but its address is the
registered office, often an accountant in another town. So matching can't
rely on postcode alone:

1. Same normalized name + same postcode district (or same town) -> same business.
2. Same normalized name, different places, but the name appears exactly
   once in each source -> same business (confidence "name").
   A name that appears several times in one source ("Premier Windows") is
   never merged on name alone - those are usually different firms.
3. Different but near-identical names in the same postcode district
   (token_sort_ratio >= 92) -> same business ("Acme Windows" vs
   "Acme Windows & Doors" does NOT reach this; typo-level variants do).
"""

import re
from collections import defaultdict

from rapidfuzz import fuzz

_LEGAL_SUFFIXES = re.compile(r"\b(ltd|limited|plc|llp|lp|cic|co|company|uk|group|the)\b")
_ACRONYMS = {"Uk": "UK", "Upvc": "uPVC", "Pvc": "PVC", "Pvcu": "PVCu", "Gb": "GB", "Ni": "NI", "Diy": "DIY"}
FUZZY_THRESHOLD = 92

# Which source wins per field when both have a value.
_PREFER_OSM = ("display_name", "website", "email", "phone", "postcode", "address", "city", "lat", "lon", "osm_category", "brand", "osm_id")
_PREFER_CH = ("company_number", "sic_codes", "incorporation_date", "accounts_category", "company_category", "legal_name")


def match_name(name: str) -> str:
    text = str(name or "").lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = _LEGAL_SUFFIXES.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def tidy_display_name(name: str) -> str:
    """'HALEWOOD WINDOWS LIMITED' -> 'Halewood Windows'. Leaves mixed-case
    names (already human-written, e.g. from OSM) alone apart from spacing."""
    name = re.sub(r"\s+", " ", str(name or "")).strip()
    if name.isupper():
        name = re.sub(r"\s+(limited|ltd\.?|plc|llp)$", "", name, flags=re.IGNORECASE)
        name = " ".join(_ACRONYMS.get(w, w) for w in name.title().split())
    return name


def _district(postcode) -> str | None:
    """Outward code: 'SW1A 1AA' -> 'SW1A'. Unspaced full postcodes lose the
    3-char inward code; anything shorter can't be trusted."""
    postcode = str(postcode or "").strip().upper()
    if " " in postcode:
        return postcode.split()[0]
    if len(postcode) >= 5:
        return postcode[:-3]
    return None


def _town(lead: dict) -> str | None:
    return str(lead.get("city") or "").strip().lower() or None


def _source(lead: dict) -> str:
    return "companies_house" if lead.get("lead_source") == "companies_house" else "osm"


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, a: int, b: int) -> None:
        self.parent[self.find(a)] = self.find(b)


def _same_place(a: dict, b: dict) -> bool:
    district_a, district_b = _district(a.get("postcode")), _district(b.get("postcode"))
    if district_a and district_b:
        return district_a == district_b
    town_a, town_b = _town(a), _town(b)
    return bool(town_a and town_b and town_a == town_b)


def _merge_cluster(records: list[dict], confidence: str) -> dict:
    osm = [r for r in records if _source(r) == "osm"]
    ch = [r for r in records if _source(r) == "companies_house"]
    merged: dict = {}
    for record in [*ch, *osm]:  # later sources fill gaps only
        for key, value in record.items():
            if value not in (None, "") and merged.get(key) in (None, ""):
                merged[key] = value

    for field in _PREFER_OSM:
        if value := next((r.get(field) for r in osm if r.get(field) not in (None, "")), None):
            merged[field] = value
    for field in _PREFER_CH:
        if value := next((r.get(field) for r in ch if r.get(field) not in (None, "")), None):
            merged[field] = value

    sources = sorted({_source(r) for r in records})
    merged["lead_source"] = "+".join(sources)
    merged["sources"] = sources
    merged["merged_count"] = len(records)
    merged["merge_confidence"] = confidence if len(records) > 1 else None
    merged["osm_ids"] = [r["osm_id"] for r in osm if r.get("osm_id")]
    merged["company_numbers"] = [r["company_number"] for r in ch if r.get("company_number")]
    if ch and osm:
        merged["registered_postcode"] = ch[0].get("postcode")

    # Every contributing record, untouched, for the source_records table.
    merged["raw_sources"] = [
        {"source": "osm", "source_id": r.get("osm_id"), "payload": r.get("osm_tags") or {}}
        for r in osm if r.get("osm_id")
    ] + [
        {"source": "companies_house", "source_id": r.get("company_number"), "payload": r.get("ch_raw") or {}}
        for r in ch if r.get("company_number")
    ]
    merged.pop("osm_tags", None)
    merged.pop("ch_raw", None)
    return merged


def merge_sources(leads: list[dict]) -> list[dict]:
    for lead in leads:
        if _source(lead) == "companies_house":
            lead.setdefault("legal_name", lead.get("company_name"))
        lead.setdefault("display_name", tidy_display_name(lead.get("company_name")))

    keys = [match_name(lead.get("company_name")) for lead in leads]
    uf = _UnionFind(len(leads))
    confidence = ["" for _ in leads]

    by_name: dict[str, list[int]] = defaultdict(list)
    for i, key in enumerate(keys):
        if key:
            by_name[key].append(i)

    for indices in by_name.values():
        if len(indices) < 2:
            continue
        for x, i in enumerate(indices):
            for j in indices[x + 1:]:
                if _same_place(leads[i], leads[j]):
                    uf.union(i, j)
                    confidence[i] = confidence[j] = "name+place"
        per_source: dict[str, list[int]] = defaultdict(list)
        for i in indices:
            per_source[_source(leads[i])].append(i)
        if len(per_source) == 2 and all(len(v) == 1 for v in per_source.values()):
            i, j = per_source["osm"][0], per_source["companies_house"][0]
            if uf.find(i) != uf.find(j):
                uf.union(i, j)
                confidence[i] = confidence[j] = "name"

    by_district: dict[str, list[int]] = defaultdict(list)
    for i, lead in enumerate(leads):
        if district := _district(lead.get("postcode")):
            by_district[district].append(i)
    for indices in by_district.values():
        for x, i in enumerate(indices):
            for j in indices[x + 1:]:
                if uf.find(i) == uf.find(j) or not keys[i] or not keys[j] or keys[i] == keys[j]:
                    continue
                if fuzz.token_sort_ratio(keys[i], keys[j]) >= FUZZY_THRESHOLD:
                    uf.union(i, j)
                    confidence[i] = confidence[j] = confidence[i] or "fuzzy+place"

    clusters: dict[int, list[int]] = defaultdict(list)
    for i in range(len(leads)):
        clusters[uf.find(i)].append(i)

    merged = []
    for indices in clusters.values():
        levels = [confidence[i] for i in indices if confidence[i]]
        # weakest link decides the cluster's confidence
        order = ["name", "fuzzy+place", "name+place"]
        cluster_confidence = min(levels, key=order.index) if levels else "single"
        merged.append(_merge_cluster([leads[i] for i in indices], cluster_confidence))
    return merged
