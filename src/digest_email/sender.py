import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from src.utils.config import load_config
from src.utils.logging import get_logger
from src.digest_email.template_engine import EmailTemplateEngine

# Deprecated: Old SMTP-based sender
# class EmailSender:
#     ...

class EmailSender:
    def __init__(self, config=None, logger=None):
        self.config = config or load_config()
        self.logger = logger or get_logger(__name__)
        self.template_engine = EmailTemplateEngine()

    def send_email(self, subject: str, body: str, recipient: Optional[str] = None, html: Optional[str] = None, retries: int = 3):
        recipient = recipient or self.config.email.recipient_email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.config.email.sender_email
        msg['To'] = recipient
        part1 = MIMEText(body, 'plain')
        msg.attach(part1)
        if html:
            part2 = MIMEText(html, 'html')
            msg.attach(part2)
        attempt = 0
        while attempt < retries:
            try:
                with smtplib.SMTP(self.config.email.smtp_host, self.config.email.smtp_port) as server:
                    if (
                        self.config.email.smtp_username not in [None, '', 'none']
                        and self.config.email.smtp_password not in [None, '', 'none']
                    ):
                        server.starttls()
                        server.login(self.config.email.smtp_username, self.config.email.smtp_password)
                    server.sendmail(self.config.email.sender_email, recipient, msg.as_string())
                self.logger.info("email_sent", to=recipient, subject=subject)
                return True
            except Exception as e:
                attempt += 1
                self.logger.error("email_delivery_failed", to=recipient, subject=subject, attempt=attempt, error=str(e))
                if attempt >= retries:
                    raise

    def send_templated_email(self, template_name: str, context: dict, recipient: Optional[str] = None, subject: Optional[str] = None, retries: int = 3):
        body = self.template_engine.render(template_name, context, plain=True)
        html = self.template_engine.render(template_name, context, plain=False)
        subject = subject or context.get('subject', 'Daily Digest')
        return self.send_email(subject, body, recipient, html, retries)

# TODO: Integrate EmailTemplateEngine for rendering emails 