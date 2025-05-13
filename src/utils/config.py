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


@dataclass
class MotionAPIConfig:
    """Configuration for Motion API only."""
    motion_api_key: str
    motion_api_url: str


@dataclass
class WeatherAPIConfig:
    """Configuration for Weather API only."""
    weather_api_key: str
    weather_api_url: str


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


def load_config() -> Config:
    """
    Load configuration from environment variables.
    
    Returns:
        Config: Validated configuration object.
        
    Raises:
        ValueError: If required configuration is missing or invalid.
    """
    # Load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    
    # Validate and load configuration
    try:
        config = Config(
            # Environment
            env=os.getenv("ENV", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            
            # APIs
            motion=MotionAPIConfig(
                motion_api_key=_get_required_env("MOTION_API_KEY"),
                motion_api_url=_get_required_env("MOTION_API_URL"),
            ),
            weather=WeatherAPIConfig(
                weather_api_key=_get_required_env("WEATHER_API_KEY"),
                weather_api_url=_get_required_env("WEATHER_API_URL"),
            ),
            
            # Email
            email=EmailConfig(
                smtp_host=_get_required_env("SMTP_HOST"),
                smtp_port=int(_get_required_env("SMTP_PORT")),
                smtp_username=_get_required_env("SMTP_USERNAME"),
                smtp_password=_get_required_env("SMTP_PASSWORD"),
                sender_email=_get_required_env("SENDER_EMAIL"),
                recipient_email=_get_required_env("RECIPIENT_EMAIL"),
            ),
            
            # AWS
            aws_region=os.getenv("AWS_REGION", "ap-southeast-2"),
            
            # Logging
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=Path(os.getenv("LOG_FILE", "logs/daily_digest.log")),
        )
        
        # Validate configuration
        _validate_config(config)
        
        return config
        
    except Exception as e:
        raise ValueError(f"Failed to load configuration: {str(e)}")


def _get_required_env(key: str) -> str:
    """Get a required environment variable."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def _validate_config(config: Config) -> None:
    """Validate the configuration."""
    # Validate email configuration
    if not config.email.sender_email or "@" not in config.email.sender_email:
        raise ValueError("Invalid sender email address")
    if not config.email.recipient_email or "@" not in config.email.recipient_email:
        raise ValueError("Invalid recipient email address")
    
    # Validate API URLs
    if not config.motion.motion_api_url.startswith(("http://", "https://")):
        raise ValueError("Invalid Motion API URL")
    if not config.weather.weather_api_url.startswith(("http://", "https://")):
        raise ValueError("Invalid Weather API URL")
    
    # Validate log level
    valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if config.log_level.upper() not in valid_log_levels:
        raise ValueError(f"Invalid log level. Must be one of: {valid_log_levels}")


def create_config_template() -> None:
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
    
    env_path = Path(".env.template")
    if not env_path.exists():
        env_path.write_text(template)
        print(f"Created configuration template at {env_path}")
    else:
        print(f"Configuration template already exists at {env_path}") 