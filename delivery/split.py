"""Deterministic comparison-group (holdout) split, stratified by quote age,
so treatment and holdout have the same mix of old and recent quotes.
Same inputs always give the same split: re-running can never reshuffle."""

import hashlib
import math


def _order(pilot_id: str, homeowner_key: str) -> str:
    return hashlib.sha256(f"{pilot_id}:{homeowner_key}".encode()).hexdigest()


def split(pilot_id: str, homeowners: list[tuple[str, str]], fraction: float) -> dict[str, str]:
    """homeowners: (homeowner_key, stratum). Returns {homeowner_key: 'holdout'|'treatment'}."""
    by_stratum: dict[str, list[str]] = {}
    for key, stratum in homeowners:
        by_stratum.setdefault(stratum, []).append(key)
    arms = {}
    for keys in by_stratum.values():
        ordered = sorted(keys, key=lambda k: _order(pilot_id, k))
        n_holdout = math.floor(len(ordered) * fraction + 0.5)
        for i, key in enumerate(ordered):
            arms[key] = "holdout" if i < n_holdout else "treatment"
    return arms
