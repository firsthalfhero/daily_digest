import pytest
from unittest.mock import MagicMock
from src.core.monitoring.alert import AlertSystem

def test_register_and_trigger_alert():
    mock_email = MagicMock()
    mock_logger = MagicMock()
    alert = AlertSystem(email_sender=mock_email, logger=mock_logger)
    rule = {
        'metric': 'cpu',
        'condition': lambda v: v > 0.8,
        'channels': ['email', 'log'],
        'recipient': 'test@example.com',
        'description': 'CPU usage high',
    }
    alert.register_rule(rule)
    alert.check_and_alert('cpu', 0.9)
    mock_email.send_email.assert_called_once()
    mock_logger.warning.assert_called_once()

def test_no_alert_when_condition_false():
    mock_email = MagicMock()
    mock_logger = MagicMock()
    alert = AlertSystem(email_sender=mock_email, logger=mock_logger)
    rule = {
        'metric': 'cpu',
        'condition': lambda v: v > 0.8,
        'channels': ['email', 'log'],
        'recipient': 'test@example.com',
        'description': 'CPU usage high',
    }
    alert.register_rule(rule)
    alert.check_and_alert('cpu', 0.5)
    mock_email.send_email.assert_not_called()
    mock_logger.warning.assert_not_called() 