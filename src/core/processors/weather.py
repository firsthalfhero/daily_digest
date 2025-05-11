"""
Weather data processor for digest email preparation.

This module provides specialized processing of weather data for the daily digest email,
including filtering, formatting, summary generation, and trend analysis.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from zoneinfo import ZoneInfo

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
    AlertType,
    AlertSeverity,
    SYDNEY_TIMEZONE,
)
from src.utils.exceptions import ValidationError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WeatherProcessor:
    """
    Processes weather data for digest email preparation.
    
    This class provides specialized methods for processing weather data
    specifically for the daily digest email, including digest-specific
    filtering, formatting, summary generation, and trend analysis.
    """
    
    def __init__(self, forecast: WeatherForecast):
        """
        Initialize the processor with a weather forecast.
        
        Args:
            forecast: Weather forecast data to process
        """
        self.forecast = forecast
        self._validate_forecast()
    
    def _validate_forecast(self) -> None:
        """Validate the forecast data."""
        if not isinstance(self.forecast, WeatherForecast):
            raise ValidationError("Invalid forecast data type")
        
        # Ensure forecast is for Sydney
        if self.forecast.location.city != "Sydney":
            raise ValidationError("Forecast must be for Sydney")
        
        # Validate chronological order of forecasts
        for i in range(len(self.forecast.daily_forecasts) - 1):
            current = self.forecast.daily_forecasts[i]
            next_day = self.forecast.daily_forecasts[i + 1]
            if current.date >= next_day.date:
                raise ValidationError("Daily forecasts must be in chronological order")
    
    def get_daily_digest_weather(self, date: datetime) -> Dict[str, Any]:
        """
        Get weather data for the daily digest, filtered and processed appropriately.
        
        Args:
            date: The date to get weather for
            
        Returns:
            Dict[str, Any]: Processed weather data for the digest
        """
        # Get the forecast day that matches the date
        target_date = date.date()
        daily_forecast = next(
            (day for day in self.forecast.daily_forecasts 
             if day.date.date() == target_date),
            None
        )
        
        if not daily_forecast:
            raise ValidationError(f"No forecast available for {date.date()}")
        
        # Get current conditions if date is today
        current = self.forecast.current if date.date() == datetime.now(SYDNEY_TIMEZONE).date() else None
        
        # Get any active alerts
        alerts = self._get_active_alerts(date)
        
        # Generate weather summary
        summary = self._generate_weather_summary(daily_forecast, current)
        
        # Analyze trends
        trends = self._analyze_weather_trends(daily_forecast)
        
        # Assess weather impact
        impact = self._assess_weather_impact(daily_forecast, alerts)
        
        return {
            "date": date.strftime("%A, %B %d, %Y"),
            "current": self._format_current_weather(current) if current else None,
            "forecast": self._format_daily_forecast(daily_forecast),
            "alerts": self._format_alerts(alerts),
            "summary": summary,
            "trends": trends,
            "impact": impact,
        }
    
    def _get_active_alerts(self, date: datetime) -> List[WeatherAlert]:
        """
        Get active weather alerts for the specified date.
        
        Args:
            date: The date to check alerts for
            
        Returns:
            List[WeatherAlert]: Active weather alerts
        """
        if not hasattr(self.forecast, 'alerts'):
            return []
            
        target_date = date.date()
        return [
            alert for alert in self.forecast.alerts.alerts
            if alert.start_time.date() <= target_date <= alert.end_time.date()
        ]
    
    def _generate_weather_summary(
        self,
        daily_forecast: ForecastDay,
        current: Optional[CurrentWeather] = None
    ) -> str:
        """
        Generate a natural language summary of the weather.
        
        Args:
            daily_forecast: Daily forecast data
            current: Optional current weather data
            
        Returns:
            str: Natural language weather summary
        """
        parts = []
        
        # Add current conditions if available
        if current:
            temp = current.temperature_c
            condition = current.condition.value.title()
            parts.append(f"Currently {condition} at {temp}°C")
        
        # Add daily forecast
        max_temp = daily_forecast.max_temp_c
        min_temp = daily_forecast.min_temp_c
        condition = daily_forecast.condition.value.title()
        
        parts.append(
            f"Today will be {condition} with a high of {max_temp}°C "
            f"and a low of {min_temp}°C"
        )
        
        # Add precipitation if significant
        if daily_forecast.total_precipitation_mm > 0:
            parts.append(
                f"Expect {daily_forecast.total_precipitation_mm}mm of rain"
            )
        
        # Add wind if significant
        if daily_forecast.max_wind_speed_kmh > 20:
            parts.append(
                f"Winds up to {daily_forecast.max_wind_speed_kmh}km/h"
            )
        
        return " ".join(parts)
    
    def _analyze_weather_trends(self, daily_forecast: ForecastDay) -> Dict[str, Any]:
        """
        Analyze weather trends for the day.
        
        Args:
            daily_forecast: Daily forecast data
            
        Returns:
            Dict[str, Any]: Weather trend analysis
        """
        # Analyze temperature trend
        hourly_temps = [hour.temperature_c for hour in daily_forecast.hourly_forecasts]
        temp_trend = "stable"
        if len(hourly_temps) >= 2:
            temp_diff = hourly_temps[-1] - hourly_temps[0]
            if abs(temp_diff) > 5:
                temp_trend = "warming" if temp_diff > 0 else "cooling"
        
        # Analyze precipitation trend
        hourly_precip = [hour.precipitation_chance for hour in daily_forecast.hourly_forecasts]
        precip_trend = "stable"
        if len(hourly_precip) >= 2:
            precip_diff = hourly_precip[-1] - hourly_precip[0]
            if abs(precip_diff) > 20:
                precip_trend = "increasing" if precip_diff > 0 else "decreasing"
        
        # Analyze condition changes
        conditions = [hour.condition for hour in daily_forecast.hourly_forecasts]
        condition_changes = len(set(conditions))
        
        return {
            "temperature_trend": temp_trend,
            "precipitation_trend": precip_trend,
            "condition_changes": condition_changes,
            "max_temperature": max(hourly_temps),
            "min_temperature": min(hourly_temps),
            "max_precipitation_chance": max(hourly_precip),
        }
    
    def _assess_weather_impact(
        self,
        daily_forecast: ForecastDay,
        alerts: List[WeatherAlert]
    ) -> Dict[str, Any]:
        """
        Assess the impact of weather conditions.
        
        Args:
            daily_forecast: Daily forecast data
            alerts: Active weather alerts
            
        Returns:
            Dict[str, Any]: Weather impact assessment
        """
        impact = {
            "severity": "low",
            "concerns": [],
            "recommendations": []
        }
        
        # Check temperature extremes
        if daily_forecast.max_temp_c > 35:
            impact["severity"] = "high"
            impact["concerns"].append("High temperature")
            impact["recommendations"].append("Stay hydrated and avoid prolonged sun exposure")
        elif daily_forecast.min_temp_c < 10:
            impact["concerns"].append("Low temperature")
            impact["recommendations"].append("Dress warmly")
        
        # Check precipitation
        if daily_forecast.total_precipitation_mm > 10:
            impact["severity"] = "moderate"
            impact["concerns"].append("Significant rainfall")
            impact["recommendations"].append("Carry an umbrella")
        
        # Check wind
        if daily_forecast.max_wind_speed_kmh > 30:
            impact["severity"] = "moderate"
            impact["concerns"].append("Strong winds")
            impact["recommendations"].append("Secure loose objects")
        
        # Check UV index
        if daily_forecast.uv_index > 8:
            impact["severity"] = "moderate"
            impact["concerns"].append("High UV index")
            impact["recommendations"].append("Use sun protection")
        
        # Check alerts
        if alerts:
            impact["severity"] = "high"
            for alert in alerts:
                impact["concerns"].append(f"{alert.alert_type.value.title()} alert: {alert.title}")
                impact["recommendations"].append(alert.description)
        
        return impact
    
    def _format_current_weather(self, current: CurrentWeather) -> Dict[str, Any]:
        """
        Format current weather for display.
        
        Args:
            current: Current weather data
            
        Returns:
            Dict[str, Any]: Formatted current weather
        """
        return {
            "temperature": f"{current.temperature_c}°C",
            "feels_like": f"{current.feels_like_c}°C",
            "condition": current.condition.value.title(),
            "humidity": f"{current.humidity}%",
            "wind": f"{current.wind_speed_kmh}km/h {current.wind_direction}",
            "precipitation": f"{current.precipitation_mm}mm",
            "uv_index": current.uv_index,
            "observation_time": current.observation_time.strftime("%I:%M %p").lstrip("0"),
        }
    
    def _format_daily_forecast(self, daily_forecast: ForecastDay) -> Dict[str, Any]:
        """
        Format daily forecast for display.
        
        Args:
            daily_forecast: Daily forecast data
            
        Returns:
            Dict[str, Any]: Formatted daily forecast
        """
        return {
            "date": daily_forecast.date.strftime("%A, %B %d"),
            "condition": daily_forecast.condition.value.title(),
            "temperature": {
                "max": f"{daily_forecast.max_temp_c}°C",
                "min": f"{daily_forecast.min_temp_c}°C",
                "average": f"{daily_forecast.avg_temp_c}°C",
            },
            "precipitation": {
                "total": f"{daily_forecast.total_precipitation_mm}mm",
                "chance": f"{max(hour.precipitation_chance for hour in daily_forecast.hourly_forecasts)}%",
            },
            "wind": f"{daily_forecast.max_wind_speed_kmh}km/h",
            "humidity": f"{daily_forecast.avg_humidity}%",
            "uv_index": daily_forecast.uv_index,
            "sunrise": daily_forecast.sunrise.strftime("%I:%M %p").lstrip("0"),
            "sunset": daily_forecast.sunset.strftime("%I:%M %p").lstrip("0"),
            "hourly": [
                {
                    "time": hour.time.strftime("%I:%M %p").lstrip("0"),
                    "temperature": f"{hour.temperature_c}°C",
                    "condition": hour.condition.value.title(),
                    "precipitation_chance": f"{hour.precipitation_chance}%",
                    "wind_speed": f"{hour.wind_speed_kmh}km/h",
                }
                for hour in daily_forecast.hourly_forecasts
            ],
        }
    
    def _format_alerts(self, alerts: List[WeatherAlert]) -> List[Dict[str, Any]]:
        """
        Format weather alerts for display.
        
        Args:
            alerts: List of weather alerts
            
        Returns:
            List[Dict[str, Any]]: Formatted weather alerts
        """
        return [
            {
                "type": alert.alert_type.value.title(),
                "severity": alert.severity.value.title(),
                "title": alert.title,
                "description": alert.description,
                "start_time": alert.start_time.strftime("%I:%M %p").lstrip("0"),
                "end_time": alert.end_time.strftime("%I:%M %p").lstrip("0"),
                "affected_areas": ", ".join(alert.affected_areas),
            }
            for alert in sorted(alerts, key=lambda x: x.severity, reverse=True)
        ]
    
    def validate_weather_data(self) -> Tuple[bool, List[str]]:
        """
        Validate weather data for digest inclusion.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list of validation messages)
        """
        messages = []
        
        # Validate forecast structure
        if not self.forecast.daily_forecasts:
            messages.append("No daily forecasts available")
        
        # Validate current weather if available
        if self.forecast.current:
            current = self.forecast.current
            if current.temperature_c < -50 or current.temperature_c > 50:
                messages.append("Current temperature outside valid range")
            if current.humidity < 0 or current.humidity > 100:
                messages.append("Current humidity outside valid range")
        
        # Validate daily forecasts
        for day in self.forecast.daily_forecasts:
            if day.max_temp_c < day.min_temp_c:
                messages.append(f"Invalid temperature range for {day.date.date()}")
            if not day.hourly_forecasts:
                messages.append(f"No hourly forecasts for {day.date.date()}")
        
        # Validate alerts if present
        if hasattr(self.forecast, 'alerts'):
            for alert in self.forecast.alerts.alerts:
                if alert.start_time >= alert.end_time:
                    messages.append(f"Invalid alert time range: {alert.title}")
        
        return len(messages) == 0, messages 