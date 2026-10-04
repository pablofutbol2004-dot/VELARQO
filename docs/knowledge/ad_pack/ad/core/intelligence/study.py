"""Intelligence Loop A — the bounded workshop study.

One real pipeline that turns a small, honestly-labelled sample into evidence:

    sources → exclusion preflight → source policy → entity resolution
            → source artifacts → per-feature observations → teardown artifact
            → dataset artifact (explicit sample) → findings

Three disciplines keep it from manufacturing conclusions:

- **Presence as well as absence.** Every measured feature is recorded as present,
  absent, partial, unknown or unverifiable, so the dataset shows real variation
  and counterexamples instead of a universe made only of problems.
- **Capture limits are not business findings.** A page that was truncated, or
  that looks like a JavaScript shell, cannot support a claim that something is
  missing. Under those conditions an ``absent`` observation is recorded as
  ``unverifiable`` and excluded from the aggregate.
- **Absence is not causation.** Findings claim only what was observed on a page.
  ``claim_strength`` says so, and a causal claim is refused outright unless the
  evidence includes something behavioural.

The study proves the architecture; it does **not** claim statistical
representativeness. The sample definition is attached to the dataset artifact.

Reuse rather than rebuild: the control plane gates the run, the source policy
refuses what may not be collected, entity resolution joins sightings to
workshops, the artifact and intel stores persist everything, and web access goes
through the injected Zeus ``read_url`` surface. There is no new framework.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import re
import time
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum

import yaml
from pydantic import BaseModel, Field, model_validator

from kleos.actions import ActionKind
from kleos.artifacts import (
    ArtifactType,
    DatasetDefinition,
    content_hash,
    create_artifact,
    find_duplicates,
    list_artifacts,
)
from kleos.control import ActionDecision, ActionProposal, ControlPlane, Verdict
from kleos.domain import MainConstraint
from kleos.entities import Identity, get_entity, list_entities, resolve_workshop
from kleos.gate import propose
from kleos.intel import (
    ClaimStrength,
    Directness,
    EpistemicType,
    FeaturePresence,
    ItemType,
    Relation,
    add_edge,
    add_evidence,
    add_finding,
    get_item,
    list_items,
    refresh_health,
)
from kleos.jsoncalls import JSON_ATTEMPTS
from kleos.models import EvidenceLabel
from kleos.prompts import PromptRegistry, PromptTemplate
from kleos.review import ReviewItem, ReviewQueue
from kleos.source_policy import (
    SourceClass,
    SourcePolicy,
    SourcePolicyError,
    require_collection_allowed,
)
from kleos.trace import TraceActor, TraceEvent, TraceOutcome, TraceStore

TASK_CLASS = "normal"

#: Bump when the checklist or the observation model changes. It is part of the
#: resume key, so a new checklist re-inspects every source instead of reusing
#: observations recorded under the old one — and the old teardowns stay in the
#: store as the historical record of what the previous pass concluded.
CHECKLIST_VERSION = 2

#: Total model-input budget per source, and the portion reserved for the head of
#: the page before keyword windows are added.
MAX_SOURCE_CHARS = 8_000
HEAD_CHARS = 4_000
WINDOW_CHARS = 350

#: A page this short that also contains no contact marker at all is more likely a
#: JavaScript/template shell the fetcher could not render than a business with no
#: contact details. It is not evidence of absence.
SUSPECT_CAPTURE_CHARS = 2_500
_CONTACT_MARKERS = (
    "contacto",
    "contact",
    "teléfono",
    "telefono",
    "whatsapp",
    "mailto:",
    "formulario",
    "@",
    "cita",
    "presupuesto",
)

#: Words that hint a page region matters for this checklist; windows around them
#: are added to the excerpt so truncation does not hide contact or pricing.
_KEYWORD_WINDOWS = (
    "contacto",
    "teléfono",
    "telefono",
    "whatsapp",
    "presupuesto",
    "precio",
    "tarifa",
    "cita",
    "reserva",
    "horario",
    "email",
    "correo",
    "opiniones",
    "reseñas",
    "resenas",
    "trabajos",
    "galería",
    "galeria",
    "garantía",
    "garantia",
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SiteFeature(StrEnum):
    """The measured features. Named neutrally: each is measured as present,
    absent, partially present, unknown or unverifiable — not as a "leak"."""

    REPLY_PATH = "reply_path"
    RESPONSE_EVIDENCE = "response_evidence"
    ONLINE_BOOKING = "online_booking"
    PRICING_TRANSPARENCY = "pricing_transparency"
    TRUST_SIGNALS = "trust_signals"
    REVIEW_MANAGEMENT = "review_management"
    PROOF_OF_WORK = "proof_of_work"
    RETENTION_PATH = "retention_path"


#: The neutral question asked about each feature on each source.
FEATURE_QUESTION: dict[SiteFeature, str] = {
    SiteFeature.REPLY_PATH: "is there a visible way to make an enquiry (phone, form, email, WhatsApp)?",
    SiteFeature.RESPONSE_EVIDENCE: "is there anything showing how quickly they respond?",
    SiteFeature.ONLINE_BOOKING: "is there a way to book or request an appointment online?",
    SiteFeature.PRICING_TRANSPARENCY: "is any pricing, or an explanation of how quoting works, published?",
    SiteFeature.TRUST_SIGNALS: "is there anything that builds trust before contact (team photos, credentials, guarantees)?",
    SiteFeature.REVIEW_MANAGEMENT: "are customer reviews shown, and are any of them answered?",
    SiteFeature.PROOF_OF_WORK: "are examples of finished work or results shown?",
    SiteFeature.RETENTION_PATH: "is there anything aimed at bringing a customer back (follow-up, loyalty, rebooking)?",
}

#: How an absence of that feature reads in a finding. Deliberately phrased as
#: "the site did not visibly show", never as "the business lacks".
FEATURE_ABSENCE_LABEL: dict[SiteFeature, str] = {
    SiteFeature.REPLY_PATH: "any visible way to reply to an enquiry",
    SiteFeature.RESPONSE_EVIDENCE: "any indication of response speed",
    SiteFeature.ONLINE_BOOKING: "any way to book online",
    SiteFeature.PRICING_TRANSPARENCY: "any published pricing or quoting explanation",
    SiteFeature.TRUST_SIGNALS: "much that builds trust before contact",
    SiteFeature.REVIEW_MANAGEMENT: "any handling of customer reviews",
    SiteFeature.PROOF_OF_WORK: "any examples of finished work",
    SiteFeature.RETENTION_PATH: "anything aimed at bringing a customer back",
}

CONSTRAINT_BY_FEATURE: dict[SiteFeature, MainConstraint] = {
    SiteFeature.REPLY_PATH: MainConstraint.CONVERSION,
    SiteFeature.RESPONSE_EVIDENCE: MainConstraint.SERVICE_QUALITY,
    SiteFeature.ONLINE_BOOKING: MainConstraint.ADMIN,
    SiteFeature.PRICING_TRANSPARENCY: MainConstraint.CONVERSION,
    SiteFeature.TRUST_SIGNALS: MainConstraint.DEMAND,
    SiteFeature.REVIEW_MANAGEMENT: MainConstraint.SERVICE_QUALITY,
    SiteFeature.PROOF_OF_WORK: MainConstraint.DEMAND,
    SiteFeature.RETENTION_PATH: MainConstraint.RETENTION,
}

#: The artifact type a given source class lands as.
_ARTIFACT_TYPE_BY_SOURCE: dict[SourceClass, ArtifactType] = {
    SourceClass.PUBLIC_WEB: ArtifactType.WEBPAGE,
    SourceClass.PUBLIC_REVIEWS: ArtifactType.REVIEW_BATCH,
    SourceClass.PUBLIC_SOCIAL: ArtifactType.WEBPAGE,
    SourceClass.MANUAL_OBSERVATION: ArtifactType.NOTES,
    SourceClass.INDUSTRY_REPORT: ArtifactType.RESEARCH_REPORT,
    SourceClass.MODEL_RESEARCH: ArtifactType.RESEARCH_RESPONSE,
    SourceClass.OWN_CONVERSATION: ArtifactType.TRANSCRIPT,
    SourceClass.OWN_CONTENT: ArtifactType.CONTENT_RENDER,
    SourceClass.OWN_PERFORMANCE: ArtifactType.ANALYSIS,
}

#: Exclusions that can only be seen in the page content, not in the domain name.
#: Word-boundary matched against the page title and text. A sample member that
#: matches is excluded from the run and recorded as excluded, never silently kept.
EXCLUSION_MARKERS: dict[str, tuple[str, ...]] = {
    "franchised or brand-affiliated network": (
        "vulco",
        "first stop",
        "euromaster",
        "feuvert",
        "midas",
        "norauto",
        "aurgi",
        "confortauto",
        "rodaje ibérico",
        "red rodaje",
        "rodi",
        "bosch car service",
        "autoglass",
        "carglass",
    ),
    "online retailer / marketplace": (
        "pneus online",
        "oponeo",
        "grip500",
        "1001neumaticos",
        "neumaticos online",
    ),
}

_PROMPT_ID = "intel/teardown"
_PROMPT_TEXT = """You audit one workshop's public presence. For EACH feature listed,
report what the source below actually shows.

For every feature return one object with exactly these fields:
- feature: the feature key, exactly as written below
- status: one of present | absent | partial | unknown
- observation: one specific sentence describing what you actually saw. For
  "present", say what is there. For "absent", say that it is not visible.
- quote: a short verbatim fragment from the source supporting it, or null

Status meanings:
- present: the source clearly shows this
- partial: it is shown incompletely (e.g. prices for some services only)
- absent: you looked and it is genuinely not there
- unknown: you cannot tell from this source. USE THIS when the page looks like a
  template or a JavaScript shell, when it is very short or mostly navigation, or
  when content appears to be missing because it did not load. Do NOT report
  "absent" for something you simply could not see.

Rules:
- Never speculate about the business. Report only what the source shows.
- One object per feature, always every feature, in the order given.
- No commentary, no keys outside these fields.

FEATURES:
{features}

SOURCE CLASS: {source_class}

SOURCE:
{source}
"""


class _PromptHolder:
    def __init__(self) -> None:
        self._registry: PromptRegistry | None = None

    def registry(self) -> PromptRegistry:
        if self._registry is None:
            self._registry = PromptRegistry()
            self._registry.register(
                PromptTemplate(
                    id=_PROMPT_ID,
                    text=_PROMPT_TEXT,
                    description="Intelligence: report per-feature presence on one source",
                    version=CHECKLIST_VERSION,
                    task_class=TASK_CLASS,
                )
            )
        return self._registry


_PROMPTS = _PromptHolder()


class Sighting(BaseModel):
    """One workshop as observed on one source."""

    name: str = Field(min_length=1)
    source_class: SourceClass
    url: str | None = None
    identities: list[Identity] = Field(default_factory=list)
    excerpt: str | None = Field(
        default=None,
        description="Text already in hand (manual observation, pasted page, fixture)",
    )

    @model_validator(mode="after")
    def _something_to_read(self) -> Sighting:
        if not self.excerpt and not self.url:
            raise ValueError(f"sighting {self.name!r} has neither an excerpt nor a url")
        return self


class StudyPlan(BaseModel):
    """The bounded sample: the workshops and the sources we read."""

    venture_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    sightings: list[Sighting] = Field(min_length=1)
    population: str = Field(min_length=1)
    selection_method: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    geography: str = Field(min_length=1)
    measurement_method: str = "manual inspection of each source against a fixed feature checklist"
    inclusion: list[str] = Field(default_factory=list)
    exclusion: list[str] = Field(default_factory=list)
    correlation_id: str | None = None


@dataclasses.dataclass
class WorkshopResult:
    """What one workshop produced."""

    entity: dict
    source_artifact: dict
    teardown_artifact: dict
    evidence_ids: list[str]
    capture_quality: str
    reused: bool = False


@dataclasses.dataclass
class SourceFailure:
    """One source that could not be collected, and why."""

    name: str
    source_class: str
    url: str | None
    reason: str


@dataclasses.dataclass
class ExcludedSighting:
    """One sighting excluded by the sample's own criteria, and why."""

    name: str
    url: str | None
    reason: str
    marker: str


@dataclasses.dataclass
class StudyResult:
    """What the run produced."""

    decision: ActionDecision
    workshops: list[WorkshopResult]
    dataset_artifact: dict | None
    findings: list[dict]
    correlation_id: str
    review_item: ReviewItem | None = None
    failures: list[SourceFailure] = dataclasses.field(default_factory=list)
    excluded: list[ExcludedSighting] = dataclasses.field(default_factory=list)


# -- source reading ---------------------------------------------------------


def select_source_excerpt(text: str) -> tuple[str, dict]:
    """Build the model input from a page: the head, plus windows around terms
    that matter for this checklist.

    Naive truncation would hide a footer contact block behind a long nav, which
    converts a coverage limit into a false absence. Instead the head is kept and
    later regions are sampled around relevant words, so what gets dropped is
    irrelevant bulk. What was NOT inspected is recorded either way.
    """
    if len(text) <= MAX_SOURCE_CHARS:
        return text, {
            "source_chars": len(text),
            "excerpt_chars": len(text),
            "truncated": False,
        }
    parts = [text[:HEAD_CHARS]]
    budget = MAX_SOURCE_CHARS - HEAD_CHARS
    lowered = text.lower()
    for keyword in _KEYWORD_WINDOWS:
        if budget <= 0:
            break
        for match in re.finditer(re.escape(keyword), lowered):
            start = match.start()
            if start < HEAD_CHARS:
                continue
            window = text[max(0, start - 100) : start + WINDOW_CHARS]
            parts.append(f"[...] {window}")
            budget -= len(window)
            if budget <= 0:
                break
    excerpt = "\n".join(parts)
    return excerpt, {
        "source_chars": len(text),
        "excerpt_chars": len(excerpt),
        "truncated": True,
    }


def capture_quality(text: str, inspection: dict) -> str:
    """How much this capture can be trusted: ``full``, ``partial`` or ``suspect``.

    ``suspect`` means the page is short and shows no contact marker at all — more
    likely an unrendered template than a business with no way to be reached.
    """
    lowered = text.lower()
    if len(text) < SUSPECT_CAPTURE_CHARS and not any(m in lowered for m in _CONTACT_MARKERS):
        return "suspect"
    if inspection.get("truncated"):
        return "partial"
    return "full"


def exclusion_hit(*, title: str | None, text: str) -> tuple[str, str] | None:
    """Whether the page itself reveals an exclusion criterion. Returns
    ``(reason, marker)`` or None."""
    haystack = f"{title or ''}\n{text}".lower()
    for reason, markers in EXCLUSION_MARKERS.items():
        for marker in markers:
            if re.search(rf"\b{re.escape(marker)}\b", haystack):
                return reason, marker
    return None


def load_capture_limitations(path: str | pathlib.Path) -> dict[str, str]:
    """Operator-verified capture limitations: url -> why it cannot be trusted.

    A human who looked at the rendered site can record here that a captured page
    is not representative. Sources listed are treated as ``suspect``, so their
    absences are recorded as unverifiable rather than believed.
    """
    raw = yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"capture limitations must map to an object: {path}")
    entries = raw.get("capture_limitations") or []
    if not isinstance(entries, list):
        raise TypeError(f"capture_limitations must be a list: {path}")
    limitations: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("url"):
            raise TypeError(f"each capture limitation needs a url: {path}")
        limitations[str(entry["url"])] = str(entry.get("reason") or "unspecified")
    return limitations


def load_study_plan(path: str | pathlib.Path) -> StudyPlan:
    """Load and validate a study plan from a human-editable YAML file."""
    raw = yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"study plan must map to an object: {path}")
    return StudyPlan.model_validate(raw)


def render_teardown_prompt(sighting: Sighting, source_text: str) -> str:
    """Serialize one sighting into the versioned per-feature prompt."""
    features = "\n".join(
        f"- {feature.value}: {FEATURE_QUESTION[feature]}" for feature in SiteFeature
    )
    return (
        _PROMPTS.registry()
        .render(
            _PROMPT_ID,
            {
                "features": features,
                "source_class": sighting.source_class.value,
                "source": source_text,
            },
        )
        .text
    )


def _parse_rows(raw: str, warnings: list[str]) -> list[dict]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        warnings.append(f"model returned invalid JSON: {exc}")
        return []
    if not isinstance(data, list):
        warnings.append("model did not return a JSON array")
        return []
    return [row for row in data if isinstance(row, dict)]


def read_source(sighting: Sighting, *, fetch: Callable[[Sighting], dict] | None = None) -> dict:
    """Get the source text for one sighting (from the excerpt or the fetcher)."""
    if sighting.excerpt is not None:
        return {
            "text": sighting.excerpt,
            "url": sighting.url,
            "title": sighting.name,
            "provider": "manual",
            "retrieved_at": _now(),
        }
    if fetch is None:
        raise RuntimeError(f"no fetch supplied and {sighting.name!r} has no excerpt")
    document = fetch(sighting)
    if not isinstance(document, dict):
        raise RuntimeError(
            f"fetch returned {type(document).__name__} for {sighting.name!r}; expected a mapping"
        )
    if not (document.get("text") or "").strip():
        raise RuntimeError(f"fetch returned no text for {sighting.name!r}")
    return document


def zeus_fetcher(zeus, venture_id: str) -> Callable[[Sighting], dict]:
    """A fetcher backed by the live Zeus web layer (``read_url``).

    Zeus owns provider choice, free-quota accounting and provenance; the study
    never re-implements that.

    Note: ``DevZeus`` inherits the ``Zeus`` Protocol, so an unimplemented
    ``read_url`` exists as a stub that returns ``None`` rather than being absent.
    The returned document is therefore validated, not merely assumed.
    """

    def fetch(sighting: Sighting) -> dict:
        if sighting.url is None:
            raise RuntimeError(f"{sighting.name!r} has no url to read")
        read_url = getattr(zeus, "read_url", None)
        if not callable(read_url):
            raise RuntimeError(
                f"this Zeus surface has no read_url: cannot read {sighting.name!r}; "
                "pass an explicit fetch"
            )
        document = read_url(sighting.url, venture=venture_id)
        if not isinstance(document, dict):
            raise RuntimeError(
                f"the Zeus web layer returned {type(document).__name__} for {sighting.url!r}: "
                "cannot read through this surface (a Protocol stub returns None) — "
                "pass an explicit fetch"
            )
        document.setdefault("url", sighting.url)
        return document

    return fetch


# -- teardown ----------------------------------------------------------------


def source_key(sighting: Sighting) -> str:
    """A stable identity for *this source*, not merely this workshop.

    A workshop may have several pages of the same source class (home, contact,
    services); each is a separate source and gets its own teardown.
    """
    base = sighting.url if sighting.url else f"excerpt:{content_hash(sighting.excerpt or '')}"
    # The checklist version is part of the key: a new checklist re-inspects rather
    # than reusing observations recorded under the old one.
    return f"{base}@{CHECKLIST_VERSION}"


def _existing_teardown(store, venture_id: str, key: str) -> dict | None:
    """A teardown already produced from this source.

    Keyed on the source alone, not on the workshop: it must be answerable *before*
    an entity exists, so a source that the exclusion preflight rejects never
    creates a half-built entity.
    """
    for artifact in list_artifacts(store, venture_id, artifact_type=ArtifactType.TEARDOWN):
        if (artifact.get("source_metadata") or {}).get("source_key") == key:
            return artifact
    return None


def _presence_for(status: str, quality: str) -> FeaturePresence:
    """The presence to record, given what the model said and how good the capture was."""
    try:
        reported = str(status or "").strip().lower()
    except Exception:  # pragma: no cover - defensive
        reported = ""
    if reported == "present":
        return FeaturePresence.PRESENT
    if reported == "partial":
        return FeaturePresence.PARTIAL
    if reported in ("absent", "missing"):
        # A capture we do not trust cannot support a claim of absence.
        return FeaturePresence.ABSENT if quality == "full" else FeaturePresence.UNVERIFIABLE
    return FeaturePresence.UNKNOWN


def teardown_sighting(
    sighting: Sighting,
    *,
    venture_id: str,
    store,
    model: Callable[[str, str], str],
    fetch: Callable[[Sighting], dict] | None = None,
    declared_policy: dict[SourceClass, SourcePolicy] | None = None,
    capture_limitations: dict[str, str] | None = None,
    correlation_id: str | None = None,
) -> WorkshopResult:
    """Resolve one workshop, read its source, and record every feature's presence.

    Skips the fetch and the model entirely when a teardown already exists for this
    workshop, source and checklist version.
    """
    require_collection_allowed(sighting.source_class, declared=declared_policy)

    key = source_key(sighting)
    existing = _existing_teardown(store, venture_id, key)
    if existing is not None:
        metadata = existing.get("source_metadata") or {}
        entity_id = (existing.get("about_entity_ids") or [None])[0]
        entity = get_entity(store, entity_id) if entity_id else None
        if entity is None:
            raise RuntimeError(f"teardown {existing['id']} references a missing entity {entity_id!r}")
        return WorkshopResult(
            entity=entity,
            source_artifact={},
            teardown_artifact=existing,
            evidence_ids=[
                o["evidence_id"] for o in metadata.get("observations") or [] if o.get("evidence_id")
            ],
            capture_quality=metadata.get("capture_quality") or "full",
            reused=True,
        )

    document = read_source(sighting, fetch=fetch)
    text = document["text"]
    title = document.get("title") or sighting.name

    # Sample preflight, before anything is created: an exclusion criterion visible
    # in the page itself. A rejected source must leave no entity and no artifact.
    hit = exclusion_hit(title=title, text=text)
    if hit is not None:
        raise ExcludedSource(*hit)

    resolution = resolve_workshop(
        store,
        venture_id,
        name=sighting.name,
        identities=sighting.identities,
        source=sighting.source_class.value,
    )
    entity = resolution.entity

    excerpt, inspection = select_source_excerpt(text)
    quality = capture_quality(text, inspection)
    if capture_limitations and sighting.url and sighting.url in capture_limitations:
        quality = "suspect"
        inspection["manual_note"] = capture_limitations[sighting.url]

    duplicates = [
        artifact
        for artifact in find_duplicates(store, venture_id, text)
        if artifact.get("source_class") == sighting.source_class.value
    ]
    source_artifact = (
        duplicates[0]
        if duplicates
        else create_artifact(
            store,
            venture_id,
            artifact_type=_ARTIFACT_TYPE_BY_SOURCE[sighting.source_class],
            title=title,
            uri=document.get("url") or sighting.url,
            body=text,
            source_class=sighting.source_class,
            about_entity_ids=[entity["id"]],
            # Grouped by content, not by workshop: identical text appearing in two
            # places is one voice, however many workshops repeat it.
            independence_group=f"content:{content_hash(text)}",
            source_metadata={
                "provider": document.get("provider"),
                "retrieved_at": document.get("retrieved_at"),
                "title": title,
                "inspection": inspection,
                "capture_quality": quality,
            },
        )
    )

    prompt_text = render_teardown_prompt(sighting, excerpt)
    warnings: list[str] = []
    rows: list[dict] = []
    for attempt in range(1, JSON_ATTEMPTS + 1):
        rows = _parse_rows(model(TASK_CLASS, prompt_text), warnings)
        if rows:
            break
        if attempt < JSON_ATTEMPTS and any("invalid JSON" in w for w in warnings):
            warnings.clear()
            continue
        break

    reported: dict[str, dict] = {}
    for row in rows:
        slug = str(row.get("feature") or "").strip()
        if slug in {feature.value for feature in SiteFeature}:
            reported[slug] = row
        elif slug:
            warnings.append(f"unknown feature {slug!r}; ignored")

    evidence_ids: list[str] = []
    observations: list[dict] = []
    for feature in SiteFeature:  # always every feature, in a fixed order
        row = reported.get(feature.value, {})
        presence = _presence_for(row.get("status", "unknown"), quality)
        statement = str(row.get("observation") or "").strip() or (
            f"{feature.value} could not be assessed from this capture"
        )
        evidence = add_evidence(
            store,
            venture_id,
            statement=statement,
            directness=Directness.MEASURED,
            feature=feature.value,
            presence=presence,
            artifact_ids=[source_artifact["id"]],
            entity_ids=[entity["id"]],
            constraint=CONSTRAINT_BY_FEATURE[feature],
            correlation_id=correlation_id,
            note=f"feature:{feature.value}={presence.value} | capture:{quality}"
            + (f" | quote: {row['quote']}" if row.get("quote") else ""),
        )
        evidence_ids.append(evidence["id"])
        observations.append(
            {
                "feature": feature.value,
                "reported_status": row.get("status") or "unknown",
                "presence": presence.value,
                "observation": statement,
                "quote": row.get("quote"),
                "evidence_id": evidence["id"],
                "capture_quality": quality,
            }
        )

    teardown = create_artifact(
        store,
        venture_id,
        artifact_type=ArtifactType.TEARDOWN,
        title=f"Teardown: {sighting.name} ({sighting.source_class.value})",
        originated_by_us=True,
        derived_from_artifact_ids=[source_artifact["id"]],
        source_class=sighting.source_class,
        about_entity_ids=[entity["id"]],
        body=text,
        independence_group=f"teardown:{entity['id']}",
        source_metadata={
            "source_class": sighting.source_class.value,
            "source_key": key,
            "checklist_version": CHECKLIST_VERSION,
            "entity_id": entity["id"],
            "capture_quality": quality,
            "inspection": inspection,
            "observations": observations,
            "warnings": warnings,
        },
        note=(
            f"{sum(1 for o in observations if o['presence'] == 'absent')} absence(s), "
            f"{sum(1 for o in observations if o['presence'] == 'present')} present "
            f"(capture: {quality})"
        ),
    )
    return WorkshopResult(
        entity=entity,
        source_artifact=source_artifact,
        teardown_artifact=teardown,
        evidence_ids=evidence_ids,
        capture_quality=quality,
    )


class ExcludedSource(Exception):
    """Raised when a page itself reveals a sample exclusion criterion."""


# -- dataset and findings ----------------------------------------------------


def build_dataset(
    plan: StudyPlan,
    *,
    workshop_count: int,
    attempted: int,
    excluded: list[ExcludedSighting],
    failures: list[SourceFailure],
    store,
    correlation_id: str,
) -> dict:
    """The study's dataset artifact, with an explicit and honest sample record."""
    for artifact in list_artifacts(store, plan.venture_id, artifact_type=ArtifactType.DATASET):
        metadata = artifact.get("source_metadata") or {}
        if (
            metadata.get("correlation_id") == correlation_id
            and metadata.get("purpose") == "loop_a_sample"
        ):
            return artifact
    notes = (
        f"{workshop_count} of {attempted} planned sources collected; "
        f"{len(excluded)} excluded by sample criteria; {len(failures)} failed. "
        "Bounded architectural proof, not a representative survey."
    )
    return create_artifact(
        store,
        plan.venture_id,
        artifact_type=ArtifactType.DATASET,
        title=f"Loop A sample: {workshop_count} workshops",
        originated_by_us=True,
        source_class=SourceClass.PUBLIC_WEB,
        dataset_definition=DatasetDefinition(
            population=plan.population,
            selection_method=plan.selection_method,
            timeframe=plan.timeframe,
            geography=plan.geography,
            measurement_method=plan.measurement_method,
            inclusion=plan.inclusion,
            exclusion=plan.exclusion,
            sample_size=workshop_count,
            missingness=(
                f"excluded by criteria: {[e.name for e in excluded]}; "
                f"uncollected: {[f.name for f in failures]}"
            ),
            notes=notes,
        ),
        source_metadata={"correlation_id": correlation_id, "purpose": "loop_a_sample"},
        note="The sample is labelled honestly: it is not statistically representative.",
    )


def _source_artifacts_for(store, venture_id: str, evidence_ids: list[str]) -> list[str]:
    """The source artifacts behind a set of evidence items."""
    artifacts: list[str] = []
    for evidence_id in evidence_ids:
        item = get_item(store, venture_id, evidence_id)
        if item is not None:
            artifacts.extend(item.get("artifact_ids") or [])
    return sorted(set(artifacts))


def derive_findings(
    store,
    venture_id: str,
    *,
    dataset_artifact_id: str,
    observations_by_workshop: dict[str, list[dict]],
    workshop_count: int,
    correlation_id: str,
) -> list[dict]:
    """Aggregate observations into one finding per feature.

    A finding reports the full breakdown — how many distinct workshops showed the
    feature, how many did not, and how many could not be verified — so the pattern
    carries its own counterexamples and its own uncertainty. It claims only what
    was observed on a page (``OBSERVED_ABSENCE``), never what it costs.

    Re-running the study does not duplicate a feature's finding.
    """
    existing = {
        (finding.get("note") or ""): finding
        for finding in list_items(store, venture_id, item_type=ItemType.FINDING)
        if finding.get("correlation_id") == correlation_id
    }

    # Resolve ONE presence per (workshop, feature). A workshop that shows the
    # feature on any of its sources counts as showing it — the feature exists for
    # that business — so a workshop is never counted as both absent and present.
    # When its sources disagree, both observations are kept and linked as a
    # contradiction: the tension is recorded, not averaged into a middle answer.
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for entity_id, observations in observations_by_workshop.items():
        for observation in observations:
            grouped[(entity_id, observation["feature"])].append(observation)

    # feature -> presence -> one entry per WORKSHOP, carrying all its evidence ids.
    # Counting per workshop is the point; several sources agreeing must not
    # multiply the workshop.
    by_feature: dict[SiteFeature, dict[str, list[tuple[str, list[str]]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for (entity_id, feature_slug), observations in grouped.items():
        feature = SiteFeature(feature_slug)
        present = [o for o in observations if o["presence"] == FeaturePresence.PRESENT.value]
        partial = [o for o in observations if o["presence"] == FeaturePresence.PARTIAL.value]
        absent = [o for o in observations if o["presence"] == FeaturePresence.ABSENT.value]
        unverifiable = [
            o for o in observations if o["presence"] == FeaturePresence.UNVERIFIABLE.value
        ]
        if present and absent:
            add_edge(
                store,
                venture_id,
                relation=Relation.CONTRADICTS,
                source=absent[0]["evidence_id"],
                target=present[0]["evidence_id"],
                note=f"{feature.value}: shown on one source, not on another",
            )
        if present:
            chosen, chosen_observations = FeaturePresence.PRESENT.value, present
        elif partial:
            chosen, chosen_observations = FeaturePresence.PARTIAL.value, partial
        elif absent:
            chosen, chosen_observations = FeaturePresence.ABSENT.value, absent
        elif unverifiable:
            chosen, chosen_observations = FeaturePresence.UNVERIFIABLE.value, unverifiable
        else:
            chosen, chosen_observations = FeaturePresence.UNKNOWN.value, [
                o for o in observations if o["presence"] == FeaturePresence.UNKNOWN.value
            ]
        by_feature[feature][chosen].append(
            (entity_id, [o["evidence_id"] for o in chosen_observations])
        )

    findings: list[dict] = []
    for feature in SiteFeature:
        counts = by_feature.get(feature)
        if not counts:
            continue
        absent = counts.get(FeaturePresence.ABSENT.value, [])
        present = counts.get(FeaturePresence.PRESENT.value, [])
        partial = counts.get(FeaturePresence.PARTIAL.value, [])
        unverifiable = counts.get(FeaturePresence.UNVERIFIABLE.value, [])
        unknown = counts.get(FeaturePresence.UNKNOWN.value, [])
        if not (absent or present or partial):
            continue  # nothing determinate to report for this feature

        note_marker = f"feature:{feature.value}"
        if note_marker in existing:
            findings.append(existing[note_marker])
            continue

        deterministic = [*absent, *present, *partial]
        # The three "we do not know" cases stay distinct, because they mean
        # different things: a capture we could not trust, a page that was unclear,
        # and a genuine absence are not the same claim.
        statement = (
            f"{len(absent)} of {workshop_count} sampled workshops did not visibly show "
            f"{FEATURE_ABSENCE_LABEL[feature]}. "
            f"{len(present)} did show it; {len(partial)} showed it partly; "
            f"{len(unverifiable)} could not be judged because the page capture was "
            f"incomplete or unrendered; {len(unknown)} were unclear from the page. "
            f"(Observed on the workshops' own websites; not a representative survey.)"
        )
        finding = add_finding(
            store,
            venture_id,
            statement=statement,
            epistemic_type=EpistemicType.OBSERVED_ON_SITE,
            claim_strength=ClaimStrength.OBSERVED_ABSENCE,
            label=EvidenceLabel.OBSERVED,
            artifact_ids=_source_artifacts_for(
                store,
                venture_id,
                [evidence_id for _, evidence_ids in deterministic for evidence_id in evidence_ids],
            ),
            entity_ids=[entity_id for entity_id, _ in absent],
            constraint=CONSTRAINT_BY_FEATURE[feature],
            dataset_artifact_id=dataset_artifact_id,
            correlation_id=correlation_id,
            note=note_marker,
        )
        for _, evidence_ids in deterministic:
            for evidence_id in evidence_ids:
                add_edge(
                    store,
                    venture_id,
                    relation=Relation.SUPPORTS,
                    source=evidence_id,
                    target=finding["id"],
                )
        # Unverifiable observations are linked too, so the doubt is visible.
        for _, evidence_ids in [*unverifiable, *unknown]:
            for evidence_id in evidence_ids:
                add_edge(
                    store,
                    venture_id,
                    relation=Relation.USES_ARTIFACT,
                    source=evidence_id,
                    target=finding["id"],
                )
        findings.append(refresh_health(store, venture_id, finding["id"]))
    return findings


def run_study(
    plan: StudyPlan,
    *,
    store,
    model: Callable[[str, str], str],
    plane: ControlPlane,
    fetch: Callable[[Sighting], dict] | None = None,
    declared_policy: dict[SourceClass, SourcePolicy] | None = None,
    capture_limitations: dict[str, str] | None = None,
    trace: TraceStore | None = None,
    review: ReviewQueue | None = None,
    pause_seconds: float = 0.0,
) -> StudyResult:
    """Run the bounded study end to end.

    Everything persists through the injected store, so a re-run continues rather
    than repeating work it already did.

    ``pause_seconds`` waits between workshops. Back-to-back model calls over large
    pages trip free-tier per-minute token limits; a real run wants a pause of a
    few seconds, tests do not.
    """
    venture_id = plan.venture_id
    correlation_id = plan.correlation_id or f"{venture_id}-study"
    proposal = ActionProposal(
        business_id=venture_id,
        kind=ActionKind.EVIDENCE_INGEST,
        subject_kind="study",
        subject_id=correlation_id,
        detail=f"{len(plan.sightings)} sighting(s)",
    )
    gated = propose(plane, proposal, review=review, trace=trace, correlation_id=correlation_id)
    if gated.decision.verdict is not Verdict.ALLOW:
        return StudyResult(
            decision=gated.decision,
            workshops=[],
            dataset_artifact=None,
            findings=[],
            correlation_id=correlation_id,
            review_item=gated.review_item,
        )

    workshops: list[WorkshopResult] = []
    failures: list[SourceFailure] = []
    excluded: list[ExcludedSighting] = []
    for index, sighting in enumerate(plan.sightings):
        if index and pause_seconds:
            time.sleep(pause_seconds)
        try:
            workshops.append(
                teardown_sighting(
                    sighting,
                    venture_id=venture_id,
                    store=store,
                    model=model,
                    fetch=fetch,
                    declared_policy=declared_policy,
                    capture_limitations=capture_limitations,
                    correlation_id=correlation_id,
                )
            )
        except SourcePolicyError:
            raise  # a policy violation is a configuration error, not a flaky source
        except ExcludedSource as skip:
            excluded.append(
                ExcludedSighting(
                    name=sighting.name,
                    url=sighting.url,
                    reason=skip.args[0],
                    marker=skip.args[1],
                )
            )
        except Exception as exc:  # noqa: BLE001 - recorded and reported, never swallowed
            failures.append(
                SourceFailure(
                    name=sighting.name,
                    source_class=sighting.source_class.value,
                    url=sighting.url,
                    reason=f"{type(exc).__name__}: {exc}",
                )
            )

    observations_by_workshop: dict[str, list[dict]] = defaultdict(list)
    for result in workshops:
        observations_by_workshop[result.entity["id"]].extend(
            (result.teardown_artifact.get("source_metadata") or {}).get("observations") or []
        )
    workshop_count = len({result.entity["id"] for result in workshops})
    dataset = build_dataset(
        plan,
        workshop_count=workshop_count,
        attempted=len(plan.sightings),
        excluded=excluded,
        failures=failures,
        store=store,
        correlation_id=correlation_id,
    )
    findings = derive_findings(
        store,
        venture_id,
        dataset_artifact_id=dataset["id"],
        observations_by_workshop=observations_by_workshop,
        workshop_count=workshop_count,
        correlation_id=correlation_id,
    )

    if trace is not None:
        trace.record(
            TraceEvent(
                id=trace.next_id(venture_id),
                business_id=venture_id,
                at=datetime.now(UTC),
                actor=TraceActor.MACHINE,
                outcome=TraceOutcome.COMPLETED,
                action_kind=ActionKind.EVIDENCE_INGEST,
                subject_kind="study",
                subject_id=correlation_id,
                reason=(
                    f"{workshop_count} workshop(s), "
                    f"{sum(len(w.evidence_ids) for w in workshops)} observation(s), "
                    f"{len(findings)} finding(s), {len(excluded)} excluded, "
                    f"{len(failures)} failure(s)"
                ),
                gear="intelligence",
                correlation_id=correlation_id,
                detail={
                    "dataset": dataset["id"],
                    "findings": [f["id"] for f in findings],
                    "excluded": [f"{e.name}: {e.reason}" for e in excluded],
                    "failures": [f"{f.name} ({f.source_class}): {f.reason}" for f in failures],
                },
            )
        )
    return StudyResult(
        decision=gated.decision,
        workshops=workshops,
        dataset_artifact=dataset,
        findings=findings,
        correlation_id=correlation_id,
        failures=failures,
        excluded=excluded,
    )


def entity_ids_for(store, venture_id: str) -> list[str]:
    return [entity["id"] for entity in list_entities(store, venture_id)]
