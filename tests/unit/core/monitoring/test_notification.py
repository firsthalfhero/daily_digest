import pytest
from unittest.mock import MagicMock
from src.core.monitoring.notification import NotificationSystem

def test_notify_email_and_log():
    mock_email = MagicMock()
    mock_logger = MagicMock()
    ns = NotificationSystem(email_sender=mock_email, logger=mock_logger)
    ns.notify('Test', 'Message', recipient='test@example.com', channels=['email', 'log'])
    mock_email.send_email.assert_called_once_with(subject='Test', body='Message', recipient='test@example.com')
    mock_logger.info.assert_called_once()

def test_notify_log_only():
    mock_email = MagicMock()
    mock_logger = MagicMock()
    ns = NotificationSystem(email_sender=mock_email, logger=mock_logger)
    ns.notify('Test', 'Message', channels=['log'])
    mock_email.send_email.assert_not_called()
    mock_logger.info.assert_called_once() 