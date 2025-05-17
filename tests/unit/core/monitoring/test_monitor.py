import pytest
from src.core.monitoring.monitor import MonitoringSystem

def test_track_metric_and_get_metrics():
    ms = MonitoringSystem()
    ms.track_metric('cpu', 0.5)
    assert ms.get_metrics() == {'cpu': 0.5}
    assert ('cpu', 0.5) in ms.get_data()

def test_track_kpi_and_get_kpis():
    ms = MonitoringSystem()
    ms.track_kpi('uptime', 99.9)
    assert ms.get_kpis() == {'uptime': 99.9}
    assert ('uptime', 99.9) in ms.get_data() 