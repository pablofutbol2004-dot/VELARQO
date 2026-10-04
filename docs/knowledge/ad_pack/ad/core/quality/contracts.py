"""Quality gear — draft gate contracts (not implemented).

Quality gates a piece before it may go out: truth, strategic fit, usefulness,
creative taste, and technical/native checks, routed by risk to auto-pass, human,
or reject (README gear 6). Draft seam only; pinned on first implementation.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class QualityVerdict(StrEnum):
    """Where a piece may go next."""

    AUTO_PASS = "auto_pass"  # every check passed; safe to proceed
    HUMAN = "human"  # some check needs a person
    REJECT = "reject"  # a hard check failed; do not proceed


class CheckKind(StrEnum):
    """The kinds of checks Quality runs (README gear 6)."""

    TRUTH = "truth"
    STRATEGIC_FIT = "strategic_fit"
    USEFULNESS = "usefulness"
    CREATIVE_TASTE = "creative_taste"
    TECHNICAL_NATIVE = "technical_native"


class QualityCheckResult(BaseModel):
    """One check's outcome; ``passed=None`` means it still needs a human."""

    check: CheckKind
    passed: bool | None = None
    note: str | None = None


class QualityReport(BaseModel):
    """A gate decision for one piece."""

    pack: str
    item: str = Field(description="Reference to the piece being gated")
    checks: list[QualityCheckResult] = Field(default_factory=list)
    verdict: QualityVerdict

    def blocking(self) -> list[str]:
        """Why this piece did not auto-pass — never just "bad"."""
        out: list[str] = []
        for result in self.checks:
            if result.passed is False:
                out.append(f"{result.check.value}: {result.note or 'failed'}")
            elif result.passed is None:
                note = f" ({result.note})" if result.note else ""
                out.append(f"{result.check.value}: needs human review{note}")
        return out


def decide(checks: list[QualityCheckResult]) -> QualityVerdict:
    """Deterministic risk-based routing over a set of check results.

    - any failed check -> reject
    - no checks at all, or any unresolved (None) -> human
    - otherwise -> auto-pass
    """
    if any(result.passed is False for result in checks):
        return QualityVerdict.REJECT
    if not checks or any(result.passed is None for result in checks):
        return QualityVerdict.HUMAN
    return QualityVerdict.AUTO_PASS
