import pytest
from unittest.mock import patch, MagicMock
from src.digest_email.sender import EmailSender
from src.utils.config import load_config

@pytest.fixture
def email_sender():
    config = load_config()
    return EmailSender(config=config)

@patch('smtplib.SMTP')
def test_send_email_success(mock_smtp, email_sender):
    instance = mock_smtp.return_value.__enter__.return_value
    result = email_sender.send_email('Test Subject', 'Test Body', 'recipient@example.com')
    assert result is True
    instance.starttls.assert_called_once()
    instance.login.assert_called_once()
    instance.sendmail.assert_called_once()

@patch('smtplib.SMTP', side_effect=Exception('SMTP failure'))
def test_send_email_retries_and_fails(mock_smtp, email_sender):
    with pytest.raises(Exception):
        email_sender.send_email('Test Subject', 'Test Body', 'recipient@example.com', retries=2)
    assert mock_smtp.call_count == 2

@patch('smtplib.SMTP')
def test_send_templated_email_success(mock_smtp, email_sender):
    context = {'user_name': 'Test', 'greeting_time': 'morning', 'calendar_events': [], 'weather': None, 'daily_summary': 'Summary'}
    result = email_sender.send_templated_email('daily_digest', context, 'recipient@example.com')
    assert result is True
    instance = mock_smtp.return_value.__enter__.return_value
    instance.sendmail.assert_called_once() 