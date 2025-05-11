### 1. Unit Testing Plan

#### A. Core Components
```python
# tests/core/test_logger.py
def test_log_operation():
    """Test basic operation logging"""
    logger = DigestLogger()
    logger.log_operation('test_op', 'success', {'detail': 'test'})
    # Verify log file contains entry

def test_log_error():
    """Test error logging with retry information"""
    logger = DigestLogger()
    logger.log_error('api_call', 'timeout', attempt=1)
    # Verify retry information in log

# tests/core/test_scheduler.py
def test_scheduler_timezone():
    """Test scheduler timezone handling"""
    scheduler = DigestScheduler(settings)
    # Verify correct Sydney timezone handling
    # Test DST transitions

def test_should_run():
    """Test scheduler run window"""
    scheduler = DigestScheduler(settings)
    # Test various times around 6:30 AM
    # Verify 5-minute window behavior
```

#### B. API Clients
```python
# tests/api/test_motion_client.py
def test_calendar_data_retrieval():
    """Test successful calendar data retrieval"""
    client = MotionClient(settings)
    with mock.patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = sample_calendar_data
        data = client.get_calendar_data()
        assert data == sample_calendar_data

def test_api_retry():
    """Test retry behavior on API failure"""
    client = MotionClient(settings)
    with mock.patch('requests.get') as mock_get:
        mock_get.side_effect = [
            requests.RequestException(),
            mock.Mock(json=lambda: sample_calendar_data)
        ]
        data = client.get_calendar_data()
        assert mock_get.call_count == 2

# tests/api/test_weather_client.py
def test_weather_data_retrieval():
    """Test weather data retrieval and formatting"""
    client = WeatherClient(settings)
    with mock.patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = sample_weather_data
        data = client.get_weather_data()
        assert data['temperature'] is not None
```

#### C. Email System
```python
# tests/email/test_template.py
def test_template_rendering():
    """Test email template rendering"""
    template = EmailTemplate()
    content = template.render({
        'calendar': sample_calendar_data,
        'weather': sample_weather_data
    })
    assert 'Daily Digest' in content
    assert 'mobile-friendly' in content

def test_template_mobile():
    """Test mobile responsiveness"""
    template = EmailTemplate()
    content = template.render(sample_data)
    # Verify mobile viewport meta tag
    # Verify responsive table structure

# tests/email/test_sender.py
def test_email_delivery():
    """Test successful email delivery"""
    sender = EmailSender(settings)
    with mock.patch('smtplib.SMTP') as mock_smtp:
        result = sender.send_digest(sample_content)
        assert result is True
        assert mock_smtp.called

def test_email_retry():
    """Test email retry on failure"""
    sender = EmailSender(settings)
    with mock.patch('smtplib.SMTP') as mock_smtp:
        mock_smtp.side_effect = [
            Exception('Connection failed'),
            mock.Mock()
        ]
        result = sender.send_digest(sample_content)
        assert result is True
        assert mock_smtp.call_count == 2
```

### 2. Integration Testing Plan

#### A. Component Integration
```python
# tests/integration/test_digest_generation.py
def test_full_digest_generation():
    """Test complete digest generation flow"""
    generator = DigestGenerator(settings)
    with mock.patch('MotionClient.get_calendar_data') as mock_calendar:
        with mock.patch('WeatherClient.get_weather_data') as mock_weather:
            with mock.patch('EmailSender.send_digest') as mock_send:
                mock_calendar.return_value = sample_calendar_data
                mock_weather.return_value = sample_weather_data
                mock_send.return_value = True
                
                generator.run()
                
                assert mock_calendar.called
                assert mock_weather.called
                assert mock_send.called

def test_partial_data_handling():
    """Test system behavior with partial data"""
    generator = DigestGenerator(settings)
    with mock.patch('MotionClient.get_calendar_data') as mock_calendar:
        with mock.patch('WeatherClient.get_weather_data') as mock_weather:
            mock_calendar.side_effect = Exception('API Error')
            mock_weather.return_value = sample_weather_data
            
            generator.run()
            # Verify graceful degradation
            # Verify error logging
```

### 3. End-to-End Testing Plan

#### A. Full System Tests
```python
# tests/e2e/test_system.py
def test_complete_digest_flow():
    """Test complete system from scheduling to delivery"""
    # Setup test environment
    test_settings = Settings(
        MOTION_API_KEY='test_key',
        WEATHER_API_KEY='test_key',
        EMAIL_SERVICE_KEY='test_key',
        TARGET_TIME='06:30',
        TIMEZONE='Australia/Sydney'
    )
    
    generator = DigestGenerator(test_settings)
    
    # Test scheduler
    assert generator.scheduler.should_run() is True
    
    # Test data collection
    calendar_data = generator.motion_client.get_calendar_data()
    weather_data = generator.weather_client.get_weather_data()
    
    # Test email generation and delivery
    content = generator._format_digest(calendar_data, weather_data)
    assert generator.email_sender.send_digest(content) is True

def test_error_recovery():
    """Test system recovery from various failures"""
    # Test API failures
    # Test email service failures
    # Test scheduling issues
    # Verify logging and monitoring
```

### 4. Test Data and Fixtures

```python
# tests/fixtures.py
sample_calendar_data = {
    'events': [
        {
            'title': 'Team Meeting',
            'start_time': '2024-03-20T09:00:00+10:00',
            'end_time': '2024-03-20T10:00:00+10:00'
        }
    ]
}

sample_weather_data = {
    'temperature': 22,
    'conditions': 'Sunny',
    'forecast': [
        {'time': '09:00', 'temp': 21, 'conditions': 'Sunny'},
        {'time': '12:00', 'temp': 23, 'conditions': 'Partly Cloudy'}
    ]
}

sample_email_content = {
    'subject': 'Daily Digest - March 20, 2024',
    'body': '...'
}
```

### 5. Test Execution Plan

1. **Local Development Testing**
   ```bash
   # Run all tests
   pytest tests/
   
   # Run specific test categories
   pytest tests/unit/
   pytest tests/integration/
   pytest tests/e2e/
   
   # Run with coverage
   pytest --cov=src tests/
   ```

2. **Continuous Integration**
   ```yaml
   # .github/workflows/test.yml
   name: Test
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Set up Python
           uses: actions/setup-python@v2
         - name: Install dependencies
           run: pip install -r requirements.txt
         - name: Run tests
           run: pytest --cov=src tests/
   ```

### 6. Test Monitoring and Reporting

1. **Test Coverage Requirements**
   - Core components: 90% coverage
   - API clients: 85% coverage
   - Email system: 85% coverage
   - Overall: 80% coverage

2. **Test Results Tracking**
   - Track test execution time
   - Monitor failure rates
   - Track coverage trends
   - Document known issues

