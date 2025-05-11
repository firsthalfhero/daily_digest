"""
Weather data models for the Daily Digest Assistant.

This module defines the data structures and validation logic for weather data
retrieved from the Weather API. It includes unit conversion utilities and data
transformation capabilities.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

from src.utils.exceptions import ValidationError
from src.utils.logging import get_logger
from src.utils.timezone import (
    SYDNEY_TIMEZONE,
    DEFAULT_TIMEZONE,
    validate_timezone,
    convert_to_timezone,
)

logger = get_logger(__name__)

# Constants
SYDNEY_TIMEZONE = ZoneInfo("Australia/Sydney")
DEFAULT_TIMEZONE = SYDNEY_TIMEZONE

class WeatherCondition(str, Enum):
    """Possible weather conditions."""
    CLEAR = "clear"
    SUNNY = "sunny"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    SNOW = "snow"
    FOG = "fog"
    WINDY = "windy"
    UNKNOWN = "unknown"

class AlertSeverity(str, Enum):
    """Severity levels for weather alerts."""
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"

class AlertType(str, Enum):
    """Types of weather alerts."""
    WIND = "wind"
    RAIN = "rain"
    THUNDERSTORM = "thunderstorm"
    FLOOD = "flood"
    HEAT = "heat"
    COLD = "cold"
    FIRE = "fire"
    OTHER = "other"

class BaseWeatherModel(BaseModel):
    """Base model for all weather data with common fields and methods."""
    
    # Version tracking
    version: str = Field("1.0.0", description="Model version")
    created_at: datetime = Field(default_factory=datetime.now, description="When the data was created")
    updated_at: Optional[datetime] = Field(None, description="When the data was last updated")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator("created_at", "updated_at")
    @classmethod
    def ensure_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime fields have timezone information."""
        if v is None:
            return v
        if v.tzinfo is None:
            return v.replace(tzinfo=DEFAULT_TIMEZONE)
        return v
    
    @model_validator(mode='after')
    def validate_timestamps(self) -> 'BaseWeatherModel':
        """Validate that updated_at is after created_at if both exist."""
        if self.updated_at and self.created_at and self.updated_at < self.created_at:
            raise ValidationError("updated_at must be after created_at")
        return self

class Location(BaseWeatherModel):
    """Location information for weather data."""
    
    city: str = Field(..., description="City name", min_length=1)
    region: str = Field(..., description="Region or state", min_length=1)
    country: str = Field(..., description="Country name", min_length=1)
    latitude: float = Field(..., description="Latitude in degrees", ge=-90, le=90)
    longitude: float = Field(..., description="Longitude in degrees", ge=-180, le=180)
    timezone: str = Field(..., description="Timezone name")
    local_time: datetime = Field(..., description="Local time at location")
    
    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone string."""
        if not validate_timezone(v):
            raise ValidationError(f"Invalid timezone: {v}")
        return v
    
    @field_validator("local_time")
    @classmethod
    def validate_local_time(cls, v: datetime, values: Dict[str, Any]) -> datetime:
        """Validate that local time matches timezone."""
        if "timezone" in values and v.tzinfo and v.tzinfo.key != values["timezone"]:
            raise ValidationError(f"Local time timezone {v.tzinfo.key} does not match location timezone {values['timezone']}")
        return v

class CurrentWeather(BaseWeatherModel):
    """Current weather conditions at a location."""
    
    location: Location = Field(..., description="Location information")
    temperature_c: float = Field(..., description="Temperature in Celsius")
    temperature_f: float = Field(..., description="Temperature in Fahrenheit")
    feels_like_c: float = Field(..., description="Feels like temperature in Celsius")
    feels_like_f: float = Field(..., description="Feels like temperature in Fahrenheit")
    humidity: int = Field(..., description="Humidity percentage", ge=0, le=100)
    wind_speed_kmh: float = Field(..., description="Wind speed in km/h", ge=0)
    wind_speed_mph: float = Field(..., description="Wind speed in mph", ge=0)
    wind_direction: str = Field(..., description="Wind direction (e.g., 'N', 'SE')")
    precipitation_mm: float = Field(..., description="Precipitation in mm", ge=0)
    precipitation_inches: float = Field(..., description="Precipitation in inches", ge=0)
    uv_index: float = Field(..., description="UV index", ge=0)
    condition: WeatherCondition = Field(..., description="Current weather condition")
    observation_time: datetime = Field(..., description="When the observation was made")
    
    @model_validator(mode='after')
    def validate_temperatures(self) -> 'CurrentWeather':
        """Validate temperature conversions."""
        # Check that F temperatures match C temperatures
        expected_f = (self.temperature_c * 9/5) + 32
        if abs(self.temperature_f - expected_f) > 0.1:
            raise ValidationError(f"Temperature F ({self.temperature_f}) does not match C ({self.temperature_c})")
        
        expected_feels_f = (self.feels_like_c * 9/5) + 32
        if abs(self.feels_like_f - expected_feels_f) > 0.1:
            raise ValidationError(f"Feels like F ({self.feels_like_f}) does not match C ({self.feels_like_c})")
        
        return self
    
    @model_validator(mode='after')
    def validate_precipitation(self) -> 'CurrentWeather':
        """Validate precipitation conversions."""
        # Check that inches match mm
        expected_inches = self.precipitation_mm / 25.4
        if abs(self.precipitation_inches - expected_inches) > 0.001:
            raise ValidationError(f"Precipitation inches ({self.precipitation_inches}) does not match mm ({self.precipitation_mm})")
        return self
    
    @model_validator(mode='after')
    def validate_wind_speed(self) -> 'CurrentWeather':
        """Validate wind speed conversions."""
        # Check that mph matches km/h
        expected_mph = self.wind_speed_kmh / 1.60934
        if abs(self.wind_speed_mph - expected_mph) > 0.1:
            raise ValidationError(f"Wind speed mph ({self.wind_speed_mph}) does not match km/h ({self.wind_speed_kmh})")
        return self
    
    @field_validator("wind_direction")
    @classmethod
    def validate_wind_direction(cls, v: str) -> str:
        """Validate wind direction format."""
        valid_directions = {'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'}
        if v.upper() not in valid_directions:
            raise ValidationError(f"Invalid wind direction: {v}. Must be one of {valid_directions}")
        return v.upper()
    
    @field_validator("observation_time")
    @classmethod
    def validate_observation_time(cls, v: datetime) -> datetime:
        """Validate observation time is not in the future."""
        if v > datetime.now(v.tzinfo or DEFAULT_TIMEZONE):
            raise ValidationError("Observation time cannot be in the future")
        return v 

class ForecastHour(BaseWeatherModel):
    """Hourly forecast data."""
    
    time: datetime = Field(..., description="Forecast time")
    temperature_c: float = Field(..., description="Temperature in Celsius")
    temperature_f: float = Field(..., description="Temperature in Fahrenheit")
    feels_like_c: float = Field(..., description="Feels like temperature in Celsius")
    feels_like_f: float = Field(..., description="Feels like temperature in Fahrenheit")
    humidity: int = Field(..., description="Humidity percentage", ge=0, le=100)
    wind_speed_kmh: float = Field(..., description="Wind speed in km/h", ge=0)
    wind_speed_mph: float = Field(..., description="Wind speed in mph", ge=0)
    wind_direction: str = Field(..., description="Wind direction")
    precipitation_mm: float = Field(..., description="Precipitation in mm", ge=0)
    precipitation_inches: float = Field(..., description="Precipitation in inches", ge=0)
    precipitation_chance: int = Field(..., description="Chance of precipitation", ge=0, le=100)
    condition: WeatherCondition = Field(..., description="Weather condition")
    
    @model_validator(mode='after')
    def validate_temperatures(self) -> 'ForecastHour':
        """Validate temperature conversions."""
        expected_f = (self.temperature_c * 9/5) + 32
        if abs(self.temperature_f - expected_f) > 0.1:
            raise ValidationError(f"Temperature F ({self.temperature_f}) does not match C ({self.temperature_c})")
        
        expected_feels_f = (self.feels_like_c * 9/5) + 32
        if abs(self.feels_like_f - expected_feels_f) > 0.1:
            raise ValidationError(f"Feels like F ({self.feels_like_f}) does not match C ({self.feels_like_c})")
        return self
    
    @model_validator(mode='after')
    def validate_precipitation(self) -> 'ForecastHour':
        """Validate precipitation conversions."""
        expected_inches = self.precipitation_mm / 25.4
        if abs(self.precipitation_inches - expected_inches) > 0.001:
            raise ValidationError(f"Precipitation inches ({self.precipitation_inches}) does not match mm ({self.precipitation_mm})")
        return self
    
    @model_validator(mode='after')
    def validate_wind_speed(self) -> 'ForecastHour':
        """Validate wind speed conversions."""
        expected_mph = self.wind_speed_kmh / 1.60934
        if abs(self.wind_speed_mph - expected_mph) > 0.1:
            raise ValidationError(f"Wind speed mph ({self.wind_speed_mph}) does not match km/h ({self.wind_speed_kmh})")
        return self
    
    @field_validator("wind_direction")
    @classmethod
    def validate_wind_direction(cls, v: str) -> str:
        """Validate wind direction format."""
        valid_directions = {'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'}
        if v.upper() not in valid_directions:
            raise ValidationError(f"Invalid wind direction: {v}. Must be one of {valid_directions}")
        return v.upper()

class ForecastDay(BaseWeatherModel):
    """Daily forecast data."""
    
    date: datetime = Field(..., description="Forecast date")
    max_temp_c: float = Field(..., description="Maximum temperature in Celsius")
    max_temp_f: float = Field(..., description="Maximum temperature in Fahrenheit")
    min_temp_c: float = Field(..., description="Minimum temperature in Celsius")
    min_temp_f: float = Field(..., description="Minimum temperature in Fahrenheit")
    avg_temp_c: float = Field(..., description="Average temperature in Celsius")
    avg_temp_f: float = Field(..., description="Average temperature in Fahrenheit")
    max_wind_speed_kmh: float = Field(..., description="Maximum wind speed in km/h", ge=0)
    max_wind_speed_mph: float = Field(..., description="Maximum wind speed in mph", ge=0)
    total_precipitation_mm: float = Field(..., description="Total precipitation in mm", ge=0)
    total_precipitation_inches: float = Field(..., description="Total precipitation in inches", ge=0)
    avg_humidity: int = Field(..., description="Average humidity percentage", ge=0, le=100)
    condition: WeatherCondition = Field(..., description="Weather condition")
    uv_index: float = Field(..., description="UV index", ge=0)
    sunrise: datetime = Field(..., description="Sunrise time")
    sunset: datetime = Field(..., description="Sunset time")
    hourly_forecasts: List[ForecastHour] = Field(default_factory=list, description="Hourly forecasts")
    
    @model_validator(mode='after')
    def validate_temperatures(self) -> 'ForecastDay':
        """Validate temperature conversions and ranges."""
        # Check F temperatures match C temperatures
        expected_max_f = (self.max_temp_c * 9/5) + 32
        if abs(self.max_temp_f - expected_max_f) > 0.1:
            raise ValidationError(f"Max temperature F ({self.max_temp_f}) does not match C ({self.max_temp_c})")
        
        expected_min_f = (self.min_temp_c * 9/5) + 32
        if abs(self.min_temp_f - expected_min_f) > 0.1:
            raise ValidationError(f"Min temperature F ({self.min_temp_f}) does not match C ({self.min_temp_c})")
        
        expected_avg_f = (self.avg_temp_c * 9/5) + 32
        if abs(self.avg_temp_f - expected_avg_f) > 0.1:
            raise ValidationError(f"Avg temperature F ({self.avg_temp_f}) does not match C ({self.avg_temp_c})")
        
        # Check temperature ranges
        if self.min_temp_c > self.max_temp_c:
            raise ValidationError(f"Min temperature ({self.min_temp_c}°C) cannot be greater than max temperature ({self.max_temp_c}°C)")
        
        if not (self.min_temp_c <= self.avg_temp_c <= self.max_temp_c):
            raise ValidationError(f"Average temperature ({self.avg_temp_c}°C) must be between min ({self.min_temp_c}°C) and max ({self.max_temp_c}°C)")
        
        return self
    
    @model_validator(mode='after')
    def validate_precipitation(self) -> 'ForecastDay':
        """Validate precipitation conversions."""
        expected_inches = self.total_precipitation_mm / 25.4
        if abs(self.total_precipitation_inches - expected_inches) > 0.001:
            raise ValidationError(f"Precipitation inches ({self.total_precipitation_inches}) does not match mm ({self.total_precipitation_mm})")
        return self
    
    @model_validator(mode='after')
    def validate_wind_speed(self) -> 'ForecastDay':
        """Validate wind speed conversions."""
        expected_mph = self.max_wind_speed_kmh / 1.60934
        if abs(self.max_wind_speed_mph - expected_mph) > 0.1:
            raise ValidationError(f"Wind speed mph ({self.max_wind_speed_mph}) does not match km/h ({self.max_wind_speed_kmh})")
        return self
    
    @model_validator(mode='after')
    def validate_sun_times(self) -> 'ForecastDay':
        """Validate sunrise and sunset times."""
        if self.sunrise >= self.sunset:
            raise ValidationError(f"Sunrise time ({self.sunrise}) must be before sunset time ({self.sunset})")
        return self

class WeatherForecast(BaseWeatherModel):
    """Complete weather forecast for a location."""
    
    location: Location = Field(..., description="Location information")
    current: CurrentWeather = Field(..., description="Current weather conditions")
    daily_forecasts: List[ForecastDay] = Field(..., description="Daily forecasts", min_items=1)
    
    @model_validator(mode='after')
    def validate_forecast_sequence(self) -> 'WeatherForecast':
        """Validate forecast dates are in sequence."""
        dates = [f.date for f in self.daily_forecasts]
        if dates != sorted(dates):
            raise ValidationError("Daily forecasts must be in chronological order")
        return self

class WeatherAlert(BaseWeatherModel):
    """Weather alert information."""
    
    alert_type: AlertType = Field(..., description="Type of alert")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title", min_length=1)
    description: str = Field(..., description="Alert description", min_length=1)
    start_time: datetime = Field(..., description="When the alert starts")
    end_time: datetime = Field(..., description="When the alert ends")
    affected_areas: List[str] = Field(..., description="List of affected areas", min_items=1)
    source: str = Field(..., description="Alert source", min_length=1)
    url: Optional[str] = Field(None, description="URL for more information")
    
    @model_validator(mode='after')
    def validate_time_period(self) -> 'WeatherAlert':
        """Validate alert time period."""
        if self.start_time >= self.end_time:
            raise ValidationError(f"Alert start time ({self.start_time}) must be before end time ({self.end_time})")
        return self

class WeatherAlerts(BaseWeatherModel):
    """Collection of weather alerts for a location."""
    
    location: Location = Field(..., description="Location information")
    alerts: List[WeatherAlert] = Field(default_factory=list, description="Active weather alerts")
    
    @model_validator(mode='after')
    def validate_alerts(self) -> 'WeatherAlerts':
        """Validate alert collection."""
        # Check for overlapping alerts of the same type
        alert_types = {}
        for alert in self.alerts:
            if alert.alert_type not in alert_types:
                alert_types[alert.alert_type] = []
            for existing in alert_types[alert.alert_type]:
                if (alert.start_time <= existing.end_time and 
                    alert.end_time >= existing.start_time):
                    raise ValidationError(
                        f"Overlapping alerts of type {alert.alert_type}: "
                        f"{alert.title} ({alert.start_time} to {alert.end_time}) and "
                        f"{existing.title} ({existing.start_time} to {existing.end_time})"
                    )
            alert_types[alert.alert_type].append(alert)
        return self 