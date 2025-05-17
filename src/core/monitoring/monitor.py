class MonitoringSystem:
    def __init__(self):
        self.metrics = {}
        self.kpis = {}
        self.data = []

    def track_metric(self, name, value):
        self.metrics[name] = value
        self.data.append((name, value))

    def track_kpi(self, name, value):
        self.kpis[name] = value
        self.data.append((name, value))

    def get_metrics(self):
        return self.metrics

    def get_kpis(self):
        return self.kpis

    def get_data(self):
        return self.data 