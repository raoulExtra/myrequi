"""Controlled five-band pilot for the advisory trust model."""
from __future__ import annotations

import json
from trust_advisory import assess

RISK_LEVELS = (0.1, 0.3, 0.5, 0.7, 0.9)
DOMAINS = ("medical_advice", "high_impact_software")


def run_sweep(*, quality=.8, provenance=.8, domain_fit=.8, freshness=.8):
    """Run a same-score risk sweep; returns advisory results only."""
    rows = []
    for domain in DOMAINS:
        for risk in RISK_LEVELS:
            result = assess(domain=domain, quality=quality, provenance=provenance,
                            domain_fit=domain_fit, freshness=freshness, risk=risk)
            rows.append({"domain": domain, "risk": risk, **result.__dict__})
    for domain in DOMAINS:
        domain_rows = [row for row in rows if row["domain"] == domain]
        thresholds = [row["action_threshold"] for row in domain_rows]
        if thresholds != sorted(thresholds):
            raise AssertionError(f"non-monotonic action threshold for {domain}")
    return {"profile": {"quality": quality, "provenance": provenance,
                         "domain_fit": domain_fit, "freshness": freshness},
            "rows": rows, "advisory_only": True}


def realistic_cases():
    """Evaluate representative cases without providing advice or executing actions."""
    cases = (
        {"case_key": "medical_conflicting_credible_evidence", "domain": "medical_advice",
         "quality": .65, "provenance": .85, "domain_fit": .75, "freshness": .85, "risk": .70},
        {"case_key": "medical_ai_summary_weak_provenance", "domain": "medical_advice",
         "quality": .90, "provenance": .15, "domain_fit": .75, "freshness": .80, "risk": .70},
        {"case_key": "medical_guidance_guideline_supported", "domain": "medical_advice",
         "quality": .82, "provenance": .90, "domain_fit": .88, "freshness": .86, "risk": .70},
        {"case_key": "software_production_schema_change", "domain": "high_impact_software",
         "quality": .86, "provenance": .84, "domain_fit": .92, "freshness": .90, "risk": .90},
    )
    results = []
    for case in cases:
        result = assess(**{key: case[key] for key in
                           ("domain", "quality", "provenance", "domain_fit", "freshness", "risk")})
        results.append({**case, **result.__dict__})
    return {"cases": results, "advisory_only": True,
            "execution_performed": False}


def to_json(**kwargs):
    return json.dumps(run_sweep(**kwargs), ensure_ascii=False)
