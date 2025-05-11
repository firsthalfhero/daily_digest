### Phase 1: Foundation Setup
1. **Project Structure**
```python
daily_digest/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py        # Environment variables and config
│   ├── core/
│   │   ├── __init__.py
│   │   ├── scheduler.py       # Basic scheduler implementation
│   │   └── logger.py          # Basic operation logging
│   ├── api/
│   │   ├── __init__.py
│   │   ├── motion_client.py   # Motion API client
│   │   └── weather_client.py  # Weather API client
│   ├── email/
│   │   ├── __init__.py
│   │   ├── template.py        # Mobile-first email template
│   │   └── sender.py          # Email delivery with retry
│   └── digest/
│       ├── __init__.py
│       ├── generator.py       # Digest content generation
│       └── formatter.py       # Content formatting
├── tests/
│   └── __init__.py
├── .env.example              # Template for environment variables
├── .env                      # Actual environment variables (git-ignored)
├── requirements.txt          # Project dependencies
└── README.md                # Project documentation
```

2. **Initial Dependencies**
```txt
# requirements.txt
python-dotenv==1.0.0        # Environment variable management
requests==2.31.0            # API clients
pytz==2024.1               # Timezone handling
jinja2==3.1.3              # Email templating
python-dateutil==2.8.2     # Date handling
```

3. **Configuration Setup**
```python
# src/config/settings.py
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    # API Credentials
    MOTION_API_KEY = os.getenv('MOTION_API_KEY')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    EMAIL_SERVICE_KEY = os.getenv('EMAIL_SERVICE_KEY')
    
    # Email Settings
    EMAIL_FROM = os.getenv('EMAIL_FROM')
    EMAIL_TO = os.getenv('EMAIL_TO')
    
    # Scheduling
    TARGET_TIME = '06:30'
    TIMEZONE = 'Australia/Sydney'
    
    # API Settings
    API_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 300  # 5 minutes
```

### Phase 2: Core Components Implementation

1. **Basic Logger**
```python
# src/core/logger.py
import logging
from datetime import datetime

class DigestLogger:
    def __init__(self):
        logging.basicConfig(
            filename='digest.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('digest')
        
    def log_operation(self, operation, status, details=None):
        self.logger.info(f"Operation: {operation} - Status: {status}")
        if details:
            self.logger.debug(f"Details: {details}")
```

2. **Scheduler**
```python
# src/core/scheduler.py
from datetime import datetime
import pytz
from .logger import DigestLogger

class DigestScheduler:
    def __init__(self, settings):
        self.settings = settings
        self.sydney_tz = pytz.timezone(settings.TIMEZONE)
        self.logger = DigestLogger()
        
    def should_run(self):
        now = datetime.now(self.sydney_tz)
        target = now.replace(
            hour=int(self.settings.TARGET_TIME.split(':')[0]),
            minute=int(self.settings.TARGET_TIME.split(':')[1])
        )
        return abs((now - target).total_seconds()) <= 300  # 5-minute window
```

3. **API Clients**
```python
# src/api/motion_client.py
import requests
from ..core.logger import DigestLogger

class MotionClient:
    def __init__(self, settings):
        self.settings = settings
        self.logger = DigestLogger()
        
    def get_calendar_data(self):
        for attempt in range(self.settings.MAX_RETRIES):
            try:
                response = requests.get(
                    'https://api.motion.com/calendar',
                    headers={'Authorization': f'Bearer {self.settings.MOTION_API_KEY}'},
                    timeout=self.settings.API_TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                self.logger.log_error('motion_api', str(e))
                if attempt < self.settings.MAX_RETRIES - 1:
                    time.sleep(self.settings.RETRY_DELAY)
                else:
                    raise
```

### Phase 3: Email System Implementation

1. **Email Template**
```html
<!-- src/email/templates/digest.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Digest</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 100%;">
        <tr>
            <td style="padding: 16px;">
                <!-- Content sections -->
            </td>
        </tr>
    </table>
</body>
</html>
```

2. **Email Sender**
```python
# src/email/sender.py
from ..core.logger import DigestLogger

class EmailSender:
    def __init__(self, settings):
        self.settings = settings
        self.logger = DigestLogger()
        
    def send_digest(self, content):
        for attempt in range(self.settings.MAX_RETRIES):
            try:
                # Implement email sending logic
                self.logger.log_operation('email', 'success')
                return True
            except Exception as e:
                self.logger.log_error('email', str(e))
                if attempt < self.settings.MAX_RETRIES - 1:
                    time.sleep(self.settings.RETRY_DELAY)
                else:
                    raise
```

### Phase 4: Main Application

```python
# src/digest/generator.py
from ..core.scheduler import DigestScheduler
from ..api.motion_client import MotionClient
from ..api.weather_client import WeatherClient
from ..email.sender import EmailSender
from ..core.logger import DigestLogger

class DigestGenerator:
    def __init__(self, settings):
        self.settings = settings
        self.scheduler = DigestScheduler(settings)
        self.motion_client = MotionClient(settings)
        self.weather_client = WeatherClient(settings)
        self.email_sender = EmailSender(settings)
        self.logger = DigestLogger()
        
    def run(self):
        if not self.scheduler.should_run():
            return
            
        try:
            # Generate digest
            calendar_data = self.motion_client.get_calendar_data()
            weather_data = self.weather_client.get_weather_data()
            
            # Format and send
            content = self._format_digest(calendar_data, weather_data)
            self.email_sender.send_digest(content)
            
        except Exception as e:
            self.logger.log_error('digest_generation', str(e))
            raise
```

### Implementation Steps:

1. **Setup Phase**
   - Create project structure
   - Set up virtual environment
   - Install dependencies
   - Configure environment variables

2. **Core Development**
   - Implement logger
   - Create scheduler
   - Develop API clients
   - Set up error handling

3. **Email System**
   - Create email template
   - Implement email sender
   - Add retry logic
   - Test delivery

4. **Integration**
   - Combine all components
   - Implement main application
   - Add monitoring
   - Test end-to-end

5. **Testing**
   - Unit tests
   - Integration tests
   - End-to-end tests
   - Error scenario testing

