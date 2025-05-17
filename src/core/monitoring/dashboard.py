from src.core.monitoring.monitor import MonitoringSystem
from src.core.monitoring.alert import AlertSystem
from src.core.monitoring.health import HealthCheckSystem

class MonitoringDashboard:
    def __init__(self, monitor=None, alert=None, health=None):
        self.monitor = monitor or MonitoringSystem()
        self.alert = alert or AlertSystem()
        self.health = health or HealthCheckSystem()

    def get_status(self):
        return {
            'metrics': self.monitor.get_metrics(),
            'kpis': self.monitor.get_kpis(),
            'alerts': [rule['metric'] for rule in self.alert.rules],
            'health': self.health.run_checks(),
        } 