from typing import Any, Dict, List, Optional

class ContentAssembler:
    def __init__(self, personality: str = 'formal', preferences: Optional[Dict[str, Any]] = None):
        self.personality = personality
        self.preferences = preferences or {}

    def assemble(self, user: Dict[str, Any], calendar_events: List[Dict[str, Any]], weather: Optional[Dict[str, Any]], summary: str) -> Dict[str, Any]:
        """
        Assemble all content sections into a context dict for template rendering.
        """
        context = {
            'user_name': user.get('name', 'Friend'),
            'greeting_time': self._greeting_time(),
            'calendar_events': self._format_calendar(calendar_events),
            'weather': self._format_weather(weather),
            'daily_summary': self._format_summary(summary),
            'personality': self.personality,
            'unsubscribe_url': user.get('unsubscribe_url', '#'),
            'preferences_url': user.get('preferences_url', '#'),
        }
        self._apply_personalization(context, user)
        self._apply_british_tone(context)
        self._validate(context)
        return context

    def _greeting_time(self) -> str:
        # Simple time-of-day logic, can be expanded
        from datetime import datetime
        hour = datetime.now().hour
        if hour < 12:
            return 'morning'
        elif hour < 18:
            return 'afternoon'
        else:
            return 'evening'

    def _format_calendar(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Formatting rules for calendar events
        return events

    def _format_weather(self, weather: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        # Formatting rules for weather
        if not weather:
            return None
        if self.preferences.get('weather_units') == 'fahrenheit':
            weather = weather.copy()
            weather['high'] = round(weather['high'] * 9/5 + 32)
            weather['low'] = round(weather['low'] * 9/5 + 32)
        return weather

    def _format_summary(self, summary: str) -> str:
        # Formatting rules for summary
        return summary.strip()

    def _apply_personalization(self, context: Dict[str, Any], user: Dict[str, Any]):
        # Replace tokens, apply user preferences, etc.
        pass

    def _apply_british_tone(self, context: Dict[str, Any]):
        # Adjust context for British idioms, formality, etc.
        pass

    def _validate(self, context: Dict[str, Any]):
        # Validate content completeness, formatting, and tone
        required = ['user_name', 'greeting_time', 'calendar_events', 'daily_summary']
        for key in required:
            if key not in context or context[key] is None:
                raise ValueError(f"Missing required content: {key}") 