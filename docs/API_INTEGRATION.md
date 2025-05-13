# API Integration Specifications

## 1. Motion API Integration

### 1.1 Authentication and Configuration
```python
# Authentication Method: Bearer Token
# Stored in: AWS Secrets Manager
# Key Path: /digest/{env}/motion-api-key

# API URL Configuration
# Stored in: Environment Variable
# Variable Name: MOTION_API_URL
```

### 1.2 Endpoints

#### Calendar Events
```python
# Endpoint: {MOTION_API_URL}/calendar/events
# Method: GET
# Parameters:
#   - start_date: YYYY-MM-DD (required)
#   - end_date: YYYY-MM-DD (required)
#   - timezone: Australia/Sydney (required)

# Example Request
GET /calendar/events?start_date=2024-03-20&end_date=2024-03-20&timezone=Australia/Sydney
Authorization: Bearer {motion_api_key}

# Example Response
{
    "events": [
        {
            "id": "evt_123",
            "title": "Team Meeting",
            "start_time": "2024-03-20T09:00:00+10:00",
            "end_time": "2024-03-20T10:00:00+10:00",
            "location": "Conference Room A",
            "description": "Weekly team sync",
            "status": "confirmed"
        }
    ]
}
```

### 1.3 Error Handling
```python
# Rate Limits
# - 100 requests per minute
# - 1000 requests per hour

# Error Responses
{
    "error": {
        "code": "rate_limit_exceeded",
        "message": "Rate limit exceeded",
        "retry_after": 60  # seconds
    }
}

# Retry Strategy
# - Maximum 3 retries
# - Exponential backoff (5s, 10s, 20s)
# - Retry on: 429, 500, 502, 503, 504
```

### 1.4 Data Processing
```python
# Required Fields
required_fields = [
    'id',
    'title',
    'start_time',
    'end_time',
    'status'
]

# Timezone Handling
# - All times stored in UTC
# - Convert to Sydney time for display
# - Handle DST transitions

# Event Filtering
# - Filter out declined/cancelled events
# - Sort by start time
# - Group by time of day (morning/afternoon/evening)
```

## 2. Weather API Integration

### 2.1 Authentication
```python
# Authentication Method: API Key
# Stored in: AWS Secrets Manager
# Key Path: /digest/{env}/weather-api-key
```

### 2.2 Endpoints

#### Current Weather
```python
# Endpoint: https://api.weather.com/v1/current
# Method: GET
# Parameters:
#   - location: Sydney,AU (required)
#   - units: metric (required)

# Example Request
GET /v1/current?location=Sydney,AU&units=metric
X-API-Key: {weather_api_key}

# Example Response
{
    "current": {
        "temperature": 22.5,
        "feels_like": 23.0,
        "conditions": "Sunny",
        "humidity": 65,
        "wind_speed": 15,
        "wind_direction": "SE",
        "precipitation": 0,
        "uv_index": 8
    }
}
```

#### Daily Forecast
```python
# Endpoint: https://api.weather.com/v1/forecast
# Method: GET
# Parameters:
#   - location: Sydney,AU (required)
#   - units: metric (required)
#   - days: 1 (required)

# Example Response
{
    "forecast": [
        {
            "time": "09:00",
            "temperature": 21.0,
            "conditions": "Sunny",
            "precipitation_chance": 10,
            "wind_speed": 12
        }
    ]
}
```

### 2.3 Error Handling
```python
# Rate Limits
# - 60 requests per minute
# - 1000 requests per day

# Error Responses
{
    "error": {
        "code": "invalid_api_key",
        "message": "Invalid API key provided"
    }
}

# Retry Strategy
# - Maximum 3 retries
# - Exponential backoff (5s, 10s, 20s)
# - Retry on: 429, 500, 502, 503, 504
```

### 2.4 Data Processing
```python
# Weather Data Models
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
    AlertType
)

# Model Usage Example
location = Location(
    city="Sydney",
    region="NSW",
    country="Australia",
    latitude=-33.8688,
    longitude=151.2093,
    timezone="Australia/Sydney"
)

current_weather = CurrentWeather(
    location=location,
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
    condition=WeatherCondition.SUNNY
)

# Data Validation
# - All models inherit from BaseWeatherModel
# - Automatic unit conversion (C/F, mm/inches, km/h/mph)
# - Timezone validation and conversion
# - Coordinate validation (-90 to 90 lat, -180 to 180 lon)
# - Chronological ordering for forecasts
# - Alert overlap detection

# Required Fields and Validation
required_fields = {
    'location': [
        'city',
        'latitude',
        'longitude',
        'timezone'
    ],
    'current_weather': [
        'temperature_c',
        'temperature_f',
        'humidity',
        'wind_speed_kmh',
        'wind_speed_mph',
        'condition'
    ],
    'forecast': [
        'date',
        'max_temp_c',
        'min_temp_c',
        'condition',
        'hourly_forecasts'
    ],
    'alert': [
        'alert_type',
        'severity',
        'title',
        'start_time',
        'end_time'
    ]
}

# Weather Conditions
weather_conditions = {
    'SUNNY': '☀️',
    'PARTLY_CLOUDY': '⛅',
    'CLOUDY': '☁️',
    'RAIN': '🌧️',
    'THUNDERSTORM': '⛈️',
    'SNOW': '❄️',
    'FOG': '🌫️',
    'WINDY': '💨'
}

# Alert Types and Severity
alert_types = {
    'RAIN': 'Rain Warning',
    'WIND': 'Wind Warning',
    'THUNDERSTORM': 'Thunderstorm Warning',
    'FLOOD': 'Flood Warning',
    'FIRE': 'Fire Warning'
}

alert_severity = {
    'MINOR': 'Minor',
    'MODERATE': 'Moderate',
    'SEVERE': 'Severe',
    'EXTREME': 'Extreme'
}

# Data Processing Guidelines
# 1. Location Processing
#    - Validate coordinates
#    - Verify timezone
#    - Format city/region names
#
# 2. Current Weather
#    - Convert temperatures (C/F)
#    - Convert precipitation (mm/inches)
#    - Convert wind speeds (km/h/mph)
#    - Validate observation time
#
# 3. Forecast Processing
#    - Ensure chronological order
#    - Validate temperature ranges
#    - Check sunrise/sunset times
#    - Process hourly forecasts
#
# 4. Alert Processing
#    - Check for overlapping alerts
#    - Validate time periods
#    - Group by severity
#    - Sort by start time
```

## 3. Implementation Guidelines

### 3.1 API Client Structure
```python
class BaseAPIClient:
    def __init__(self, api_key, max_retries=3, retry_delay=5):
        self.api_key = api_key
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()

    def _make_request(self, method, url, **kwargs):
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay * (2 ** attempt))
```

### 3.2 Error Handling
```python
class APIError(Exception):
    def __init__(self, message, code=None, retry_after=None):
        self.message = message
        self.code = code
        self.retry_after = retry_after
        super().__init__(self.message)

def handle_api_error(response):
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        raise APIError("Rate limit exceeded", "rate_limit", retry_after)
    # Handle other error cases
```

### 3.3 Data Validation
```python
def validate_response(data, required_fields):
    missing_fields = [field for field in required_fields 
                     if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    return data
```

## 4. Testing Requirements

### 4.1 Unit Tests
- Authentication handling
- Request formatting
- Response parsing
- Error handling
- Retry logic
- Data validation

### 4.2 Integration Tests
- API connectivity
- Rate limit handling
- Error recovery
- Data processing
- Timezone handling

### 4.3 Mock Responses
```python
# Example mock responses for testing
MOCK_CALENDAR_RESPONSE = {
    "events": [
        {
            "id": "evt_123",
            "title": "Test Meeting",
            "start_time": "2024-03-20T09:00:00+10:00",
            "end_time": "2024-03-20T10:00:00+10:00",
            "status": "confirmed"
        }
    ]
}

MOCK_WEATHER_RESPONSE = {
    "current": {
        "temperature": 22.5,
        "conditions": "Sunny",
        "precipitation": 0
    }
}
```

## 5. Monitoring

### 5.1 Key Metrics
- API response times
- Error rates
- Rate limit hits
- Retry attempts
- Data validation failures

### 5.2 Alerts
- API unavailability
- High error rates
- Rate limit exhaustion
- Invalid responses
- Authentication failures
