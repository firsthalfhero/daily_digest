"""Pytest configuration and fixtures."""

import os
from typing import Generator

import pytest
from moto import mock_secretsmanager, mock_ses

@pytest.fixture(autouse=True)
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-2"

@pytest.fixture
def mock_secrets() -> Generator:
    """Mock AWS Secrets Manager."""
    with mock_secretsmanager():
        yield

@pytest.fixture
def mock_email() -> Generator:
    """Mock AWS SES."""
    with mock_ses():
        yield

@pytest.fixture
def test_config() -> dict:
    """Test configuration."""
    return {
        "MOTION_API_KEY": "test_motion_key",
        "WEATHER_API_KEY": "test_weather_key",
        "EMAIL_SERVICE_KEY": "test_email_key",
        "AWS_REGION": "ap-southeast-2",
        "ENVIRONMENT": "test",
        "EMAIL_FROM": "test@example.com",
        "EMAIL_TO": "recipient@example.com",
        "EMAIL_SUBJECT_PREFIX": "[Test]",
        "LOCATION_LATITUDE": -33.8688,
        "LOCATION_LONGITUDE": 151.2093,
        "LOCATION_NAME": "Sydney",
        "DELIVERY_TIME": "06:30",
        "TIMEZONE": "Australia/Sydney",
    } 