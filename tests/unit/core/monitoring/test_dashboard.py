import pytest
from src.core.monitoring.dashboard import MonitoringDashboard
from src.core.monitoring.monitor import MonitoringSystem
from src.core.monitoring.alert import AlertSystem
from src.core.monitoring.health import HealthCheckSystem

def test_dashboard_status_aggregation():
    monitor = MonitoringSystem()
    alert = AlertSystem()
    health = HealthCheckSystem()
    monitor.track_metric('cpu', 0.7)
    monitor.track_kpi('uptime', 99.8)
    alert.register_rule({'metric': 'cpu', 'condition': lambda v: v > 0.8, 'channels': ['log']})
    health.register_check('db', lambda: (True, 'OK'))
    dashboard = MonitoringDashboard(monitor=monitor, alert=alert, health=health)
    status = dashboard.get_status()
    assert status['metrics'] == {'cpu': 0.7}
    assert status['kpis'] == {'uptime': 99.8}
    assert status['alerts'] == ['cpu']
    assert status['health']['db']['status'] is True 