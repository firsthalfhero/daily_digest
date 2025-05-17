import pytest
from src.core.monitoring.health import HealthCheckSystem

def test_register_and_run_health_check():
    hcs = HealthCheckSystem()
    hcs.register_check('db', lambda: (True, 'OK'))
    results = hcs.run_checks()
    assert results['db']['status'] is True
    assert results['db']['message'] == 'OK'

def test_health_check_failure():
    hcs = HealthCheckSystem()
    def fail_check():
        raise Exception('fail')
    hcs.register_check('fail', fail_check)
    results = hcs.run_checks()
    assert results['fail']['status'] is False
    assert 'fail' in results['fail']['message'] 