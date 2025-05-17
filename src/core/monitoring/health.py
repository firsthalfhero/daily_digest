class HealthCheckSystem:
    def __init__(self):
        self.checks = []

    def register_check(self, name, check_fn):
        self.checks.append((name, check_fn))

    def run_checks(self):
        results = {}
        for name, check_fn in self.checks:
            try:
                status, msg = check_fn()
            except Exception as e:
                status, msg = False, str(e)
            results[name] = {'status': status, 'message': msg}
        return results 