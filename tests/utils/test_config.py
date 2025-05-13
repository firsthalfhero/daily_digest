"""Tests for the configuration management module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.config import (
    Config, MotionAPIConfig, WeatherAPIConfig, EmailConfig,
    load_config, create_config_template
)
from src.utils.exceptions import ConfigurationError


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


class TestMotionAPIConfig:
    """Test MotionAPIConfig functionality."""

    def test_init_with_valid_values(self):
        """Test initializing with valid configuration values."""
        config = MotionAPIConfig(
            motion_api_key="test_motion_key",
            motion_api_url="https://api.motion.dev/v1",
        )
        assert config.motion_api_key == "test_motion_key"
        assert config.motion_api_url == "https://api.motion.dev/v1"

    def test_init_with_empty_values(self):
        """Test initializing with empty configuration values."""
        with pytest.raises(ValueError) as exc_info:
            MotionAPIConfig(
                motion_api_key="",
                motion_api_url="https://api.motion.dev/v1",
            )
        assert "Empty configuration value" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            MotionAPIConfig(
                motion_api_key="test_motion_key",
                motion_api_url="",
            )
        assert "Empty configuration value" in str(exc_info.value)

    def test_init_with_invalid_url(self):
        """Test initializing with invalid API URL."""
        with pytest.raises(ValueError) as exc_info:
            MotionAPIConfig(
                motion_api_key="test_motion_key",
                motion_api_url="invalid_url",
            )
        assert "Invalid API URL" in str(exc_info.value)


class TestWeatherAPIConfig:
    """Test WeatherAPIConfig functionality."""

    def test_init_with_valid_values(self):
        """Test initializing with valid configuration values."""
        config = WeatherAPIConfig(
            weather_api_key="test_weather_key",
            weather_api_url="https://api.weatherapi.com/v1",
        )
        assert config.weather_api_key == "test_weather_key"
        assert config.weather_api_url == "https://api.weatherapi.com/v1"

    def test_init_with_empty_values(self):
        """Test initializing with empty configuration values."""
        with pytest.raises(ValueError) as exc_info:
            WeatherAPIConfig(
                weather_api_key="",
                weather_api_url="https://api.weatherapi.com/v1",
            )
        assert "Empty configuration value" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            WeatherAPIConfig(
                weather_api_key="test_weather_key",
                weather_api_url="",
            )
        assert "Empty configuration value" in str(exc_info.value)

    def test_init_with_invalid_url(self):
        """Test initializing with invalid API URL."""
        with pytest.raises(ValueError) as exc_info:
            WeatherAPIConfig(
                weather_api_key="test_weather_key",
                weather_api_url="invalid_url",
            )
        assert "Invalid API URL" in str(exc_info.value)


class TestLoadConfig:
    """Test load_config functionality."""

    @pytest.fixture
    def env_vars(self):
        """Create test environment variables."""
        return {
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

    def test_load_config_from_env(self, env_vars):
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            assert isinstance(config.motion, MotionAPIConfig)
            assert isinstance(config.weather, WeatherAPIConfig)
            assert config.motion.motion_api_key == "test_motion_key"
            assert config.motion.motion_api_url == "https://api.motion.dev/v1"
            assert config.weather.weather_api_key == "test_weather_key"
            assert config.weather.weather_api_url == "https://api.weatherapi.com/v1"

    def test_load_config_with_missing_env_vars(self):
        """Test loading configuration with missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config()
            error = exc_info.value
            assert "Missing required environment variables" in str(error)
            assert "MOTION_API_KEY" in error.details["missing_vars"]
            assert "MOTION_API_URL" in error.details["missing_vars"]
            assert "WEATHER_API_KEY" in error.details["missing_vars"]
            assert "WEATHER_API_URL" in error.details["missing_vars"]

    def test_load_config_with_empty_env_vars(self, env_vars):
        """Test loading configuration with empty environment variables."""
        env_vars["MOTION_API_KEY"] = ""
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config()
            error = exc_info.value
            assert "Empty environment variable" in str(error)
            assert "MOTION_API_KEY" in error.details["empty_vars"]

    def test_load_config_with_invalid_urls(self, env_vars):
        """Test loading configuration with invalid API URLs."""
        env_vars["MOTION_API_URL"] = "invalid_url"
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config()
            error = exc_info.value
            assert "Invalid API URL" in str(error)
            assert "MOTION_API_URL" in error.details["invalid_urls"]

        env_vars["MOTION_API_URL"] = "https://api.motion.dev/v1"
        env_vars["WEATHER_API_URL"] = "invalid_url"
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config()
            error = exc_info.value
            assert "Invalid API URL" in str(error)
            assert "WEATHER_API_URL" in error.details["invalid_urls"]

    def test_load_config_with_custom_env_prefix(self, env_vars):
        """Test loading configuration with custom environment variable prefix."""
        custom_env_vars = {
            "CUSTOM_MOTION_API_KEY": env_vars["MOTION_API_KEY"],
            "CUSTOM_MOTION_API_URL": env_vars["MOTION_API_URL"],
            "CUSTOM_WEATHER_API_KEY": env_vars["WEATHER_API_KEY"],
            "CUSTOM_WEATHER_API_URL": env_vars["WEATHER_API_URL"],
        }
        with patch.dict(os.environ, custom_env_vars, clear=True):
            config = load_config(env_prefix="CUSTOM_")
            assert config.motion_api_key == "test_motion_key"
            assert config.motion_api_url == "https://api.motion.dev/v1"
            assert config.weather_api_key == "test_weather_key"
            assert config.weather_api_url == "https://api.weatherapi.com/v1"

    def test_load_config_with_env_file(self, env_vars, tmp_path):
        """Test loading configuration from .env file."""
        env_file = tmp_path / ".env"
        env_content = "\n".join(f"{key}={value}" for key, value in env_vars.items())
        env_file.write_text(env_content)

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(env_file=str(env_file))
            assert config.motion_api_key == "test_motion_key"
            assert config.motion_api_url == "https://api.motion.dev/v1"
            assert config.weather_api_key == "test_weather_key"
            assert config.weather_api_url == "https://api.weatherapi.com/v1"

    def test_load_config_with_invalid_env_file(self, tmp_path):
        """Test loading configuration with invalid .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("invalid_env_content")

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config(env_file=str(env_file))
            error = exc_info.value
            assert "Failed to load environment variables" in str(error)
            assert "env_file" in error.details 