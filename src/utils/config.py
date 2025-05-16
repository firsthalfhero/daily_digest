"""
Configuration management module for the Daily Digest Assistant.

This module handles loading and validating configuration from environment variables
and provides a secure way to manage API credentials and other settings.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from src.utils.exceptions import ConfigurationError


@dataclass
class MotionAPIConfig:
    """Configuration for Motion API only."""
    motion_api_key: str
    motion_api_url: str
    def __post_init__(self):
        if not self.motion_api_key or not self.motion_api_url:
            raise ConfigurationError("Empty configuration value in MotionAPIConfig")
        if not self.motion_api_url.startswith(("http://", "https://")):
            raise ConfigurationError("Invalid API URL in MotionAPIConfig")


@dataclass
class WeatherAPIConfig:
    """Configuration for Weather API only."""
    weather_api_key: str
    weather_api_url: str
    def __post_init__(self):
        if not self.weather_api_key or not self.weather_api_url:
            raise ConfigurationError("Empty configuration value in WeatherAPIConfig")
        if not self.weather_api_url.startswith(("http://", "https://")):
            raise ConfigurationError("Invalid API URL in WeatherAPIConfig")


@dataclass
class EmailConfig:
    """Configuration for email settings."""
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    sender_email: str
    recipient_email: str


@dataclass
class Config:
    """Main configuration class."""
    # Environment
    env: str
    debug: bool
    
    # APIs
    motion: MotionAPIConfig
    weather: WeatherAPIConfig
    
    # Email
    email: EmailConfig
    
    # AWS
    aws_region: str
    
    # Logging
    log_level: str
    log_file: Path


def load_config(env_prefix: str = "", env_file: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables.
    Args:
        env_prefix: Optional prefix for environment variables.
        env_file: Optional path to a .env file to load.
    """
    if env_file:
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
    def get_env(key: str) -> str:
        return _get_required_env(f"{env_prefix}{key}")
    # Check for all required environment variables before instantiating Config
    required_keys = [
        "MOTION_API_KEY", "MOTION_API_URL",
        "WEATHER_API_KEY", "WEATHER_API_URL",
        "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD",
        "SENDER_EMAIL", "RECIPIENT_EMAIL"
    ]
    missing_vars = [f"{env_prefix}{key}" for key in required_keys if not os.getenv(f"{env_prefix}{key}")]
    if missing_vars:
        raise ConfigurationError(
            f"Required environment variable(s) {', '.join(missing_vars)} is not set",
            details={"missing_vars": missing_vars}
        )
    try:
        config = Config(
            env=os.getenv(f"{env_prefix}ENV", "development"),
            debug=os.getenv(f"{env_prefix}DEBUG", "false").lower() == "true",
            motion=MotionAPIConfig(
                motion_api_key=get_env("MOTION_API_KEY"),
                motion_api_url=get_env("MOTION_API_URL"),
            ),
            weather=WeatherAPIConfig(
                weather_api_key=get_env("WEATHER_API_KEY"),
                weather_api_url=get_env("WEATHER_API_URL"),
            ),
            email=EmailConfig(
                smtp_host=get_env("SMTP_HOST"),
                smtp_port=int(get_env("SMTP_PORT")),
                smtp_username=get_env("SMTP_USERNAME"),
                smtp_password=get_env("SMTP_PASSWORD"),
                sender_email=get_env("SENDER_EMAIL"),
                recipient_email=get_env("RECIPIENT_EMAIL"),
            ),
            aws_region=os.getenv(f"{env_prefix}AWS_REGION", "ap-southeast-2"),
            log_level=os.getenv(f"{env_prefix}LOG_LEVEL", "INFO"),
            log_file=Path(os.getenv(f"{env_prefix}LOG_FILE", "logs/daily_digest.log")),
        )
        _validate_config(config)
        return config
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {str(e)}")


def _get_required_env(key: str) -> str:
    """Get a required environment variable."""
    value = os.getenv(key)
    if not value:
        raise ConfigurationError(f"Required environment variable {key} is not set", details={"missing_vars": [key]})
    return value


def _validate_config(config: Config) -> None:
    """Validate the configuration."""
    # Validate email configuration
    if not config.email.sender_email or "@" not in config.email.sender_email:
        raise ConfigurationError("Invalid sender email address")
    if not config.email.recipient_email or "@" not in config.email.recipient_email:
        raise ConfigurationError("Invalid recipient email address")
    
    # Validate API URLs
    if not config.motion.motion_api_url.startswith(("http://", "https://")):
        raise ConfigurationError("Invalid Motion API URL")
    if not config.weather.weather_api_url.startswith(("http://", "https://")):
        raise ConfigurationError("Invalid Weather API URL")
    
    # Validate log level
    valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if config.log_level.upper() not in valid_log_levels:
        raise ConfigurationError(f"Invalid log level. Must be one of: {valid_log_levels}")


def create_config_template(directory: Optional[Path] = None) -> None:
    """Create a template .env file if it doesn't exist."""
    template = """# Environment
ENV=development
DEBUG=false

# Motion API
MOTION_API_KEY=your_motion_api_key_here
MOTION_API_URL=https://api.motion.dev/v1

# Weather API
WEATHER_API_KEY=your_weather_api_key_here
WEATHER_API_URL=https://api.weatherapi.com/v1

# Email Configuration
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
SENDER_EMAIL=digest@example.com
RECIPIENT_EMAIL=user@example.com

# AWS
AWS_REGION=ap-southeast-2

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/daily_digest.log
"""
    if directory is None:
        env_path = Path(".env.template")
    else:
        env_path = Path(directory) / ".env.template"
    if not env_path.exists():
        env_path.write_text(template)
        print(f"Created configuration template at {env_path}")
    else:
        print(f"Configuration template already exists at {env_path}") 