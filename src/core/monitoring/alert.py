from src.digest_email.sender import EmailSender
from src.utils.logging import get_logger

class AlertSystem:
    def __init__(self, email_sender=None, logger=None):
        self.rules = []
        self.email_sender = email_sender or EmailSender()
        self.logger = logger or get_logger(__name__)

    def register_rule(self, rule):
        self.rules.append(rule)

    def check_and_alert(self, metric_name, value):
        for rule in self.rules:
            if rule['metric'] == metric_name and rule['condition'](value):
                self.send_alert(rule, value)

    def send_alert(self, rule, value):
        message = f"ALERT: {rule['metric']} triggered with value {value}. {rule.get('description', '')}"
        if 'email' in rule['channels']:
            self.email_sender.send_email(
                subject=f"Alert: {rule['metric']}",
                body=message,
                recipient=rule.get('recipient')
            )
        if 'log' in rule['channels']:
            self.logger.warning("alert_triggered", metric=rule['metric'], value=value, description=rule.get('description', '')) 