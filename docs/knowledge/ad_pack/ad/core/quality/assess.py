"""Quality gear — gate a finished copy against its truth packet.

Deterministic checks where possible; everything that needs taste stays a human
check. Design intent: a piece NEVER auto-passes on its own — useful and
strategic-fit are human calls (set here as unresolved), so the normal verdict is
``human``. A piece that asserts an unverified central claim is ``reject``ed;
oversized copy for a format is ``reject``ed.
"""

from __future__ import annotations

from kleos.models import EvidenceLabel

from .contracts import CheckKind, QualityCheckResult, QualityReport, decide


def assess_copy(
    piece,
    packet,
    *,
    max_chars: int | None = None,
    item_id: str | None = None,
) -> QualityReport:
    """Build a QualityReport for a finished piece against its truth packet.

    ``item_id`` is the stable identifier of the piece being assessed (a run id);
    when omitted the report falls back to a text preview so standalone callers
    stay informative.
    """
    central = packet.claim
    checks: list[QualityCheckResult] = []

    # Truth: never assert an unverified central claim.
    if central.label is EvidenceLabel.NEEDS_CHECK:
        checks.append(
            QualityCheckResult(
                check=CheckKind.TRUTH, passed=False, note="central claim is unverified"
            )
        )
    elif not central.sources:
        checks.append(
            QualityCheckResult(
                check=CheckKind.TRUTH, passed=None, note="central claim has no source"
            )
        )
    else:
        checks.append(QualityCheckResult(check=CheckKind.TRUTH, passed=True, note="grounded claim"))

    # Technical: only when the caller gives the format's length cap.
    if max_chars is not None:
        if piece.chars > max_chars:
            checks.append(
                QualityCheckResult(
                    check=CheckKind.TECHNICAL_NATIVE,
                    passed=False,
                    note=f"{piece.chars} chars exceeds {max_chars}",
                )
            )
        else:
            checks.append(
                QualityCheckResult(
                    check=CheckKind.TECHNICAL_NATIVE, passed=True, note="within length cap"
                )
            )
    else:
        checks.append(
            QualityCheckResult(
                check=CheckKind.TECHNICAL_NATIVE, passed=None, note="no format spec yet"
            )
        )

    # Taste/judgement stays human by design.
    checks.append(
        QualityCheckResult(check=CheckKind.USEFULNESS, passed=None, note="human judgement")
    )
    checks.append(
        QualityCheckResult(check=CheckKind.STRATEGIC_FIT, passed=None, note="human judgement")
    )

    return QualityReport(
        pack=piece.business_id,
        item=item_id or piece.final_text[:80],
        checks=checks,
        verdict=decide(checks),
    )
