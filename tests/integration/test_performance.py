import time
import pytest
from src.core.monitoring.monitor import MonitoringSystem

def test_monitoring_system_performance():
    ms = MonitoringSystem()
    start = time.time()
    for i in range(10000):
        ms.track_metric(f'metric_{i}', i)
    duration = time.time() - start
    # Assert that the operation completes within a reasonable time (e.g., 1 second)
    assert duration < 1.0, f"Performance degraded: {duration}s" 