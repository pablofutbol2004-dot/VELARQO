"""Intelligence gear, slice 1 — extract market insights from raw evidence.

Deterministic orchestration around one AI judgment step. It never trusts the
model blindly:

- A versioned extraction prompt turns raw evidence (verbatim owner material)
  into a strict JSON list of insights.
- Each insight is validated into the typed ``MarketInsight`` contract; the raw
  evidence item is attached as its provenance source and labelled ``INFERRED``
  (the model's read of the source, not an observed fact).
- Near-duplicate statements within one batch are dropped (similarity guard).
- If nothing valid parses, it fails loudly instead of returning junk.

The AI step is invoked through a callable ``model(task_class, prompt) -> str`` —
the caller supplies the Zeus surface (dev adapter or real ZEUS). Nothing here
names a vendor or assumes persistence.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable

from kleos.domain import MainConstraint, OutcomeBucket
from kleos.jsoncalls import JSON_ATTEMPTS
from kleos.models import EvidenceLabel, SourceRef
from kleos.prompts import PromptRegistry, PromptTemplate
from kleos.similarity import token_similarity

from .contracts import (
    EvidenceItem,
    InsightKind,
    IntelligenceInput,
    IntelligenceOutput,
    MarketInsight,
)

#: Router task class for extraction. Read-only judgement over owner language.
TASK_CLASS = "normal"

_BUCKET_ALIASES = {
    "money": OutcomeBucket.MAKE_MORE_MONEY,
    "time": OutcomeBucket.SAVE_MONEY_OR_TIME,
    "service": OutcomeBucket.DELIVER_BETTER_SERVICE,
}

_PROMPT_ID = "intel/extract"
_PROMPT_TEXT = """You are an analyst turning raw workshop-owner evidence into a
structured market model. Read each piece of evidence below and extract the
insights it supports.

Return ONLY a JSON array. Each element is an object with exactly these fields:
- kind: one of pain | desire | belief | language | opportunity
- statement: one specific, faithful insight in the owner's language/meaning
- constraint: one of demand, conversion, capacity, margin, retention, admin,
  service_quality if clearly implied, else null
- bucket: money or time or service if clearly implied, else null
- from_evidence: the 1-based line number of the evidence item this insight
  comes from (null if it genuinely draws on more than one / you cannot tell)

Rules:
- Only extract what the evidence actually supports. Do not add claims.
- Attribute each insight to the evidence line it came from, not to the batch.
- Keep owner wording close to verbatim for "language" items; translate nothing.
- Use the singular owner voice where that is what the evidence says.
- If an insight is genuinely ambiguous about constraint/bucket/from_evidence,
  set it null.
- No commentary, no keys outside these fields.

EVIDENCE:
{evidence}
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
                    description="Intelligence: extract pains/desires/beliefs/language from owner evidence",
                    version=1,
                    task_class=TASK_CLASS,
                )
            )
        return self._registry


_PROMPTS = _PromptHolder()


def render_extraction_prompt(
    evidence: list[EvidenceItem], *, registry: PromptRegistry | None = None
) -> str:
    """Serialize evidence into the versioned extraction prompt text."""
    reg = registry or _PROMPTS.registry()
    lines = []
    for i, item in enumerate(evidence, start=1):
        lines.append(
            f"{i}. [{item.source_language}] {item.verbatim}   (source: {item.source.reference})"
        )
    rendered = reg.render(_PROMPT_ID, {"evidence": "\n".join(lines)})
    return rendered.text


def _parse(raw: str, warnings: list[str]) -> list[dict]:
    text = raw.strip()
    # Tolerate a fenced JSON block.
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
    return [d for d in data if isinstance(d, dict)]


def _row_source(row: dict, evidence: list[EvidenceItem], warnings: list[str]) -> SourceRef | None:
    """Attach each insight to the evidence line it came from (never the batch).

    A single-item batch is unambiguous (that item); with several evidence items
    the model names a 1-based ``from_evidence`` line. When attribution is missing
    or out of range the insight carries NO source rather than a wrong one — a
    wrong provenance is worse than none, and the ledger only *requires* sources
    at the operator-confirmed stage.
    """
    if len(evidence) == 1:
        return evidence[0].source
    raw = row.get("from_evidence")
    if raw is None or raw == "":
        warnings.append(
            "insight had no from_evidence with multiple evidence items; no source attached"
        )
        return None
    try:
        index = int(raw) - 1
    except (TypeError, ValueError):
        warnings.append(f"insight had non-integer from_evidence {raw!r}; no source attached")
        return None
    if 0 <= index < len(evidence):
        return evidence[index].source
    warnings.append(
        f"insight had out-of-range from_evidence {raw!r} (have {len(evidence)} items); no source attached"
    )
    return None


def _map_insight(
    row: dict,
    *,
    pack: str,
    source: SourceRef | None,
    warnings: list[str],
) -> MarketInsight | None:
    statement = str(row.get("statement") or "").strip()
    if not statement:
        return None
    kind_raw = str(row.get("kind") or "").strip()
    try:
        kind = InsightKind(kind_raw)
    except ValueError:
        warnings.append(f"unknown insight kind {kind_raw!r}; dropped one statement")
        return None
    constraint = None
    bucket = None
    try:
        if row.get("constraint"):
            constraint = MainConstraint(str(row["constraint"]).strip())
    except ValueError:
        warnings.append(f"unknown constraint {row.get('constraint')!r}")
    if row.get("bucket"):
        bucket = _BUCKET_ALIASES.get(str(row["bucket"]).strip())
        if bucket is None:
            try:
                bucket = OutcomeBucket(str(row["bucket"]).strip())
            except ValueError:
                warnings.append(f"unknown bucket {row.get('bucket')!r}")
    note = row.get("note")
    return MarketInsight(
        kind=kind,
        statement=statement,
        label=EvidenceLabel.INFERRED,
        sources=[source] if source else [],
        bucket=bucket,
        constraint=constraint,
        note=str(note) if note else None,
    )


def _is_near_duplicate(statement: str, seen: list[str]) -> bool:
    return any(token_similarity(statement, prior) > 0.9 for prior in seen)


def extract_insights(
    request: IntelligenceInput,
    *,
    model: Callable[[str, str], str],
    prompt: str | None = None,
) -> IntelligenceOutput:
    """Run extraction over evidence and return validated, de-duplicated insights.

    ``model`` is the Zeus-style ``(task_class, prompt_text) -> text`` callable.
    Raises RuntimeError if nothing valid could be extracted (never returns junk).
    """
    warnings: list[str] = []
    if not request.evidence:
        return IntelligenceOutput(
            pack=request.pack, insights=[], open_questions=["no evidence supplied"]
        )
    prompt_text = prompt or render_extraction_prompt(request.evidence)
    insights: list[MarketInsight] = []
    seen: list[str] = []
    warnings: list[str] = []
    for attempt in range(1, JSON_ATTEMPTS + 1):
        batch_warnings: list[str] = []
        rows = _parse(model(TASK_CLASS, prompt_text), batch_warnings)
        fresh: list[MarketInsight] = []
        for row in rows:
            source = _row_source(row, request.evidence, batch_warnings)
            insight = _map_insight(row, pack=request.pack, source=source, warnings=batch_warnings)
            if insight is None:
                continue
            if _is_near_duplicate(insight.statement, seen):
                batch_warnings.append(f"dropped near-duplicate statement: {insight.statement!r}")
                continue
            seen.append(insight.statement)
            fresh.append(insight)
        if fresh:
            insights.extend(fresh)
            warnings.extend(batch_warnings)
            break
        # A malformed response is worth one bounded retry; a valid-but-empty one
        # is the model's honest answer and is not retried.
        if attempt < JSON_ATTEMPTS and any("invalid JSON" in w for w in batch_warnings):
            continue
        warnings.extend(batch_warnings)
        break
    output = IntelligenceOutput(pack=request.pack, insights=insights, open_questions=warnings)
    if not insights:
        raise RuntimeError(
            f"intelligence extraction produced no valid insights from {len(request.evidence)} evidence items: "
            + ("; ".join(warnings) if warnings else "model returned nothing")
        )
    return output


def prompt_hash(prompt: str) -> str:
    """Stable hash of the exact prompt text sent (for trace/reproducibility)."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
