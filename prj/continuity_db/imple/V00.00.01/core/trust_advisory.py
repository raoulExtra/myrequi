"""Bounded, advisory-only trust and evidence assessment.

This module recommends an action posture; it never authorizes or executes actions.
Scores are normalized to 0..1 and risk has separate confidence and action effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

FACTORS = ("quality", "provenance", "domain_fit", "freshness")
WEIGHTS = {"quality": 0.40, "provenance": 0.30, "domain_fit": 0.20, "freshness": 0.10}
RISK_BANDS = ("very low", "low", "moderate", "high", "very high")
POSTURES = ("allow", "caution", "verify", "review", "defer")

# Initial profiles are policy placeholders, intentionally visible and auditable.
# Floors are Q, P, D; freshness is domain-sensitive and therefore omitted here.
PROFILES = {
    "medical_advice": (
        (0.20, 0.25, 0.20), (0.35, 0.40, 0.35), (0.50, 0.55, 0.50),
        (0.65, 0.70, 0.65), (0.80, 0.85, 0.80),
    ),
    "high_impact_software": (
        (0.20, 0.20, 0.20), (0.35, 0.35, 0.35), (0.50, 0.50, 0.50),
        (0.65, 0.65, 0.65), (0.80, 0.80, 0.80),
    ),
}
ACTION_THRESHOLDS = (0.35, 0.50, 0.65, 0.80, 0.90)
REVIEW_MARGIN = 0.15


@dataclass(frozen=True)
class AdvisoryAssessment:
    domain: str
    risk_band: str
    base_confidence: float
    adjusted_confidence: float
    conflict: float
    action_threshold: float
    posture: str
    failed_floors: tuple[str, ...]
    uncertainty: tuple[str, ...]
    advisory_only: bool = True


def _score(value: float, name: str) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


def risk_band(risk: float) -> str:
    risk = _score(risk, "risk")
    index = min(4, int(risk * 5))
    return RISK_BANDS[index]


def _risk_index(risk: float) -> int:
    return min(4, int(_score(risk, "risk") * 5))


def assess(
    *, domain: str, quality: float, provenance: float, domain_fit: float,
    freshness: float, risk: float, conflict: float = 0.0,
) -> AdvisoryAssessment:
    if domain not in PROFILES:
        raise ValueError(f"unknown trust domain: {domain}")
    values = {"quality": _score(quality, "quality"), "provenance": _score(provenance, "provenance"),
              "domain_fit": _score(domain_fit, "domain_fit"), "freshness": _score(freshness, "freshness")}
    conflict = _score(conflict, "conflict")
    index = _risk_index(risk)
    base = sum(WEIGHTS[key] * values[key] for key in FACTORS)
    # Conflict is asymmetric: it penalizes confidence but is not a positive score.
    adjusted = max(0.0, base - (0.20 * conflict) - (0.05 * index))
    q_min, p_min, d_min = PROFILES[domain][index]
    failed = tuple(name for name, value, floor in (
        ("quality", quality, q_min), ("provenance", provenance, p_min),
        ("domain_fit", domain_fit, d_min),
    ) if float(value) < floor)
    uncertainty = list(failed)
    if freshness < 0.4:
        uncertainty.append("freshness")
    if conflict >= 0.5:
        uncertainty.append("conflict")
    threshold = ACTION_THRESHOLDS[index]
    conflict_escalation = conflict >= 0.70 and index >= 3
    conflict_review = conflict >= 0.50 and index >= 1
    domain_conflict_defer = domain == "medical_advice" and conflict_escalation
    domain_conflict_review = domain == "high_impact_software" and conflict_escalation and index == 3
    if failed or adjusted < threshold or conflict_escalation or conflict_review:
        # Review is a bounded intermediate posture: a moderate shortfall at
        # elevated risk needs human/domain review, not automatic deferral.
        severe_floor_failure = index >= 2 and any(name in {"quality", "provenance"} for name in failed)
        moderate_shortfall = adjusted >= threshold - REVIEW_MARGIN
        if domain_conflict_defer or index >= 4 or severe_floor_failure:
            posture = "defer"
        elif domain_conflict_review:
            posture = "review"
        elif not moderate_shortfall:
            posture = "defer"
        elif index < 2 and not conflict_review:
            posture = "caution"
        else:
            posture = "review"
    elif adjusted < threshold + 0.10:
        posture = "caution"
    else:
        posture = "allow"
    return AdvisoryAssessment(domain, risk_band(risk), base, adjusted, conflict, threshold,
                              posture, failed, tuple(uncertainty))

