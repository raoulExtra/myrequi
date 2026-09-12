from trust_pilot import run_sweep


def test_balanced_five_band_sweep_is_monotonic_and_advisory_only():
    result = run_sweep()
    assert result['advisory_only'] is True
    assert len(result['rows']) == 10
    for domain in ('medical_advice', 'high_impact_software'):
        rows = [row for row in result['rows'] if row['domain'] == domain]
        assert [row['action_threshold'] for row in rows] == sorted(row['action_threshold'] for row in rows)
        assert all(row['advisory_only'] for row in rows)


def test_realistic_cases_remain_advisory_only():
    from trust_pilot import realistic_cases
    result = realistic_cases()
    assert len(result['cases']) == 4
    assert result['advisory_only'] is True
    assert result['execution_performed'] is False
    assert all(row['advisory_only'] for row in result['cases'])
