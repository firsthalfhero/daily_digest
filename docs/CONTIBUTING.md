# Contributing to Daily Digest Assistant

## 1. Development Setup

### 1.1 Prerequisites
```bash
# Required Tools
python==3.9
aws-cli==2.15.0
terraform==1.7.0
nodejs==18.x
npm==9.x
cdk==2.100.0

# Verify installations
python --version
aws --version
terraform --version
node --version
npm --version
cdk --version
```

### 1.2 Local Environment Setup
```bash
# 1. Clone the repository
git clone https://github.com/your-org/daily-digest.git
cd daily-digest

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Configure AWS credentials
aws configure
# Enter your AWS credentials when prompted
```

### 1.3 Environment Variables
```bash
# Create .env file from template
cp .env.example .env

# Required environment variables
MOTION_API_KEY=your_motion_api_key
WEATHER_API_KEY=your_weather_api_key
EMAIL_SERVICE_KEY=your_email_service_key
AWS_REGION=ap-southeast-2
ENVIRONMENT=development
```

## 2. Development Workflow

### 2.1 Branch Strategy
- `main`: Production-ready code
- `staging`: Pre-production testing
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes

### 2.2 Development Process
1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow coding standards
   - Write tests
   - Update documentation

3. **Run Tests**
   ```bash
   # Run all tests
   pytest

   # Run specific test file
   pytest tests/test_api.py

   # Run with coverage
   pytest --cov=src tests/
   ```

4. **Code Review**
   - Self-review using checklist
   - Create pull request
   - Address review comments

### 2.3 Testing Requirements
- Unit test coverage: minimum 80%
- Integration test coverage: minimum 70%
- All tests must pass before merge
- Include test documentation

## 3. Coding Standards

### 3.1 Python Style Guide
- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters
- Use black for formatting
- Use isort for imports

```python
# Example of proper formatting
from typing import Dict, List, Optional

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

def process_events(events: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """Process a list of events and return the result.

    Args:
        events: List of event dictionaries

    Returns:
        Processed event dictionary or None if processing fails
    """
    try:
        # Implementation
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing events: {str(e)}")
        return None
```

### 3.2 Documentation Standards
- Docstrings for all functions
- Type hints for all parameters
- Clear commit messages
- Updated README.md

### 3.3 Error Handling
```python
# Example of proper error handling
from typing import Optional

class DigestError(Exception):
    """Base exception for digest-related errors."""
    pass

class APIError(DigestError):
    """Exception for API-related errors."""
    pass

def fetch_calendar_data() -> Optional[Dict[str, Any]]:
    try:
        # Implementation
        return data
    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise APIError(f"Failed to fetch calendar data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise DigestError(f"Unexpected error: {str(e)}")
```

## 4. Pull Request Process

### 4.1 PR Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] All tests pass
- [ ] No security vulnerabilities
- [ ] PR description complete

### 4.2 PR Template
```markdown
## Description
[Describe your changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Security
- [ ] No sensitive data exposed
- [ ] No hardcoded credentials
- [ ] Security best practices followed

## Documentation
- [ ] README.md updated
- [ ] API documentation updated
- [ ] Code comments added/updated
```

## 5. Deployment Process

### 5.1 Staging Deployment
```bash
# Deploy to staging
./scripts/deploy.sh staging

# Verify deployment
aws lambda invoke --function-name digest-staging --payload '{}' response.json
```

### 5.2 Production Deployment
```bash
# Deploy to production
./scripts/deploy.sh production

# Verify deployment
aws lambda invoke --function-name digest-production --payload '{}' response.json
```

## 6. Monitoring and Debugging

### 6.1 Logging
```python
# Example of proper logging
from aws_lambda_powertools import Logger

logger = Logger()

def process_data(data: Dict[str, Any]) -> None:
    logger.info("Processing data", extra={"data_size": len(data)})
    try:
        # Implementation
        logger.info("Data processed successfully")
    except Exception as e:
        logger.error("Error processing data", exc_info=True)
        raise
```

### 6.2 Debugging
- Use CloudWatch Logs
- Check Lambda execution logs
- Monitor API responses
- Review error metrics

## 7. Security Guidelines

### 7.1 Code Security
- No hardcoded credentials
- Use AWS Secrets Manager
- Follow least privilege principle
- Regular security updates

### 7.2 API Security
- Validate all inputs
- Sanitize all outputs
- Use HTTPS only
- Implement rate limiting

## 8. Performance Guidelines

### 8.1 Code Performance
- Optimize Lambda cold starts
- Minimize API calls
- Use connection pooling
- Implement caching where appropriate

### 8.2 Resource Usage
- Monitor memory usage
- Track execution time
- Optimize package size
- Review CloudWatch metrics

## 9. Support

### 9.1 Getting Help
- Check documentation
- Review existing issues
- Contact team lead
- Join team chat

### 9.2 Reporting Issues
- Use issue template
- Include reproduction steps
- Add relevant logs
- Specify environment
