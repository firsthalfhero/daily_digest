# Weather Data Models Documentation

## Overview

The weather data models provide a comprehensive structure for handling weather data in the email digest system. All models inherit from `BaseWeatherModel` and include versioning, metadata, and timestamp tracking.

## Model Hierarchy

```
BaseWeatherModel
├── Location
├── CurrentWeather
├── ForecastHour
├── ForecastDay
├── WeatherForecast
├── WeatherAlert
└── WeatherAlerts
```

## Base Model

### BaseWeatherModel

The foundation for all weather data models, providing common functionality:

```python
class BaseWeatherModel:
    version: str = "1.0.0"
    created_at: datetime
    updated_at: Optional[datetime]
    metadata: Dict[str, Any] = {}
```

**Features:**
- Version tracking
- Creation and update timestamps
- Metadata dictionary for extensibility
- Automatic timestamp validation

## Core Models

### Location

Represents a geographical location with weather data:

```python
class Location(BaseWeatherModel):
    city: str
    region: str
    country: str
    latitude: float  # -90 to 90
    longitude: float  # -180 to 180
    timezone: str
    local_time: datetime
```

**Validation Rules:**
- Latitude must be between -90 and 90
- Longitude must be between -180 and 180
- Timezone must be valid IANA timezone
- Local time must match timezone

### CurrentWeather

Represents current weather conditions at a location:

```python
class CurrentWeather(BaseWeatherModel):
    location: Location
    temperature_c: float
    temperature_f: float
    feels_like_c: float
    feels_like_f: float
    humidity: int  # 0-100
    wind_speed_kmh: float
    wind_speed_mph: float
    wind_direction: str
    precipitation_mm: float
    precipitation_inches: float
    uv_index: float
    condition: WeatherCondition
    observation_time: datetime
```

**Validation Rules:**
- Temperature F must match C conversion
- Precipitation inches must match mm conversion
- Wind speed mph must match km/h conversion
- Humidity must be 0-100
- Observation time cannot be in future
- Wind direction must be valid cardinal direction

### Forecast Models

#### ForecastHour

Hourly forecast data:

```python
class ForecastHour(BaseWeatherModel):
    time: datetime
    temperature_c: float
    temperature_f: float
    feels_like_c: float
    feels_like_f: float
    humidity: int
    wind_speed_kmh: float
    wind_speed_mph: float
    wind_direction: str
    precipitation_mm: float
    precipitation_inches: float
    precipitation_chance: int
    condition: WeatherCondition
```

#### ForecastDay

Daily forecast with hourly breakdown:

```python
class ForecastDay(BaseWeatherModel):
    date: datetime
    max_temp_c: float
    max_temp_f: float
    min_temp_c: float
    min_temp_f: float
    avg_temp_c: float
    avg_temp_f: float
    max_wind_speed_kmh: float
    max_wind_speed_mph: float
    total_precipitation_mm: float
    total_precipitation_inches: float
    avg_humidity: int
    condition: WeatherCondition
    uv_index: float
    sunrise: datetime
    sunset: datetime
    hourly_forecasts: List[ForecastHour]
```

**Validation Rules:**
- Min temperature must be less than max
- Average temperature must be between min and max
- Sunrise must be before sunset
- Hourly forecasts must be in chronological order

### WeatherForecast

Complete forecast for a location:

```python
class WeatherForecast(BaseWeatherModel):
    location: Location
    current: CurrentWeather
    daily_forecasts: List[ForecastDay]
```

**Validation Rules:**
- Daily forecasts must be in chronological order
- Current weather must match location

### Alert Models

#### WeatherAlert

Individual weather alert:

```python
class WeatherAlert(BaseWeatherModel):
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    affected_areas: List[str]
    source: str
    url: Optional[str]
```

#### WeatherAlerts

Collection of alerts for a location:

```python
class WeatherAlerts(BaseWeatherModel):
    location: Location
    alerts: List[WeatherAlert]
```

**Validation Rules:**
- Alert start time must be before end time
- No overlapping alerts of same type
- Alerts must be for location's area

## Enums

### WeatherCondition

```python
class WeatherCondition(str, Enum):
    SUNNY = "sunny"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    RAIN = "rain"
    THUNDERSTORM = "thunderstorm"
    SNOW = "snow"
    FOG = "fog"
    WINDY = "windy"
```

### AlertType

```python
class AlertType(str, Enum):
    RAIN = "rain"
    WIND = "wind"
    THUNDERSTORM = "thunderstorm"
    FLOOD = "flood"
    FIRE = "fire"
```

### AlertSeverity

```python
class AlertSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"
```

## Usage Examples

### Creating a Location

```python
location = Location(
    city="Sydney",
    region="NSW",
    country="Australia",
    latitude=-33.8688,
    longitude=151.2093,
    timezone="Australia/Sydney",
    local_time=datetime.now(ZoneInfo("Australia/Sydney"))
)
```

### Getting Current Weather

```python
current = CurrentWeather(
    location=location,
    temperature_c=22.5,
    temperature_f=72.5,  # Automatically validated
    humidity=65,
    wind_speed_kmh=15.0,
    wind_speed_mph=9.3,  # Automatically validated
    condition=WeatherCondition.SUNNY
)
```

### Creating a Forecast

```python
forecast = WeatherForecast(
    location=location,
    current=current,
    daily_forecasts=[
        ForecastDay(
            date=datetime.now(ZoneInfo("Australia/Sydney")),
            max_temp_c=25.0,
            min_temp_c=18.0,
            condition=WeatherCondition.SUNNY,
            hourly_forecasts=[
                ForecastHour(
                    time=datetime.now(ZoneInfo("Australia/Sydney")),
                    temperature_c=22.5,
                    condition=WeatherCondition.PARTLY_CLOUDY
                )
            ]
        )
    ]
)
```

### Handling Alerts

```python
alert = WeatherAlert(
    alert_type=AlertType.RAIN,
    severity=AlertSeverity.MODERATE,
    title="Heavy Rain Warning",
    start_time=datetime.now(ZoneInfo("Australia/Sydney")),
    end_time=datetime.now(ZoneInfo("Australia/Sydney")) + timedelta(hours=24),
    affected_areas=["Sydney", "Central Coast"]
)

alerts = WeatherAlerts(
    location=location,
    alerts=[alert]
)
```

## Best Practices

1. **Timezone Handling**
   - Always use IANA timezone names
   - Store times in UTC, convert to local for display
   - Use ZoneInfo for timezone operations

2. **Unit Conversions**
   - Always provide both metric and imperial units
   - Let the model handle conversions
   - Use appropriate precision for each unit

3. **Validation**
   - Validate data before model creation
   - Handle validation errors gracefully
   - Use model methods for complex validation

4. **Metadata**
   - Use metadata for extensibility
   - Include source information
   - Track confidence levels

5. **Versioning**
   - Increment version for breaking changes
   - Document version changes
   - Support backward compatibility

## Error Handling

Common validation errors and how to handle them:

```python
try:
    weather = CurrentWeather(**data)
except ValidationError as e:
    # Handle validation errors
    logger.error(f"Validation error: {e}")
except ValueError as e:
    # Handle value errors
    logger.error(f"Value error: {e}")
```

## Performance Considerations

1. **Memory Usage**
   - Models are lightweight
   - Use lazy loading for large collections
   - Clear unused metadata

2. **Processing**
   - Validate early
   - Use model methods for complex operations
   - Cache frequently accessed data

3. **Serialization**
   - Use model_dump() for dict conversion
   - Use model_dump_json() for JSON
   - Handle timezone serialization carefully 