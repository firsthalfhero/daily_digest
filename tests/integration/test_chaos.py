import pytest
from src.core.monitoring.health import HealthCheckSystem

def test_health_check_chaos():
    hcs = HealthCheckSystem()
    def flaky_check():
        raise RuntimeError('Simulated failure')
    hcs.register_check('flaky', flaky_check)
    results = hcs.run_checks()
    assert results['flaky']['status'] is False
    assert 'Simulated failure' in results['flaky']['message'] 