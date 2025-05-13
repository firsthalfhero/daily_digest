# Technical Design: Advanced Frequency Scheduling System

## 1. Core Data Models

### 1.1 Frequency Types Enum
```python
class FrequencyType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class DailyFrequencyType(str, Enum):
    EVERY_DAY = "daily_every_day"
    EVERY_WEEK_DAY = "daily_every_week_day"
    SPECIFIC_DAYS = "daily_specific_days"

class WeeklyFrequencyType(str, Enum):
    ANY_DAY = "weekly_any_day"
    ANY_WEEK_DAY = "weekly_any_week_day"
    SPECIFIC_DAYS = "weekly_specific_days"

class BiweeklyFrequencyType(str, Enum):
    FIRST_WEEK_ANY_DAY = "biweekly_first_week_any_day"
    FIRST_WEEK_ANY_WEEK_DAY = "biweekly_first_week_any_week_day"
    FIRST_WEEK_SPECIFIC_DAYS = "biweekly_first_week_specific_days"
    SECOND_WEEK_ANY_DAY = "biweekly_second_week_any_day"
    SECOND_WEEK_ANY_WEEK_DAY = "biweekly_second_week_any_week_day"
    SECOND_WEEK_SPECIFIC_DAYS = "biweekly_second_week_specific_days"

class MonthlyFrequencyType(str, Enum):
    FIRST_WEEK_DAY = "monthly_first_DAY"  # DAY will be replaced with actual day
    SECOND_WEEK_DAY = "monthly_second_DAY"
    THIRD_WEEK_DAY = "monthly_third_DAY"
    FOURTH_WEEK_DAY = "monthly_fourth_DAY"
    LAST_WEEK_DAY = "monthly_last_DAY"
    SPECIFIC_DAY = "monthly_SPECIFIC"  # e.g., monthly_15
    ANY_DAY_FIRST_WEEK = "monthly_any_day_first_week"
    ANY_DAY_SECOND_WEEK = "monthly_any_day_second_week"
    ANY_DAY_THIRD_WEEK = "monthly_any_day_third_week"
    ANY_DAY_FOURTH_WEEK = "monthly_any_day_fourth_week"
    ANY_DAY_LAST_WEEK = "monthly_any_day_last_week"
    ANY_WEEK_DAY_FIRST_WEEK = "monthly_any_week_day_first_week"
    ANY_WEEK_DAY_SECOND_WEEK = "monthly_any_week_day_second_week"
    ANY_WEEK_DAY_THIRD_WEEK = "monthly_any_week_day_third_week"
    ANY_WEEK_DAY_FOURTH_WEEK = "monthly_any_week_day_fourth_week"
    ANY_WEEK_DAY_LAST_WEEK = "monthly_any_week_day_last_week"
    LAST_DAY_OF_MONTH = "monthly_last_day_of_month"
    ANY_WEEK_DAY_OF_MONTH = "monthly_any_week_day_of_month"
    ANY_DAY_OF_MONTH = "monthly_any_day_of_month"

class QuarterlyFrequencyType(str, Enum):
    FIRST_DAY = "quarterly_first_day"
    FIRST_WEEK_DAY = "quarterly_first_week_day"
    FIRST_SPECIFIC_DAY = "quarterly_first_DAY"
    LAST_DAY = "quarterly_last_day"
    LAST_WEEK_DAY = "quarterly_last_week_day"
    LAST_SPECIFIC_DAY = "quarterly_last_DAY"
    ANY_DAY_FIRST_WEEK = "quarterly_any_day_first_week"
    ANY_DAY_SECOND_WEEK = "quarterly_any_day_second_week"
    ANY_DAY_LAST_WEEK = "quarterly_any_day_last_week"
    ANY_DAY_FIRST_MONTH = "quarterly_any_day_first_month"
    ANY_DAY_SECOND_MONTH = "quarterly_any_day_second_month"

class WeekDay(str, Enum):
    MONDAY = "MO"
    TUESDAY = "TU"
    WEDNESDAY = "WE"
    THURSDAY = "TH"
    FRIDAY = "FR"
    SATURDAY = "SA"
    SUNDAY = "SU"
```

### 1.2 Frequency Configuration Model
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union
from datetime import time

class FrequencyConfig(BaseModel):
    frequency_type: FrequencyType
    specific_type: Union[
        DailyFrequencyType,
        WeeklyFrequencyType,
        BiweeklyFrequencyType,
        MonthlyFrequencyType,
        QuarterlyFrequencyType
    ]
    days: Optional[List[WeekDay]] = None
    specific_day: Optional[int] = None  # For monthly specific days
    target_time: time = Field(default=time(6, 30))  # Default to 6:30 AM
    timezone: str = Field(default="Australia/Sydney")
    
    @validator('days')
    def validate_days(cls, v, values):
        if 'specific_type' in values:
            if values['specific_type'].endswith('_specific_days') and not v:
                raise ValueError("Days must be specified for specific_days frequency types")
            if v and not all(day in WeekDay for day in v):
                raise ValueError("Invalid day specified")
        return v

    @validator('specific_day')
    def validate_specific_day(cls, v, values):
        if 'specific_type' in values and values['specific_type'].startswith('monthly_') and v is not None:
            if not 1 <= v <= 31:
                raise ValueError("Specific day must be between 1 and 31")
        return v
```

## 2. Frequency Calculator Service

```python
from datetime import datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo

class FrequencyCalculator:
    def __init__(self, config: FrequencyConfig):
        self.config = config
        self.timezone = ZoneInfo(config.timezone)
    
    def get_next_occurrence(self, from_date: datetime) -> Optional[datetime]:
        """
        Calculate the next occurrence based on the frequency configuration.
        Returns None if no more occurrences are possible.
        """
        if self.config.frequency_type == FrequencyType.DAILY:
            return self._calculate_daily(from_date)
        elif self.config.frequency_type == FrequencyType.WEEKLY:
            return self._calculate_weekly(from_date)
        elif self.config.frequency_type == FrequencyType.BIWEEKLY:
            return self._calculate_biweekly(from_date)
        elif self.config.frequency_type == FrequencyType.MONTHLY:
            return self._calculate_monthly(from_date)
        elif self.config.frequency_type == FrequencyType.QUARTERLY:
            return self._calculate_quarterly(from_date)
        return None

    def _calculate_daily(self, from_date: datetime) -> Optional[datetime]:
        if self.config.specific_type == DailyFrequencyType.EVERY_DAY:
            return self._next_daily(from_date)
        elif self.config.specific_type == DailyFrequencyType.EVERY_WEEK_DAY:
            return self._next_weekday(from_date)
        elif self.config.specific_type == DailyFrequencyType.SPECIFIC_DAYS:
            return self._next_specific_days(from_date)
        return None

    def _calculate_weekly(self, from_date: datetime) -> Optional[datetime]:
        # Implementation for weekly calculations
        pass

    def _calculate_biweekly(self, from_date: datetime) -> Optional[datetime]:
        # Implementation for biweekly calculations
        pass

    def _calculate_monthly(self, from_date: datetime) -> Optional[datetime]:
        # Implementation for monthly calculations
        pass

    def _calculate_quarterly(self, from_date: datetime) -> Optional[datetime]:
        # Implementation for quarterly calculations
        pass

    def _next_daily(self, from_date: datetime) -> datetime:
        next_date = from_date + timedelta(days=1)
        return next_date.replace(
            hour=self.config.target_time.hour,
            minute=self.config.target_time.minute,
            second=0,
            microsecond=0
        )

    def _next_weekday(self, from_date: datetime) -> datetime:
        next_date = from_date + timedelta(days=1)
        while next_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            next_date += timedelta(days=1)
        return next_date.replace(
            hour=self.config.target_time.hour,
            minute=self.config.target_time.minute,
            second=0,
            microsecond=0
        )

    def _next_specific_days(self, from_date: datetime) -> Optional[datetime]:
        # Implementation for specific days calculation
        pass
```

## 3. Scheduler Service

```python
from typing import Optional, Dict
from datetime import datetime
import asyncio
from zoneinfo import ZoneInfo

class AdvancedScheduler:
    def __init__(self):
        self.frequency_calculator: Optional[FrequencyCalculator] = None
        self.config: Optional[FrequencyConfig] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, config: FrequencyConfig):
        """Start the scheduler with the given frequency configuration."""
        self.config = config
        self.frequency_calculator = FrequencyCalculator(config)
        self._running = True
        self._task = asyncio.create_task(self._run())
    
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            await self._task
    
    async def _run(self):
        """Main scheduler loop."""
        while self._running:
            now = datetime.now(ZoneInfo(self.config.timezone))
            next_occurrence = self.frequency_calculator.get_next_occurrence(now)
            
            if next_occurrence:
                wait_seconds = (next_occurrence - now).total_seconds()
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                    await self._trigger_event()
                else:
                    await asyncio.sleep(1)  # Prevent tight loop
            else:
                await asyncio.sleep(60)  # Check again in a minute
    
    async def _trigger_event(self):
        """Trigger the scheduled event."""
        # Implementation for triggering the actual event
        pass
```

## 4. Configuration Storage

```python
from typing import Optional
import json
from pathlib import Path

class FrequencyConfigStorage:
    def __init__(self, config_path: Path):
        self.config_path = config_path
    
    def save_config(self, config: FrequencyConfig) -> None:
        """Save frequency configuration to storage."""
        with open(self.config_path, 'w') as f:
            json.dump(config.dict(), f, default=str)
    
    def load_config(self) -> Optional[FrequencyConfig]:
        """Load frequency configuration from storage."""
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                return FrequencyConfig.parse_obj(data)
        except FileNotFoundError:
            return None
```

## 5. Usage Example

```python
# Example usage
async def main():
    # Create frequency configuration
    config = FrequencyConfig(
        frequency_type=FrequencyType.WEEKLY,
        specific_type=WeeklyFrequencyType.SPECIFIC_DAYS,
        days=[WeekDay.MONDAY, WeekDay.WEDNESDAY, WeekDay.FRIDAY],
        target_time=time(6, 30),
        timezone="Australia/Sydney"
    )
    
    # Initialize scheduler
    scheduler = AdvancedScheduler()
    
    # Start scheduler
    await scheduler.start(config)
    
    try:
        # Keep the program running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Clean shutdown
        await scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## 6. Integration Points

1. **Event Trigger System**
   - The scheduler's `_trigger_event` method should be connected to the existing digest generation system
   - Events should be logged and monitored
   - Failed events should be retried according to the retry policy

2. **Configuration Management**
   - Add API endpoints for updating frequency configuration
   - Implement configuration validation
   - Add configuration versioning

3. **Monitoring and Logging**
   - Add comprehensive logging for scheduler operations
   - Implement monitoring for missed events
   - Add metrics for scheduler performance

4. **Error Handling**
   - Implement robust error handling for all frequency calculations
   - Add validation for edge cases (e.g., month end dates)
   - Handle timezone transitions (DST)

## 7. Testing Strategy

1. **Unit Tests**
   - Test each frequency type calculation
   - Validate configuration models
   - Test timezone handling
   - Test edge cases

2. **Integration Tests**
   - Test scheduler with different configurations
   - Test configuration storage
   - Test event triggering

3. **End-to-End Tests**
   - Test complete scheduling cycle
   - Test with real digest generation
   - Test error recovery