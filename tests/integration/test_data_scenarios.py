import pytest
from src.core.monitoring.monitor import MonitoringSystem

def test_multiple_user_profiles_and_edge_cases():
    ms = MonitoringSystem()
    user_profiles = [
        {'user_id': 'user1', 'metric': 10},
        {'user_id': 'user2', 'metric': 0},
        {'user_id': 'user3', 'metric': -1},  # edge case
        {'user_id': 'user4', 'metric': None},  # incomplete data
    ]
    for profile in user_profiles:
        try:
            ms.track_metric(f"user_{profile['user_id']}_metric", profile['metric'])
        except Exception as e:
            # Only None should raise an error
            assert profile['metric'] is None
    # Check that valid metrics are tracked
    assert ms.get_metrics()['user_user1_metric'] == 10
    assert ms.get_metrics()['user_user2_metric'] == 0
    assert ms.get_metrics()['user_user3_metric'] == -1 