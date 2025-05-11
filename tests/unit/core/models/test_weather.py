"""
Unit tests for weather data models.

This module tests the validation, transformation, and unit conversion
of weather data models.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.core.models.weather import (
    BaseWeatherModel,
    Location,
    CurrentWeather,
    ForecastHour,
    ForecastDay,
    WeatherForecast,
    WeatherAlert,
    WeatherAlerts,
    WeatherCondition,
    AlertSeverity,
    AlertType,
    SYDNEY_TIMEZONE,
    DEFAULT_TIMEZONE,
)
from src.utils.exceptions import ValidationError

# Test data
VALID_LOCATION_DATA = {
    "city": "Sydney",
    "region": "NSW",
    "country": "Australia",
    "latitude": -33.8688,
    "longitude": 151.2093,
    "timezone": "Australia/Sydney",
    "local_time": "2024-03-20T10:00:00+10:00",
    "version": "1.0.0",
    "created_at": "2024-03-20T09:00:00+10:00",
}

VALID_CURRENT_WEATHER_DATA = {
    "location": VALID_LOCATION_DATA,
    "temperature_c": 22.5,
    "temperature_f": 72.5,
    "feels_like_c": 23.0,
    "feels_like_f": 73.4,
    "humidity": 65,
    "wind_speed_kmh": 15.0,
    "wind_speed_mph": 9.3,
    "wind_direction": "SE",
    "precipitation_mm": 0.0,
    "precipitation_inches": 0.0,
    "uv_index": 6.0,
    "condition": "sunny",
    "observation_time": "2024-03-20T10:00:00+10:00",
    "version": "1.0.0",
    "created_at": "2024-03-20T09:00:00+10:00",
}

VALID_FORECAST_HOUR_DATA = {
    "time": "2024-03-20T11:00:00+10:00",
    "temperature_c": 23.0,
    "temperature_f": 73.4,
    "feels_like_c": 23.5,
    "feels_like_f": 74.3,
    "humidity": 63,
    "wind_speed_kmh": 16.0,
    "wind_speed_mph": 9.9,
    "wind_direction": "SE",
    "precipitation_mm": 0.0,
    "precipitation_inches": 0.0,
    "precipitation_chance": 10,
    "condition": "partly_cloudy",
    "version": "1.0.0",
    "created_at": "2024-03-20T09:00:00+10:00",
}

VALID_FORECAST_DAY_DATA = {
    "date": "2024-03-20T00:00:00+10:00",
    "max_temp_c": 25.0,
    "max_temp_f": 77.0,
    "min_temp_c": 18.0,
    "min_temp_f": 64.4,
    "avg_temp_c": 21.5,
    "avg_temp_f": 70.7,
    "max_wind_speed_kmh": 20.0,
    "max_wind_speed_mph": 12.4,
    "total_precipitation_mm": 0.0,
    "total_precipitation_inches": 0.0,
    "avg_humidity": 65,
    "condition": "sunny",
    "uv_index": 7.0,
    "sunrise": "2024-03-20T06:45:00+10:00",
    "sunset": "2024-03-20T19:00:00+10:00",
    "hourly_forecasts": [VALID_FORECAST_HOUR_DATA],
    "version": "1.0.0",
    "created_at": "2024-03-20T09:00:00+10:00",
}

VALID_WEATHER_ALERT_DATA = {
    "alert_type": "rain",
    "severity": "moderate",
    "title": "Heavy Rain Warning",
    "description": "Heavy rainfall expected in the next 24 hours",
    "start_time": "2024-03-20T12:00:00+10:00",
    "end_time": "2024-03-21T12:00:00+10:00",
    "affected_areas": ["Sydney", "Central Coast"],
    "source": "Bureau of Meteorology",
    "url": "https://weather.test/alerts/123",
    "version": "1.0.0",
    "created_at": "2024-03-20T09:00:00+10:00",
}

# Test fixtures
@pytest.fixture
def valid_location():
    """Create a valid Location instance."""
    return Location(**VALID_LOCATION_DATA)

@pytest.fixture
def valid_current_weather():
    """Create a valid CurrentWeather instance."""
    return CurrentWeather(**VALID_CURRENT_WEATHER_DATA)

@pytest.fixture
def valid_forecast_hour():
    """Create a valid ForecastHour instance."""
    return ForecastHour(**VALID_FORECAST_HOUR_DATA)

@pytest.fixture
def valid_forecast_day():
    """Create a valid ForecastDay instance."""
    return ForecastDay(**VALID_FORECAST_DAY_DATA)

@pytest.fixture
def valid_weather_alert():
    """Create a valid WeatherAlert instance."""
    return WeatherAlert(**VALID_WEATHER_ALERT_DATA)

# Additional test fixtures
@pytest.fixture
def weather_models_with_metadata():
    """Create models with metadata for testing."""
    metadata = {
        "source": "test_api",
        "confidence": 0.95,
        "last_updated": "2024-03-20T09:00:00+10:00"
    }
    
    location = Location(**{**VALID_LOCATION_DATA, "metadata": metadata})
    current = CurrentWeather(**{**VALID_CURRENT_WEATHER_DATA, "metadata": metadata})
    forecast = ForecastDay(**{**VALID_FORECAST_DAY_DATA, "metadata": metadata})
    alert = WeatherAlert(**{**VALID_WEATHER_ALERT_DATA, "metadata": metadata})
    
    return location, current, forecast, alert

# Base model tests
def test_base_model_creation():
    """Test creating a base weather model."""
    model = BaseWeatherModel()
    assert model.version == "1.0.0"
    assert isinstance(model.created_at, datetime)
    assert model.updated_at is None
    assert isinstance(model.metadata, dict)
    assert model.metadata == {}

def test_base_model_timestamps():
    """Test timestamp validation in base model."""
    now = datetime.now(DEFAULT_TIMEZONE)
    future = now + timedelta(hours=1)
    
    # Test valid timestamps
    model = BaseWeatherModel(
        created_at=now,
        updated_at=future
    )
    assert model.created_at == now
    assert model.updated_at == future
    
    # Test invalid timestamps
    with pytest.raises(ValidationError) as exc_info:
        BaseWeatherModel(
            created_at=future,
            updated_at=now
        )
    assert "updated_at must be after created_at" in str(exc_info.value)

# Location model tests
def test_location_creation(valid_location):
    """Test creating a valid location."""
    assert valid_location.city == "Sydney"
    assert valid_location.region == "NSW"
    assert valid_location.country == "Australia"
    assert valid_location.latitude == -33.8688
    assert valid_location.longitude == 151.2093
    assert valid_location.timezone == "Australia/Sydney"
    assert valid_location.local_time == datetime.fromisoformat("2024-03-20T10:00:00+10:00")

def test_location_invalid_coordinates():
    """Test location with invalid coordinates."""
    invalid_data = VALID_LOCATION_DATA.copy()
    
    # Test invalid latitude
    invalid_data["latitude"] = 91.0
    with pytest.raises(ValidationError) as exc_info:
        Location(**invalid_data)
    assert "Latitude must be between -90 and 90" in str(exc_info.value)
    
    # Test invalid longitude
    invalid_data["latitude"] = -33.8688
    invalid_data["longitude"] = 181.0
    with pytest.raises(ValidationError) as exc_info:
        Location(**invalid_data)
    assert "Longitude must be between -180 and 180" in str(exc_info.value)

def test_location_invalid_timezone():
    """Test location with invalid timezone."""
    invalid_data = VALID_LOCATION_DATA.copy()
    invalid_data["timezone"] = "Invalid/Timezone"
    
    with pytest.raises(ValidationError) as exc_info:
        Location(**invalid_data)
    assert "Invalid timezone" in str(exc_info.value)

def test_location_timezone_mismatch():
    """Test location with mismatched timezone and local time."""
    invalid_data = VALID_LOCATION_DATA.copy()
    invalid_data["local_time"] = "2024-03-20T10:00:00+00:00"  # UTC time
    
    with pytest.raises(ValidationError) as exc_info:
        Location(**invalid_data)
    assert "timezone does not match location timezone" in str(exc_info.value)

# Current weather tests
def test_current_weather_creation(valid_current_weather):
    """Test creating valid current weather."""
    assert valid_current_weather.temperature_c == 22.5
    assert valid_current_weather.temperature_f == 72.5
    assert valid_current_weather.feels_like_c == 23.0
    assert valid_current_weather.feels_like_f == 73.4
    assert valid_current_weather.humidity == 65
    assert valid_current_weather.wind_speed_kmh == 15.0
    assert valid_current_weather.wind_speed_mph == 9.3
    assert valid_current_weather.wind_direction == "SE"
    assert valid_current_weather.precipitation_mm == 0.0
    assert valid_current_weather.precipitation_inches == 0.0
    assert valid_current_weather.uv_index == 6.0
    assert valid_current_weather.condition == WeatherCondition.SUNNY

def test_current_weather_temperature_conversion():
    """Test temperature conversion validation."""
    invalid_data = VALID_CURRENT_WEATHER_DATA.copy()
    invalid_data["temperature_f"] = 80.0  # Incorrect conversion
    
    with pytest.raises(ValidationError) as exc_info:
        CurrentWeather(**invalid_data)
    assert "Temperature F does not match C" in str(exc_info.value)

def test_current_weather_precipitation_conversion():
    """Test precipitation conversion validation."""
    invalid_data = VALID_CURRENT_WEATHER_DATA.copy()
    invalid_data["precipitation_inches"] = 0.1  # Incorrect conversion
    
    with pytest.raises(ValidationError) as exc_info:
        CurrentWeather(**invalid_data)
    assert "Precipitation inches does not match mm" in str(exc_info.value)

def test_current_weather_wind_speed_conversion():
    """Test wind speed conversion validation."""
    invalid_data = VALID_CURRENT_WEATHER_DATA.copy()
    invalid_data["wind_speed_mph"] = 10.0  # Incorrect conversion
    
    with pytest.raises(ValidationError) as exc_info:
        CurrentWeather(**invalid_data)
    assert "Wind speed mph does not match km/h" in str(exc_info.value)

def test_current_weather_invalid_wind_direction():
    """Test invalid wind direction."""
    invalid_data = VALID_CURRENT_WEATHER_DATA.copy()
    invalid_data["wind_direction"] = "INVALID"
    
    with pytest.raises(ValidationError) as exc_info:
        CurrentWeather(**invalid_data)
    assert "Invalid wind direction" in str(exc_info.value)

def test_current_weather_future_observation():
    """Test future observation time."""
    invalid_data = VALID_CURRENT_WEATHER_DATA.copy()
    future_time = datetime.now(DEFAULT_TIMEZONE) + timedelta(hours=1)
    invalid_data["observation_time"] = future_time.isoformat()
    
    with pytest.raises(ValidationError) as exc_info:
        CurrentWeather(**invalid_data)
    assert "Observation time cannot be in the future" in str(exc_info.value)

# Forecast hour tests
def test_forecast_hour_creation(valid_forecast_hour):
    """Test creating valid forecast hour."""
    assert valid_forecast_hour.time == datetime.fromisoformat("2024-03-20T11:00:00+10:00")
    assert valid_forecast_hour.temperature_c == 23.0
    assert valid_forecast_hour.temperature_f == 73.4
    assert valid_forecast_hour.feels_like_c == 23.5
    assert valid_forecast_hour.feels_like_f == 74.3
    assert valid_forecast_hour.humidity == 63
    assert valid_forecast_hour.wind_speed_kmh == 16.0
    assert valid_forecast_hour.wind_speed_mph == 9.9
    assert valid_forecast_hour.wind_direction == "SE"
    assert valid_forecast_hour.precipitation_mm == 0.0
    assert valid_forecast_hour.precipitation_inches == 0.0
    assert valid_forecast_hour.precipitation_chance == 10
    assert valid_forecast_hour.condition == WeatherCondition.PARTLY_CLOUDY

# Forecast day tests
def test_forecast_day_creation(valid_forecast_day):
    """Test creating valid forecast day."""
    assert valid_forecast_day.date == datetime.fromisoformat("2024-03-20T00:00:00+10:00")
    assert valid_forecast_day.max_temp_c == 25.0
    assert valid_forecast_day.max_temp_f == 77.0
    assert valid_forecast_day.min_temp_c == 18.0
    assert valid_forecast_day.min_temp_f == 64.4
    assert valid_forecast_day.avg_temp_c == 21.5
    assert valid_forecast_day.avg_temp_f == 70.7
    assert valid_forecast_day.max_wind_speed_kmh == 20.0
    assert valid_forecast_day.max_wind_speed_mph == 12.4
    assert valid_forecast_day.total_precipitation_mm == 0.0
    assert valid_forecast_day.total_precipitation_inches == 0.0
    assert valid_forecast_day.avg_humidity == 65
    assert valid_forecast_day.condition == WeatherCondition.SUNNY
    assert valid_forecast_day.uv_index == 7.0
    assert valid_forecast_day.sunrise == datetime.fromisoformat("2024-03-20T06:45:00+10:00")
    assert valid_forecast_day.sunset == datetime.fromisoformat("2024-03-20T19:00:00+10:00")
    assert len(valid_forecast_day.hourly_forecasts) == 1

def test_forecast_day_temperature_ranges():
    """Test temperature range validation."""
    invalid_data = VALID_FORECAST_DAY_DATA.copy()
    
    # Test min > max
    invalid_data["min_temp_c"] = 26.0
    invalid_data["max_temp_c"] = 25.0
    with pytest.raises(ValidationError) as exc_info:
        ForecastDay(**invalid_data)
    assert "Min temperature cannot be greater than max temperature" in str(exc_info.value)
    
    # Test avg outside range
    invalid_data["min_temp_c"] = 18.0
    invalid_data["max_temp_c"] = 25.0
    invalid_data["avg_temp_c"] = 17.0
    with pytest.raises(ValidationError) as exc_info:
        ForecastDay(**invalid_data)
    assert "Average temperature must be between min and max" in str(exc_info.value)

def test_forecast_day_sun_times():
    """Test sunrise/sunset validation."""
    invalid_data = VALID_FORECAST_DAY_DATA.copy()
    invalid_data["sunrise"] = "2024-03-20T19:00:00+10:00"  # After sunset
    
    with pytest.raises(ValidationError) as exc_info:
        ForecastDay(**invalid_data)
    assert "Sunrise time must be before sunset time" in str(exc_info.value)

# Weather forecast tests
def test_weather_forecast_creation(valid_location, valid_current_weather, valid_forecast_day):
    """Test creating valid weather forecast."""
    forecast = WeatherForecast(
        location=valid_location,
        current=valid_current_weather,
        daily_forecasts=[valid_forecast_day]
    )
    assert forecast.location == valid_location
    assert forecast.current == valid_current_weather
    assert forecast.daily_forecasts == [valid_forecast_day]

def test_weather_forecast_sequence():
    """Test forecast date sequence validation."""
    location = Location(**VALID_LOCATION_DATA)
    current = CurrentWeather(**VALID_CURRENT_WEATHER_DATA)
    
    # Create forecasts in wrong order
    day1 = ForecastDay(**VALID_FORECAST_DAY_DATA)
    day2_data = VALID_FORECAST_DAY_DATA.copy()
    day2_data["date"] = "2024-03-19T00:00:00+10:00"  # Before day1
    day2 = ForecastDay(**day2_data)
    
    with pytest.raises(ValidationError) as exc_info:
        WeatherForecast(
            location=location,
            current=current,
            daily_forecasts=[day1, day2]
        )
    assert "Daily forecasts must be in chronological order" in str(exc_info.value)

# Weather alert tests
def test_weather_alert_creation(valid_weather_alert):
    """Test creating valid weather alert."""
    assert valid_weather_alert.alert_type == AlertType.RAIN
    assert valid_weather_alert.severity == AlertSeverity.MODERATE
    assert valid_weather_alert.title == "Heavy Rain Warning"
    assert valid_weather_alert.description == "Heavy rainfall expected in the next 24 hours"
    assert valid_weather_alert.start_time == datetime.fromisoformat("2024-03-20T12:00:00+10:00")
    assert valid_weather_alert.end_time == datetime.fromisoformat("2024-03-21T12:00:00+10:00")
    assert valid_weather_alert.affected_areas == ["Sydney", "Central Coast"]
    assert valid_weather_alert.source == "Bureau of Meteorology"
    assert valid_weather_alert.url == "https://weather.test/alerts/123"

def test_weather_alert_time_period():
    """Test alert time period validation."""
    invalid_data = VALID_WEATHER_ALERT_DATA.copy()
    invalid_data["end_time"] = "2024-03-20T11:00:00+10:00"  # Before start time
    
    with pytest.raises(ValidationError) as exc_info:
        WeatherAlert(**invalid_data)
    assert "Alert start time must be before end time" in str(exc_info.value)

# Weather alerts collection tests
def test_weather_alerts_creation(valid_location, valid_weather_alert):
    """Test creating valid weather alerts collection."""
    alerts = WeatherAlerts(
        location=valid_location,
        alerts=[valid_weather_alert]
    )
    assert alerts.location == valid_location
    assert alerts.alerts == [valid_weather_alert]

def test_weather_alerts_overlap():
    """Test overlapping alerts validation."""
    location = Location(**VALID_LOCATION_DATA)
    
    # Create overlapping alerts
    alert1 = WeatherAlert(**VALID_WEATHER_ALERT_DATA)
    alert2_data = VALID_WEATHER_ALERT_DATA.copy()
    alert2_data["title"] = "Overlapping Alert"
    alert2_data["start_time"] = "2024-03-20T18:00:00+10:00"  # Overlaps with alert1
    
    with pytest.raises(ValidationError) as exc_info:
        WeatherAlerts(
            location=location,
            alerts=[alert1, WeatherAlert(**alert2_data)]
        )
    assert "Overlapping alerts of type rain" in str(exc_info.value)

# Edge case tests
def test_location_edge_coordinates():
    """Test location with edge case coordinates."""
    # Test boundary coordinates
    valid_edges = [
        {"latitude": 90.0, "longitude": 0.0},    # North pole
        {"latitude": -90.0, "longitude": 0.0},   # South pole
        {"latitude": 0.0, "longitude": 180.0},   # International date line
        {"latitude": 0.0, "longitude": -180.0},  # International date line
    ]
    
    for coords in valid_edges:
        data = {**VALID_LOCATION_DATA, **coords}
        location = Location(**data)
        assert location.latitude == coords["latitude"]
        assert location.longitude == coords["longitude"]
    
    # Test just outside boundaries
    invalid_edges = [
        {"latitude": 90.1, "longitude": 0.0},    # Just north of pole
        {"latitude": -90.1, "longitude": 0.0},   # Just south of pole
        {"latitude": 0.0, "longitude": 180.1},   # Just past date line
        {"latitude": 0.0, "longitude": -180.1},  # Just past date line
    ]
    
    for coords in invalid_edges:
        data = {**VALID_LOCATION_DATA, **coords}
        with pytest.raises(ValidationError):
            Location(**data)

def test_current_weather_edge_values():
    """Test current weather with edge case values."""
    # Test boundary values
    valid_edges = {
        "humidity": [0, 100],                    # Min/max humidity
        "uv_index": [0.0, 15.0],                # Min/max UV index
        "precipitation_mm": [0.0, 1000.0],      # Min/max precipitation
        "wind_speed_kmh": [0.0, 300.0],         # Min/max wind speed
    }
    
    for field, values in valid_edges.items():
        for value in values:
            data = VALID_CURRENT_WEATHER_DATA.copy()
            data[field] = value
            weather = CurrentWeather(**data)
            assert getattr(weather, field) == value
    
    # Test just outside boundaries
    invalid_edges = {
        "humidity": [-1, 101],                   # Outside humidity range
        "uv_index": [-0.1, 15.1],               # Outside UV range
        "precipitation_mm": [-0.1, 1000.1],     # Negative precipitation
        "wind_speed_kmh": [-0.1, 300.1],        # Negative wind speed
    }
    
    for field, values in invalid_edges.items():
        for value in values:
            data = VALID_CURRENT_WEATHER_DATA.copy()
            data[field] = value
            with pytest.raises(ValidationError):
                CurrentWeather(**data)

def test_forecast_day_edge_times():
    """Test forecast day with edge case times."""
    # Test same sunrise/sunset (should be invalid)
    invalid_data = VALID_FORECAST_DAY_DATA.copy()
    invalid_data["sunrise"] = invalid_data["sunset"]
    
    with pytest.raises(ValidationError) as exc_info:
        ForecastDay(**invalid_data)
    assert "Sunrise time must be before sunset time" in str(exc_info.value)
    
    # Test sunrise/sunset on different days
    valid_data = VALID_FORECAST_DAY_DATA.copy()
    valid_data["sunrise"] = "2024-03-20T06:45:00+10:00"
    valid_data["sunset"] = "2024-03-21T06:45:00+10:00"  # Next day
    
    forecast = ForecastDay(**valid_data)
    assert forecast.sunrise < forecast.sunset

# Serialization tests
def test_model_serialization(valid_location, valid_current_weather, valid_forecast_day, valid_weather_alert):
    """Test model serialization and deserialization."""
    # Test Location
    location_dict = valid_location.model_dump()
    location_json = valid_location.model_dump_json()
    assert isinstance(location_dict, dict)
    assert isinstance(location_json, str)
    assert Location(**location_dict) == valid_location
    assert Location.model_validate_json(location_json) == valid_location
    
    # Test CurrentWeather
    weather_dict = valid_current_weather.model_dump()
    weather_json = valid_current_weather.model_dump_json()
    assert isinstance(weather_dict, dict)
    assert isinstance(weather_json, str)
    assert CurrentWeather(**weather_dict) == valid_current_weather
    assert CurrentWeather.model_validate_json(weather_json) == valid_current_weather
    
    # Test ForecastDay
    forecast_dict = valid_forecast_day.model_dump()
    forecast_json = valid_forecast_day.model_dump_json()
    assert isinstance(forecast_dict, dict)
    assert isinstance(forecast_json, str)
    assert ForecastDay(**forecast_dict) == valid_forecast_day
    assert ForecastDay.model_validate_json(forecast_json) == valid_forecast_day
    
    # Test WeatherAlert
    alert_dict = valid_weather_alert.model_dump()
    alert_json = valid_weather_alert.model_dump_json()
    assert isinstance(alert_dict, dict)
    assert isinstance(alert_json, str)
    assert WeatherAlert(**alert_dict) == valid_weather_alert
    assert WeatherAlert.model_validate_json(alert_json) == valid_weather_alert

# Model comparison tests
def test_model_equality(valid_location, valid_current_weather, valid_forecast_day, valid_weather_alert):
    """Test model equality and comparison."""
    # Test Location equality
    location_copy = Location(**VALID_LOCATION_DATA)
    assert valid_location == location_copy
    assert valid_location != Location(**{**VALID_LOCATION_DATA, "city": "Melbourne"})
    
    # Test CurrentWeather equality
    weather_copy = CurrentWeather(**VALID_CURRENT_WEATHER_DATA)
    assert valid_current_weather == weather_copy
    assert valid_current_weather != CurrentWeather(**{**VALID_CURRENT_WEATHER_DATA, "temperature_c": 30.0})
    
    # Test ForecastDay equality
    forecast_copy = ForecastDay(**VALID_FORECAST_DAY_DATA)
    assert valid_forecast_day == forecast_copy
    assert valid_forecast_day != ForecastDay(**{**VALID_FORECAST_DAY_DATA, "max_temp_c": 30.0})
    
    # Test WeatherAlert equality
    alert_copy = WeatherAlert(**VALID_WEATHER_ALERT_DATA)
    assert valid_weather_alert == alert_copy
    assert valid_weather_alert != WeatherAlert(**{**VALID_WEATHER_ALERT_DATA, "title": "Different Alert"})

# Versioning tests
def test_model_versioning():
    """Test model version handling."""
    # Test version field
    model = BaseWeatherModel(version="2.0.0")
    assert model.version == "2.0.0"
    
    # Test version in metadata
    model = BaseWeatherModel(metadata={"api_version": "2.0.0"})
    assert model.metadata["api_version"] == "2.0.0"
    
    # Test version update
    model = BaseWeatherModel()
    model.updated_at = datetime.now(DEFAULT_TIMEZONE)
    assert model.version == "1.0.0"  # Version should not change on update

# Metadata tests
def test_model_metadata(weather_models_with_metadata):
    """Test model metadata handling."""
    location, current, forecast, alert = weather_models_with_metadata
    
    # Test metadata presence
    assert "source" in location.metadata
    assert "confidence" in current.metadata
    assert "last_updated" in forecast.metadata
    assert "source" in alert.metadata
    
    # Test metadata values
    assert location.metadata["source"] == "test_api"
    assert current.metadata["confidence"] == 0.95
    assert forecast.metadata["last_updated"] == "2024-03-20T09:00:00+10:00"
    assert alert.metadata["source"] == "test_api"
    
    # Test metadata update
    new_metadata = {"new_field": "new_value"}
    location.metadata.update(new_metadata)
    assert "new_field" in location.metadata
    assert location.metadata["new_field"] == "new_value"

# Model collection tests
def test_weather_alerts_collection_operations(valid_location, valid_weather_alert):
    """Test weather alerts collection operations."""
    # Create collection with multiple alerts
    alert2_data = VALID_WEATHER_ALERT_DATA.copy()
    alert2_data["title"] = "Second Alert"
    alert2_data["start_time"] = "2024-03-21T12:00:00+10:00"  # After first alert
    alert2 = WeatherAlert(**alert2_data)
    
    alerts = WeatherAlerts(
        location=valid_location,
        alerts=[valid_weather_alert, alert2]
    )
    
    # Test alert filtering
    rain_alerts = [a for a in alerts.alerts if a.alert_type == AlertType.RAIN]
    assert len(rain_alerts) == 2
    
    # Test alert sorting
    sorted_alerts = sorted(alerts.alerts, key=lambda a: a.start_time)
    assert sorted_alerts[0] == valid_weather_alert
    assert sorted_alerts[1] == alert2
    
    # Test alert grouping
    alerts_by_type = {}
    for alert in alerts.alerts:
        if alert.alert_type not in alerts_by_type:
            alerts_by_type[alert.alert_type] = []
        alerts_by_type[alert.alert_type].append(alert)
    
    assert AlertType.RAIN in alerts_by_type
    assert len(alerts_by_type[AlertType.RAIN]) == 2 