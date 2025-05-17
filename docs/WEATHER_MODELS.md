# Weather Data Models Documentation

> **Migration Note:** As of [DATE], the weather integration is migrating from IBM/The Weather Company to the Google Weather API. See `CHANGE_REQUEST - 1.1 Google Weather API.md` for rationale and migration plan.

The weather data models provide a comprehensive structure for handling weather data in the email digest system. All models inherit from `BaseWeatherModel` and include versioning, metadata, and timestamp tracking.

## Data Source Mapping

- **Primary Source:** Google Weather API (see `API_INTEGRATION.md` for request/response details)
- **Field Mapping:**
  - Google API fields (e.g., `currentWeather.temperature`, `currentWeather.weatherCode`, `dailyForecast.maxTemperature`) are mapped to internal model fields (e.g., `CurrentWeather.temperature_c`, `ForecastDay.max_temp_c`).
  - See usage examples below for mapping guidance.

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
    temperature_c: float  # Maps from Google: currentWeather.temperature
    temperature_f: float
    feels_like_c: float   # Maps from Google: currentWeather.apparentTemperature
    feels_like_f: float
    humidity: int  # 0-100
    wind_speed_kmh: float  # Maps from Google: currentWeather.windSpeed
    wind_speed_mph: float
    wind_direction: str    # Maps from Google: currentWeather.windDirection
    precipitation_mm: float  # Maps from Google: currentWeather.precipitation
    precipitation_inches: float
    uv_index: float
    condition: WeatherCondition  # Maps from Google: currentWeather.weatherCode
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
    date: datetime  # Maps from Google: dailyForecast.date
    max_temp_c: float  # Maps from Google: dailyForecast.maxTemperature
    max_temp_f: float
    min_temp_c: float  # Maps from Google: dailyForecast.minTemperature
    min_temp_f: float
    avg_temp_c: float
    avg_temp_f: float
    max_wind_speed_kmh: float  # Maps from Google: dailyForecast.windSpeed
    max_wind_speed_mph: float
    total_precipitation_mm: float
    total_precipitation_inches: float
    avg_humidity: int
    condition: WeatherCondition  # Maps from Google: dailyForecast.weatherCode
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
    SUNNY = "sunny"  # Maps from Google: weatherCode = "SUNNY"
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

### Getting Current Weather (from Google API response)

```python
# Example Google API response mapping
api_response = {
    "currentWeather": {
        "temperature": 22.5,
        "apparentTemperature": 23.0,
        "humidity": 65,
        "windSpeed": 15,
        "windDirection": "SE",
        "precipitation": 0,
        "weatherCode": "SUNNY"
    },
    "location": {
        "latitude": -33.8688,
        "longitude": 151.2093,
        "regionCode": "AU-NSW",
        "timezone": "Australia/Sydney"
    }
}

current = CurrentWeather(
    location=location,
    temperature_c=api_response["currentWeather"]["temperature"],
    temperature_f=convert_temperature(api_response["currentWeather"]["temperature"]),
    feels_like_c=api_response["currentWeather"]["apparentTemperature"],
    feels_like_f=convert_temperature(api_response["currentWeather"]["apparentTemperature"]),
    humidity=api_response["currentWeather"]["humidity"],
    wind_speed_kmh=api_response["currentWeather"]["windSpeed"],
    wind_speed_mph=convert_wind_speed(api_response["currentWeather"]["windSpeed"]),
    condition=WeatherCondition(api_response["currentWeather"]["weatherCode"])
)
```

### Creating a Forecast (from Google API response)

```python
forecast = WeatherForecast(
    location=location,
    current=current,
    daily_forecasts=[
        ForecastDay(
            date=datetime.strptime(day["date"], "%Y-%m-%d"),
            max_temp_c=day["maxTemperature"],
            min_temp_c=day["minTemperature"],
            condition=WeatherCondition(day["weatherCode"]),
            max_wind_speed_kmh=day["windSpeed"]
        ) for day in api_response.get("dailyForecast", [])
    ]
)
```

### Handling Alerts

```