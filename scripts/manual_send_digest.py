from datetime import datetime
from src.core.clients.weather_client import WeatherAPIClient
from src.core.processors.weather import WeatherProcessor
from src.core.processors.calendar import CalendarEventProcessor
from src.core.models.calendar import CalendarEventCollection, CalendarEvent, EventStatus, EventType
from src.digest_email.sender import EmailSender
from src.core.models.weather import WeatherForecast, ForecastDay, CurrentWeather, Location, WeatherAlerts, WeatherCondition, SYDNEY_TIMEZONE, ForecastHour
from zoneinfo import ZoneInfo
import os

from dotenv import load_dotenv
from src.api.motion import MotionClient
from src.utils.config import load_config

load_dotenv()

def fetch_user_info():
    # Read greeting name from environment variable
    user_name = os.getenv("EMAIL_GREETING_NAME", "Friend")
    return {"user_name": user_name}

def fetch_calendar_events():
    config = load_config()
    client = MotionClient(config.motion)
    now = datetime.now(SYDNEY_TIMEZONE)
    # Fetch tasks scheduled for today
    tasks = client.get_tasks_scheduled_for_today()
    # If tasks are not already a CalendarEventCollection, convert if needed
    if isinstance(tasks, CalendarEventCollection):
        return tasks
    # If tasks are TaskCollection, convert each to CalendarEvent if possible
    if hasattr(tasks, 'tasks'):
        events = [CalendarEvent.from_api_data(task.model_dump()) for task in tasks.tasks]
        return CalendarEventCollection(events)
    return tasks

def map_wind_direction(google_dir: str) -> str:
    # Map Google wind directions to 8-point compass
    mapping = {
        "NORTH": "N", "NORTHEAST": "NE", "EAST": "E", "SOUTHEAST": "SE",
        "SOUTH": "S", "SOUTHWEST": "SW", "WEST": "W", "NORTHWEST": "NW",
        "NORTH_NORTHEAST": "NE", "EAST_NORTHEAST": "NE", "EAST_SOUTHEAST": "SE",
        "SOUTH_SOUTHEAST": "SE", "SOUTH_SOUTHWEST": "SW", "WEST_SOUTHWEST": "SW",
        "WEST_NORTHWEST": "NW", "NORTH_NORTHWEST": "NW"
    }
    if not google_dir:
        return "N"
    google_dir = google_dir.replace(" ", "_").upper()
    return mapping.get(google_dir, "N")

def google_api_to_weather_forecast(api_response: dict) -> WeatherForecast:
    # Extract location info
    forecast_days = api_response.get("forecastDays", [])
    location_info = api_response.get("location", {})
    # Try to get timezone from response
    timezone = api_response.get("timeZone", {}).get("id", "Australia/Sydney")
    city = location_info.get("city", "Sydney")
    region = location_info.get("region", "New South Wales")
    country = location_info.get("country", "Australia")
    latitude = location_info.get("latitude", -33.8688)
    longitude = location_info.get("longitude", 151.2093)
    local_time = datetime.now(SYDNEY_TIMEZONE)
    location = Location(
        city=city,
        region=region,
        country=country,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        local_time=local_time
    )
    # Current weather: fallback to first daytimeForecast if available
    current = None
    if forecast_days:
        today = forecast_days[0]
        # Use daytimeForecast for current-like info
        day_part = today.get("daytimeForecast", {})
        temp_c = day_part.get("temperature", {}).get("value")
        if temp_c is None:
            temp_c = today.get("maxTemperature", {}).get("degrees", 20.0)
        temp_f = (temp_c * 9/5) + 32
        feels_c = day_part.get("feelsLike", {}).get("value", temp_c)
        feels_f = (feels_c * 9/5) + 32
        humidity = day_part.get("relativeHumidity", 50)
        wind_kmh = day_part.get("wind", {}).get("speed", {}).get("value", 0.0)
        wind_mph = wind_kmh / 1.60934
        wind_dir = map_wind_direction(day_part.get("wind", {}).get("direction", {}).get("cardinal", "N"))
        precip_mm = day_part.get("precipitation", {}).get("qpf", {}).get("quantity", 0.0)
        precip_in = precip_mm / 25.4
        uv = day_part.get("uvIndex", 0.0)
        cond = day_part.get("weatherCondition", {}).get("type", "unknown").replace(" ", "_").lower()
        obs_time = today.get("interval", {}).get("startTime", datetime.now(SYDNEY_TIMEZONE).isoformat())
        if isinstance(obs_time, str):
            try:
                obs_time = datetime.fromisoformat(obs_time.replace("Z", "+00:00"))
            except Exception:
                obs_time = datetime.now(SYDNEY_TIMEZONE)
        current = CurrentWeather(
            location=location,
            temperature_c=temp_c,
            temperature_f=temp_f,
            feels_like_c=feels_c,
            feels_like_f=feels_f,
            humidity=humidity,
            wind_speed_kmh=wind_kmh,
            wind_speed_mph=wind_mph,
            wind_direction=wind_dir,
            precipitation_mm=precip_mm,
            precipitation_inches=precip_in,
            uv_index=uv,
            condition=WeatherCondition(cond) if cond in WeatherCondition.__members__ else WeatherCondition.UNKNOWN,
            observation_time=obs_time
        )
    else:
        print("[DEBUG] No forecastDays in API response. Raw response:", api_response)
        # Fallback minimal current weather
        temp_c = 20.0
        temp_f = (temp_c * 9/5) + 32
        feels_c = temp_c
        feels_f = temp_f
        humidity = 50
        wind_kmh = 0.0
        wind_mph = 0.0
        wind_dir = "N"
        precip_mm = 0.0
        precip_in = 0.0
        uv = 0.0
        cond = "unknown"
        obs_time = datetime.now(SYDNEY_TIMEZONE)
        current = CurrentWeather(
            location=location,
            temperature_c=temp_c,
            temperature_f=temp_f,
            feels_like_c=feels_c,
            feels_like_f=feels_f,
            humidity=humidity,
            wind_speed_kmh=wind_kmh,
            wind_speed_mph=wind_mph,
            wind_direction=wind_dir,
            precipitation_mm=precip_mm,
            precipitation_inches=precip_in,
            uv_index=uv,
            condition=WeatherCondition.UNKNOWN,
            observation_time=obs_time
        )
    # Daily forecasts
    daily_forecasts = []
    if not forecast_days:
        print("[DEBUG] No daily forecasts in API response. Raw response:", api_response)
        now = datetime.now(SYDNEY_TIMEZONE)
        daily_forecasts.append(ForecastDay(
            date=now,
            max_temp_c=25.0,
            max_temp_f=(25.0 * 9/5) + 32,
            min_temp_c=15.0,
            min_temp_f=(15.0 * 9/5) + 32,
            avg_temp_c=20.0,
            avg_temp_f=(20.0 * 9/5) + 32,
            max_wind_speed_kmh=0.0,
            max_wind_speed_mph=0.0,
            total_precipitation_mm=0.0,
            total_precipitation_inches=0.0,
            avg_humidity=50,
            condition=WeatherCondition.UNKNOWN,
            uv_index=0.0,
            sunrise=now.replace(hour=6, minute=0),
            sunset=now.replace(hour=18, minute=0),
            hourly_forecasts=[]
        ))
    else:
        for day in forecast_days:
            # Date
            date = day.get("interval", {}).get("startTime")
            if not date:
                date = datetime.now(SYDNEY_TIMEZONE)
            elif isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except Exception:
                    date = datetime.now(SYDNEY_TIMEZONE)
            # Convert to Sydney time and use only the date part
            if date.tzinfo is not None:
                date = date.astimezone(SYDNEY_TIMEZONE)
            date = datetime(date.year, date.month, date.day, tzinfo=SYDNEY_TIMEZONE)
            # Max/Min Temp
            max_temp_c = day.get("maxTemperature", {}).get("degrees", 20.0)
            min_temp_c = day.get("minTemperature", {}).get("degrees", 15.0)
            max_temp_f = (max_temp_c * 9/5) + 32
            min_temp_f = (min_temp_c * 9/5) + 32
            avg_temp_c = (max_temp_c + min_temp_c) / 2
            avg_temp_f = (max_temp_f + min_temp_f) / 2
            # Wind
            wind_kmh = day.get("daytimeForecast", {}).get("wind", {}).get("speed", {}).get("value", 0.0)
            wind_mph = wind_kmh / 1.60934
            wind_dir = map_wind_direction(day.get("daytimeForecast", {}).get("wind", {}).get("direction", {}).get("cardinal", "N"))
            # Precipitation
            precip_mm = day.get("daytimeForecast", {}).get("precipitation", {}).get("qpf", {}).get("quantity", 0.0)
            precip_in = precip_mm / 25.4
            # Humidity
            humidity = day.get("daytimeForecast", {}).get("relativeHumidity", 50)
            # Condition
            cond = day.get("daytimeForecast", {}).get("weatherCondition", {}).get("type", "unknown").replace(" ", "_").lower()
            # UV
            uv = day.get("daytimeForecast", {}).get("uvIndex", 0.0)
            # Sunrise/Sunset
            sunrise = day.get("sunEvents", {}).get("sunriseTime", datetime.now(SYDNEY_TIMEZONE))
            sunset = day.get("sunEvents", {}).get("sunsetTime", datetime.now(SYDNEY_TIMEZONE))
            if isinstance(sunrise, str):
                try:
                    sunrise = datetime.fromisoformat(sunrise.replace("Z", "+00:00"))
                except Exception:
                    sunrise = datetime.now(SYDNEY_TIMEZONE)
            if isinstance(sunset, str):
                try:
                    sunset = datetime.fromisoformat(sunset.replace("Z", "+00:00"))
                except Exception:
                    sunset = datetime.now(SYDNEY_TIMEZONE)
            # Hourly forecasts (dummy if missing)
            hourly_forecasts = []
            # Use average values for the dummy hour
            if not hourly_forecasts:
                hourly_forecasts = [ForecastHour(
                    time=date,
                    temperature_c=avg_temp_c,
                    temperature_f=avg_temp_f,
                    feels_like_c=avg_temp_c,
                    feels_like_f=avg_temp_f,
                    humidity=humidity,
                    wind_speed_kmh=wind_kmh,
                    wind_speed_mph=wind_mph,
                    wind_direction=wind_dir,
                    precipitation_mm=precip_mm,
                    precipitation_inches=precip_in,
                    precipitation_chance=0,
                    condition=WeatherCondition(cond)
                )]
            daily_forecasts.append(ForecastDay(
                date=date,
                max_temp_c=max_temp_c,
                max_temp_f=max_temp_f,
                min_temp_c=min_temp_c,
                min_temp_f=min_temp_f,
                avg_temp_c=avg_temp_c,
                avg_temp_f=avg_temp_f,
                max_wind_speed_kmh=wind_kmh,
                max_wind_speed_mph=wind_mph,
                total_precipitation_mm=precip_mm,
                total_precipitation_inches=precip_in,
                avg_humidity=humidity,
                condition=WeatherCondition(cond) if cond in WeatherCondition.__members__ else WeatherCondition.UNKNOWN,
                uv_index=uv,
                sunrise=sunrise,
                sunset=sunset,
                hourly_forecasts=hourly_forecasts
            ))
    alerts = WeatherAlerts(location=location, alerts=[])
    return WeatherForecast(
        location=location,
        current=current,
        daily_forecasts=daily_forecasts,
        alerts=alerts
    )

def fetch_weather():
    weather_client = WeatherAPIClient()
    forecast_response = weather_client.get_forecast(days=1)
    forecast = google_api_to_weather_forecast(forecast_response)
    processor = WeatherProcessor(forecast)
    today = datetime.now(SYDNEY_TIMEZONE)
    try:
        return processor.get_daily_digest_weather(today)
    except Exception as e:
        # Fallback: use the first available forecast day
        if forecast.daily_forecasts:
            fallback_date = forecast.daily_forecasts[0].date
            print(f"[DEBUG] No forecast for {today.date()}, using fallback date {fallback_date.date()} due to: {e}")
            return processor.get_daily_digest_weather(fallback_date)
        else:
            print(f"[DEBUG] No forecast data available at all: {e}")
            raise

def send_digest():
    user_info = fetch_user_info()
    calendar_events = fetch_calendar_events()
    weather = fetch_weather()

    # Process calendar events for digest
    cal_processor = CalendarEventProcessor(calendar_events)
    today_events = cal_processor.get_daily_digest_events(datetime.now(SYDNEY_TIMEZONE))
    formatted_events = [
        cal_processor.format_event_for_digest(event) for event in today_events
    ]

    # Determine greeting time
    hour = datetime.now().hour
    if hour < 12:
        greeting_time = "morning"
    elif hour < 18:
        greeting_time = "afternoon"
    else:
        greeting_time = "evening"

    context = {
        "greeting_time": greeting_time,
        "user_name": user_info["user_name"],
        "calendar_events": formatted_events,
        "weather": weather,
        "daily_summary": "Here's your summary for today."
    }

    sender = EmailSender()
    sender.send_templated_email("daily_digest", context=context)

if __name__ == "__main__":
    send_digest()