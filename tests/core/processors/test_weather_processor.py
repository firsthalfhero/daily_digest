"""
Tests for the weather processor module.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pytest

from src.core.models.weather import (
    Location,
    CurrentWeather,
    ForecastHour,
    ForecastDay,
    WeatherForecast,
    WeatherAlert,
    WeatherAlerts,
    WeatherCondition,
    AlertType,
    AlertSeverity,
    SYDNEY_TIMEZONE,
)
from src.core.processors.weather import WeatherProcessor
from src.utils.exceptions import ValidationError


@pytest.fixture
def sydney_location():
    """Create a Sydney location fixture."""
    return Location(
        city="Sydney",
        region="NSW",
        country="Australia",
        latitude=-33.8688,
        longitude=151.2093,
        timezone="Australia/Sydney",
        local_time=datetime.now(ZoneInfo("Australia/Sydney"))
    )


@pytest.fixture
def current_weather(sydney_location):
    """Create a current weather fixture."""
    return CurrentWeather(
        location=sydney_location,
        temperature_c=22.5,
        temperature_f=72.5,
        feels_like_c=23.0,
        feels_like_f=73.4,
        humidity=65,
        wind_speed_kmh=15.0,
        wind_speed_mph=9.3,
        wind_direction="SE",
        precipitation_mm=0.0,
        precipitation_inches=0.0,
        uv_index=6.0,
        condition=WeatherCondition.SUNNY,
        observation_time=datetime.now(ZoneInfo("Australia/Sydney"))
    )


@pytest.fixture
def hourly_forecast():
    """Create hourly forecast fixtures."""
    base_time = datetime.now(ZoneInfo("Australia/Sydney"))
    return [
        ForecastHour(
            time=base_time + timedelta(hours=i),
            temperature_c=20 + i,
            temperature_f=68 + i * 1.8,
            feels_like_c=21 + i,
            feels_like_f=69.8 + i * 1.8,
            humidity=60 + i,
            wind_speed_kmh=10 + i,
            wind_speed_mph=6.2 + i * 0.621371,
            wind_direction="SE",
            precipitation_mm=0.0,
            precipitation_inches=0.0,
            precipitation_chance=10 + i,
            condition=WeatherCondition.SUNNY
        )
        for i in range(24)
    ]


@pytest.fixture
def daily_forecast(sydney_location, hourly_forecast):
    """Create a daily forecast fixture."""
    base_time = datetime.now(ZoneInfo("Australia/Sydney"))
    return ForecastDay(
        date=base_time,
        max_temp_c=25.0,
        max_temp_f=77.0,
        min_temp_c=18.0,
        min_temp_f=64.4,
        avg_temp_c=21.5,
        avg_temp_f=70.7,
        max_wind_speed_kmh=20.0,
        max_wind_speed_mph=12.4,
        total_precipitation_mm=5.0,
        total_precipitation_inches=0.2,
        avg_humidity=70,
        condition=WeatherCondition.PARTLY_CLOUDY,
        uv_index=7.0,
        sunrise=base_time.replace(hour=6, minute=30),
        sunset=base_time.replace(hour=17, minute=45),
        hourly_forecasts=hourly_forecast
    )


@pytest.fixture
def weather_alert(sydney_location):
    """Create a weather alert fixture."""
    base_time = datetime.now(ZoneInfo("Australia/Sydney"))
    return WeatherAlert(
        alert_type=AlertType.RAIN,
        severity=AlertSeverity.MODERATE,
        title="Heavy Rain Warning",
        description="Heavy rain expected in Sydney area",
        start_time=base_time,
        end_time=base_time + timedelta(hours=24),
        affected_areas=["Sydney", "Central Coast"],
        source="Bureau of Meteorology",
        url="https://weather.example.com/alerts/123"
    )


@pytest.fixture
def weather_alerts(sydney_location, weather_alert):
    """Create weather alerts fixture."""
    return WeatherAlerts(
        location=sydney_location,
        alerts=[weather_alert]
    )


@pytest.fixture
def weather_forecast(sydney_location, current_weather, daily_forecast, weather_alerts):
    """Create a complete weather forecast fixture."""
    return WeatherForecast(
        location=sydney_location,
        current=current_weather,
        daily_forecasts=[daily_forecast],
        alerts=weather_alerts
    )


@pytest.fixture
def weather_processor(weather_forecast):
    """Create a weather processor fixture."""
    return WeatherProcessor(weather_forecast)


def test_processor_initialization(weather_processor, weather_forecast):
    """Test processor initialization."""
    assert weather_processor.forecast == weather_forecast


def test_processor_initialization_invalid_forecast():
    """Test processor initialization with invalid forecast."""
    with pytest.raises(ValidationError):
        WeatherProcessor(None)


def test_processor_initialization_non_sydney_location(sydney_location, current_weather, daily_forecast):
    """Test processor initialization with non-Sydney location."""
    sydney_location.city = "Melbourne"
    forecast = WeatherForecast(
        location=sydney_location,
        current=current_weather,
        daily_forecasts=[daily_forecast]
    )
    with pytest.raises(ValidationError):
        WeatherProcessor(forecast)


def test_get_daily_digest_weather(weather_processor, current_weather, daily_forecast):
    """Test getting daily digest weather."""
    date = datetime.now(ZoneInfo("Australia/Sydney"))
    result = weather_processor.get_daily_digest_weather(date)
    
    assert result["date"] == date.strftime("%A, %B %d, %Y")
    assert result["current"] is not None
    assert result["forecast"] is not None
    assert result["alerts"] is not None
    assert result["summary"] is not None
    assert result["trends"] is not None
    assert result["impact"] is not None


def test_get_daily_digest_weather_future_date(weather_processor):
    """Test getting daily digest weather for future date."""
    date = datetime.now(ZoneInfo("Australia/Sydney")) + timedelta(days=2)
    with pytest.raises(ValidationError):
        weather_processor.get_daily_digest_weather(date)


def test_generate_weather_summary(weather_processor, daily_forecast, current_weather):
    """Test weather summary generation."""
    summary = weather_processor._generate_weather_summary(daily_forecast, current_weather)
    
    assert "Currently" in summary
    assert "Today will be" in summary
    assert str(current_weather.temperature_c) in summary
    assert str(daily_forecast.max_temp_c) in summary
    assert str(daily_forecast.min_temp_c) in summary


def test_analyze_weather_trends(weather_processor, daily_forecast):
    """Test weather trend analysis."""
    trends = weather_processor._analyze_weather_trends(daily_forecast)
    
    assert "temperature_trend" in trends
    assert "precipitation_trend" in trends
    assert "condition_changes" in trends
    assert "max_temperature" in trends
    assert "min_temperature" in trends
    assert "max_precipitation_chance" in trends


def test_assess_weather_impact(weather_processor, daily_forecast, weather_alert):
    """Test weather impact assessment."""
    impact = weather_processor._assess_weather_impact(daily_forecast, [weather_alert])
    
    assert "severity" in impact
    assert "concerns" in impact
    assert "recommendations" in impact
    assert len(impact["concerns"]) > 0
    assert len(impact["recommendations"]) > 0


def test_format_current_weather(weather_processor, current_weather):
    """Test current weather formatting."""
    formatted = weather_processor._format_current_weather(current_weather)
    
    assert formatted["temperature"] == f"{current_weather.temperature_c}°C"
    assert formatted["feels_like"] == f"{current_weather.feels_like_c}°C"
    assert formatted["condition"] == current_weather.condition.value.title()
    assert formatted["humidity"] == f"{current_weather.humidity}%"
    assert formatted["wind"] == f"{current_weather.wind_speed_kmh}km/h {current_weather.wind_direction}"


def test_format_daily_forecast(weather_processor, daily_forecast):
    """Test daily forecast formatting."""
    formatted = weather_processor._format_daily_forecast(daily_forecast)
    
    assert formatted["date"] == daily_forecast.date.strftime("%A, %B %d")
    assert formatted["condition"] == daily_forecast.condition.value.title()
    assert formatted["temperature"]["max"] == f"{daily_forecast.max_temp_c}°C"
    assert formatted["temperature"]["min"] == f"{daily_forecast.min_temp_c}°C"
    assert formatted["temperature"]["average"] == f"{daily_forecast.avg_temp_c}°C"
    assert len(formatted["hourly"]) == len(daily_forecast.hourly_forecasts)


def test_format_alerts(weather_processor, weather_alert):
    """Test weather alerts formatting."""
    formatted = weather_processor._format_alerts([weather_alert])
    
    assert len(formatted) == 1
    alert = formatted[0]
    assert alert["type"] == weather_alert.alert_type.value.title()
    assert alert["severity"] == weather_alert.severity.value.title()
    assert alert["title"] == weather_alert.title
    assert alert["description"] == weather_alert.description


def test_validate_weather_data(weather_processor):
    """Test weather data validation."""
    is_valid, messages = weather_processor.validate_weather_data()
    assert is_valid
    assert len(messages) == 0


def test_validate_weather_data_invalid_temperature(weather_processor, current_weather):
    """Test weather data validation with invalid temperature."""
    weather_processor.forecast.current.temperature_c = 100  # Invalid temperature
    is_valid, messages = weather_processor.validate_weather_data()
    assert not is_valid
    assert any("temperature outside valid range" in msg for msg in messages)


def test_validate_weather_data_invalid_humidity(weather_processor, current_weather):
    """Test weather data validation with invalid humidity."""
    weather_processor.forecast.current.humidity = 150  # Invalid humidity
    is_valid, messages = weather_processor.validate_weather_data()
    assert not is_valid
    assert any("humidity outside valid range" in msg for msg in messages)


def test_validate_weather_data_invalid_temperature_range(weather_processor, daily_forecast):
    """Test weather data validation with invalid temperature range."""
    weather_processor.forecast.daily_forecasts[0].max_temp_c = 15  # Less than min_temp
    is_valid, messages = weather_processor.validate_weather_data()
    assert not is_valid
    assert any("Invalid temperature range" in msg for msg in messages)


def test_validate_weather_data_invalid_alert_time(weather_processor, weather_alert):
    """Test weather data validation with invalid alert time range."""
    weather_processor.forecast.alerts.alerts[0].end_time = weather_alert.start_time  # Invalid time range
    is_valid, messages = weather_processor.validate_weather_data()
    assert not is_valid
    assert any("Invalid alert time range" in msg for msg in messages) 