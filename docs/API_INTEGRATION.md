# API Integration Specifications

> **Migration Note:** As of [DATE], the weather integration is migrating from IBM/The Weather Company to the Google Weather API. See `CHANGE_REQUEST - 1.1 Google Weather API.md` for rationale and migration plan.

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

## 2. Weather API Integration (Google)

### 2.1 Authentication
```python
# Authentication Method: API Key
# Stored in: AWS Secrets Manager
# Key Path: /digest/{env}/weather-api-key
```

### 2.2 Endpoints

#### Current Weather
```python
# Endpoint: https://weather.googleapis.com/v1/weather:lookup
# Method: POST
# Request Body:
#   - location: { latitude: float, longitude: float }
#   - units: 'CELSIUS' | 'FAHRENHEIT' (optional, default: CELSIUS)
#   - languageCode: 'en' (optional)
#   - key: {weather_api_key} (as URL param)

# Example Request
POST /v1/weather:lookup?key=YOUR_API_KEY
Content-Type: application/json
{
    "location": { "latitude": -33.8688, "longitude": 151.2093 },
    "units": "CELSIUS"
}

# Example Response
{
    "currentWeather": {
        "temperature": 22.5,
        "apparentTemperature": 23.0,
        "humidity": 65,
        "windSpeed": 15,
        "windDirection": "SE",
        "precipitation": 0,
        "weatherCode": "SUNNY",
        "weatherDescription": "Sunny"
    },
    "location": {
        "latitude": -33.8688,
        "longitude": 151.2093,
        "regionCode": "AU-NSW",
        "timezone": "Australia/Sydney"
    }
}
```

#### Daily Forecast
```python
# Endpoint: https://weather.googleapis.com/v1/weather:lookup
# Method: POST
# Request Body:
#   - location: { latitude: float, longitude: float }
#   - dailyForecastRequired: true
#   - days: int (1-7)
#   - units: 'CELSIUS' | 'FAHRENHEIT' (optional)
#   - key: {weather_api_key} (as URL param)

# Example Request
POST /v1/weather:lookup?key=YOUR_API_KEY
Content-Type: application/json
{
    "location": { "latitude": -33.8688, "longitude": 151.2093 },
    "dailyForecastRequired": true,
    "days": 1,
    "units": "CELSIUS"
}

# Example Response
{
    "dailyForecast": [
        {
            "date": "2024-03-20",
            "maxTemperature": 25.0,
            "minTemperature": 18.0,
            "weatherCode": "SUNNY",
            "precipitationProbability": 10,
            "windSpeed": 12
        }
    ]
}
```

### 2.3 Error Handling
```python
# Rate Limits
# - See Google API documentation for quota details

# Error Responses
{
    "error": {
        "code": 401,
        "message": "API key not valid. Please pass a valid API key."
    }
}

# Retry Strategy
# - Maximum 3 retries
# - Exponential backoff (5s, 10s, 20s)
# - Retry on: 429, 500, 502, 503, 504
```

### 2.4 Data Processing
- Map Google Weather API fields to internal models (see `docs/WEATHER_MODELS.md`).
- Validate all required fields and handle unit conversions as per internal standards.

### 2.5 References
- [Google Weather API Documentation](https://developers.google.com/maps/documentation/weather/overview)
- See also: `CHANGE_REQUEST - 1.1 Google Weather API.md`

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
