from src.digest_email.sender import EmailSender
from src.utils.logging import get_logger

class NotificationSystem:
    def __init__(self, email_sender=None, logger=None):
        self.email_sender = email_sender or EmailSender()
        self.logger = logger or get_logger(__name__)

    def notify(self, subject, message, recipient=None, channels=None):
        channels = channels or ['log']
        if 'email' in channels:
            self.email_sender.send_email(subject=subject, body=message, recipient=recipient)
        if 'log' in channels:
            self.logger.info("notification", subject=subject, message=message, recipient=recipient) 