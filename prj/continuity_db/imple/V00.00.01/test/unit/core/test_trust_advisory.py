import pytest

from trust_advisory import assess, risk_band


def test_risk_bands_have_explicit_boundaries():
    assert [risk_band(value) for value in (0, .2, .4, .6, .8, 1)] == [
        'very low', 'low', 'moderate', 'high', 'very high', 'very high'
    ]


def test_risk_is_conservative_and_advisory_only():
    low = assess(domain='medical_advice', quality=.8, provenance=.8,
                 domain_fit=.8, freshness=.8, risk=.1)
    high = assess(domain='medical_advice', quality=.8, provenance=.8,
                  domain_fit=.8, freshness=.8, risk=.9)
    assert high.adjusted_confidence < low.adjusted_confidence
    assert high.action_threshold > low.action_threshold
    assert high.advisory_only is True
    assert high.posture == 'defer'


def test_factor_floor_prevents_weak_provenance_from_being_hidden():
    result = assess(domain='medical_advice', quality=.95, provenance=.20,
                    domain_fit=.90, freshness=.90, risk=.1)
    assert 'provenance' in result.failed_floors
    assert result.posture == 'caution'


def test_domain_specific_conflict_gates_preserve_safety_invariant():
    medical = assess(domain='medical_advice', quality=.9, provenance=.9,
                     domain_fit=.9, freshness=.9, conflict=.8, risk=.7)
    software = assess(domain='high_impact_software', quality=.9, provenance=.9,
                      domain_fit=.9, freshness=.9, conflict=.8, risk=.7)
    assert medical.posture == 'defer'
    assert software.posture == 'review'
    assert medical.posture not in ('allow', 'caution')
    assert software.posture not in ('allow', 'caution')


def test_unknown_domain_is_rejected():
    with pytest.raises(ValueError, match='unknown trust domain'):
        assess(domain='unknown', quality=.5, provenance=.5,
               domain_fit=.5, freshness=.5, risk=.5)
