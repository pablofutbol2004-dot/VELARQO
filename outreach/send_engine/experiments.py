"""Experiments: config/experiments/<name>.json defines the arms of a test.

Cold-email tests ("stage": "cold_email") are assigned per cohort, balanced
round-robin over the priority-sorted list. Sales-call tests (pricing) are
assigned per company by a stable hash, so a prospect always hears the same
price. Results are read with probability-of-best (Beta posteriors), which
stays honest at the small numbers Velarqo will have for months.
"""

import hashlib
import json
import math
import random
import re
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).parents[2] / "config" / "experiments"
_FIELDS = re.compile(r"\{([a-z_]+)\}")
ALLOWED_FIELDS = {"company"}


def load(name: str) -> dict:
    path = EXPERIMENTS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No experiment config at {path}")
    experiment = json.loads(path.read_text(encoding="utf-8"))
    validate(experiment)
    return experiment


def validate(experiment: dict) -> None:
    for key in ("name", "stage", "hypothesis", "primary_metric", "decision_rule", "arms"):
        if not experiment.get(key):
            raise ValueError(f"experiment is missing '{key}'")
    if len(experiment["arms"]) < 2:
        raise ValueError("an experiment needs at least two arms")
    if experiment["stage"] == "cold_email":
        for arm in experiment["arms"]:
            unknown = set(_FIELDS.findall(arm["subject"] + arm["body"])) - ALLOWED_FIELDS
            if unknown:
                raise ValueError(f"arm {arm['key']} uses unknown fields: {sorted(unknown)}")


def assigned_arm(experiment: dict, company_id: str) -> dict:
    """Stable per-company arm (for tests run in conversations, e.g. pricing)."""
    digest = hashlib.sha1(f"{experiment['name']}:{company_id}".encode()).hexdigest()
    return experiment["arms"][int(digest, 16) % len(experiment["arms"])]


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    if trials == 0:
        return (0.0, 1.0)
    p = successes / trials
    centre = (p + z * z / (2 * trials)) / (1 + z * z / trials)
    margin = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / (1 + z * z / trials)
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def probability_best(arms: list[tuple[int, int]], draws: int = 20000, seed: int = 7) -> list[float]:
    """P(each arm has the highest true rate), Beta(1+s, 1+f) posteriors."""
    rng = random.Random(seed)
    wins = [0] * len(arms)
    for _ in range(draws):
        samples = [rng.betavariate(1 + s, 1 + max(n - s, 0)) for s, n in arms]
        wins[samples.index(max(samples))] += 1
    return [w / draws for w in wins]


def verdict(experiment: dict, rows: list[dict], metric: str = "positive") -> str:
    """Plain-English read of a cold-email test against its decision rule."""
    minimum = experiment.get("min_sent_per_arm", 300)
    probs = probability_best([(r[metric], r["sent"]) for r in rows])
    best = max(range(len(rows)), key=probs.__getitem__)
    if min(r["sent"] for r in rows) < minimum:
        return (f"Too early: needs {minimum} first emails per arm (smallest arm has {min(r['sent'] for r in rows)}). "
                f"Leading: {rows[best]['arm']} ({probs[best]:.0%} chance best) - don't act on it yet.")
    if probs[best] >= 0.9:
        return f"Decision: keep {rows[best]['arm']} ({probs[best]:.0%} chance it has the higher {metric} rate)."
    return (f"No clear winner ({rows[best]['arm']} leads at {probs[best]:.0%}). Difference too small to matter at "
            f"our volume: keep the arm with more booked calls and test something bigger.")
