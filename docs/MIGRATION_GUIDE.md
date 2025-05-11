# Weather Models Migration Guide

## Version History

### Version 1.0.0 (Current)
- Initial release of weather data models
- Complete model hierarchy with validation
- Unit conversion support
- Timezone handling
- Alert system

## Migration Steps

### From Pre-Model System

If you're migrating from a system without structured models:

1. **Data Structure Changes**
   ```python
   # Old format
   weather_data = {
       "temp": 22.5,  # Celsius only
       "wind": 15.0,  # km/h only
       "rain": 0.0,   # mm only
       "time": "2024-03-20T10:00:00"  # No timezone
   }

   # New format
   from src.core.models.weather import CurrentWeather, Location
   from datetime import datetime
   from zoneinfo import ZoneInfo

   location = Location(
       city="Sydney",
       region="NSW",
       country="Australia",
       latitude=-33.8688,
       longitude=151.2093,
       timezone="Australia/Sydney",
       local_time=datetime.now(ZoneInfo("Australia/Sydney"))
   )

   weather = CurrentWeather(
       location=location,
       temperature_c=22.5,
       temperature_f=72.5,  # Added
       wind_speed_kmh=15.0,
       wind_speed_mph=9.3,  # Added
       precipitation_mm=0.0,
       precipitation_inches=0.0,  # Added
       observation_time=datetime.now(ZoneInfo("Australia/Sydney"))
   )
   ```

2. **Timezone Handling**
   ```python
   # Old format
   time = "2024-03-20T10:00:00"  # Ambiguous timezone

   # New format
   from zoneinfo import ZoneInfo
   time = datetime.now(ZoneInfo("Australia/Sydney"))
   ```

3. **Weather Conditions**
   ```python
   # Old format
   condition = "sunny"  # String literal

   # New format
   from src.core.models.weather import WeatherCondition
   condition = WeatherCondition.SUNNY  # Enum
   ```

4. **Alert System**
   ```python
   # Old format
   alert = {
       "type": "rain",
       "level": "moderate",
       "message": "Heavy rain expected"
   }

   # New format
   from src.core.models.weather import WeatherAlert, AlertType, AlertSeverity
   alert = WeatherAlert(
       alert_type=AlertType.RAIN,
       severity=AlertSeverity.MODERATE,
       title="Heavy Rain Warning",
       description="Heavy rain expected",
       start_time=datetime.now(ZoneInfo("Australia/Sydney")),
       end_time=datetime.now(ZoneInfo("Australia/Sydney")) + timedelta(hours=24)
   )
   ```

### Migration Checklist

1. **Data Validation**
   - [ ] Update all temperature values to include both C and F
   - [ ] Update all wind speeds to include both km/h and mph
   - [ ] Update all precipitation values to include both mm and inches
   - [ ] Add timezone information to all datetime fields
   - [ ] Convert weather conditions to enum values
   - [ ] Update alert system to use new model

2. **Code Updates**
   - [ ] Import new model classes
   - [ ] Update model instantiation
   - [ ] Add validation error handling
   - [ ] Update serialization/deserialization
   - [ ] Update API client to use new models

3. **Testing**
   - [ ] Update unit tests to use new models
   - [ ] Add validation test cases
   - [ ] Test unit conversions
   - [ ] Test timezone handling
   - [ ] Test alert system

4. **Documentation**
   - [ ] Update API documentation
   - [ ] Update code examples
   - [ ] Document validation rules
   - [ ] Document error handling

## Breaking Changes

1. **Required Fields**
   - All models now require both metric and imperial units
   - All datetime fields must include timezone information
   - Weather conditions must use enum values
   - Alerts must include start and end times

2. **Validation Rules**
   - Stricter validation for coordinates
   - Stricter validation for timezone
   - Required unit conversion validation
   - Required chronological ordering for forecasts
   - Required alert overlap detection

3. **Error Handling**
   - New validation errors for unit conversion
   - New validation errors for timezone
   - New validation errors for chronological ordering
   - New validation errors for alert overlap

## Backward Compatibility

The models include some backward compatibility features:

1. **Default Values**
   ```python
   # These fields have defaults
   version: str = "1.0.0"
   metadata: Dict[str, Any] = {}
   updated_at: Optional[datetime] = None
   ```

2. **Optional Fields**
   ```python
   # These fields are optional
   url: Optional[str] = None  # In WeatherAlert
   description: Optional[str] = None  # In WeatherAlert
   ```

3. **Flexible Metadata**
   ```python
   # Add old fields to metadata if needed
   model.metadata["old_field"] = old_value
   ```

## Migration Tools

1. **Data Conversion**
   ```python
   def convert_temperature(celsius: float) -> float:
       return (celsius * 9/5) + 32

   def convert_wind_speed(kmh: float) -> float:
       return kmh * 0.621371

   def convert_precipitation(mm: float) -> float:
       return mm * 0.0393701
   ```

2. **Timezone Conversion**
   ```python
   def add_timezone(dt: datetime, timezone: str) -> datetime:
       return dt.replace(tzinfo=ZoneInfo(timezone))
   ```

3. **Condition Conversion**
   ```python
   def convert_condition(condition: str) -> WeatherCondition:
       condition_map = {
           "sunny": WeatherCondition.SUNNY,
           "partly cloudy": WeatherCondition.PARTLY_CLOUDY,
           "cloudy": WeatherCondition.CLOUDY,
           "rain": WeatherCondition.RAIN,
           "thunderstorm": WeatherCondition.THUNDERSTORM
       }
       return condition_map.get(condition.lower(), WeatherCondition.CLOUDY)
   ```

## Support

For migration support:
1. Check the test suite for examples
2. Review the model documentation
3. Use the migration tools provided
4. Contact the development team for assistance

## Future Versions

Planned changes for future versions:
1. Additional weather conditions
2. Extended alert types
3. Enhanced metadata support
4. Performance optimizations
5. Additional validation rules 