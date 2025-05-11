"""Tests for the configuration management module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.config import Config, load_config, create_config_template


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    return {
        "ENV": "test",
        "DEBUG": "true",
        "MOTION_API_KEY": "test_motion_key",
        "MOTION_API_URL": "https://api.motion.dev/v1",
        "WEATHER_API_KEY": "test_weather_key",
        "WEATHER_API_URL": "https://api.weatherapi.com/v1",
        "SMTP_HOST": "smtp.test.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "test_user",
        "SMTP_PASSWORD": "test_pass",
        "SENDER_EMAIL": "test@example.com",
        "RECIPIENT_EMAIL": "user@example.com",
        "AWS_REGION": "ap-southeast-2",
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE": "logs/test.log",
    }


def test_load_config_success(mock_env_vars):
    """Test successful configuration loading."""
    with patch.dict(os.environ, mock_env_vars):
        config = load_config()
        
        assert config.env == "test"
        assert config.debug is True
        assert config.motion.motion_api_key == "test_motion_key"
        assert config.weather.weather_api_key == "test_weather_key"
        assert config.email.smtp_host == "smtp.test.com"
        assert config.email.smtp_port == 587
        assert config.aws_region == "ap-southeast-2"
        assert config.log_level == "DEBUG"
        assert config.log_file == Path("logs/test.log")


def test_load_config_missing_required():
    """Test configuration loading with missing required variables."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Required environment variable"):
            load_config()


def test_load_config_invalid_email():
    """Test configuration loading with invalid email."""
    with patch.dict(os.environ, {
        "MOTION_API_KEY": "test",
        "MOTION_API_URL": "https://api.motion.dev/v1",
        "WEATHER_API_KEY": "test",
        "WEATHER_API_URL": "https://api.weatherapi.com/v1",
        "SMTP_HOST": "smtp.test.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "test",
        "SMTP_PASSWORD": "test",
        "SENDER_EMAIL": "invalid-email",
        "RECIPIENT_EMAIL": "user@example.com",
    }):
        with pytest.raises(ValueError, match="Invalid sender email address"):
            load_config()


def test_load_config_invalid_api_url():
    """Test configuration loading with invalid API URL."""
    with patch.dict(os.environ, {
        "MOTION_API_KEY": "test",
        "MOTION_API_URL": "invalid-url",
        "WEATHER_API_KEY": "test",
        "WEATHER_API_URL": "https://api.weatherapi.com/v1",
        "SMTP_HOST": "smtp.test.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "test",
        "SMTP_PASSWORD": "test",
        "SENDER_EMAIL": "test@example.com",
        "RECIPIENT_EMAIL": "user@example.com",
    }):
        with pytest.raises(ValueError, match="Invalid Motion API URL"):
            load_config()


def test_load_config_invalid_log_level():
    """Test configuration loading with invalid log level."""
    with patch.dict(os.environ, {
        "MOTION_API_KEY": "test",
        "MOTION_API_URL": "https://api.motion.dev/v1",
        "WEATHER_API_KEY": "test",
        "WEATHER_API_URL": "https://api.weatherapi.com/v1",
        "SMTP_HOST": "smtp.test.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "test",
        "SMTP_PASSWORD": "test",
        "SENDER_EMAIL": "test@example.com",
        "RECIPIENT_EMAIL": "user@example.com",
        "LOG_LEVEL": "INVALID",
    }):
        with pytest.raises(ValueError, match="Invalid log level"):
            load_config()


def test_create_config_template(tmp_path):
    """Test creation of configuration template."""
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        create_config_template()
        
        template_path = tmp_path / ".env.template"
        assert template_path.exists()
        
        content = template_path.read_text()
        assert "MOTION_API_KEY=" in content
        assert "WEATHER_API_KEY=" in content
        assert "SMTP_HOST=" in content
        assert "LOG_LEVEL=" in content 