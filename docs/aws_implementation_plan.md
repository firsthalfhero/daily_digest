### 1. Infrastructure Setup Plan

#### A. Prerequisites
```bash
# Required tools
aws-cli/2.15.0
terraform/1.7.0
python/3.9
nodejs/18.x
npm/9.x
cdk/2.100.0
```

#### B. AWS Account Setup
```bash
# 1. Create IAM User for DevOps
aws iam create-user --user-name digest-devops
aws iam attach-user-policy --user-name digest-devops --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# 2. Create Access Key
aws iam create-access-key --user-name digest-devops

# 3. Configure AWS CLI
aws configure
# Enter the access key and secret
```

#### C. Project Structure
```
daily-digest/
├── .github/
│   └── workflows/
│       ├── deploy.yml
│       └── test.yml
├── infrastructure/
│   ├── cdk/
│   │   ├── app.py
│   │   ├── digest_stack.py
│   │   └── monitoring_stack.py
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── src/
│   └── [application code]
├── tests/
│   └── [test files]
├── scripts/
│   ├── deploy.sh
│   └── rollback.sh
└── README.md
```

### 2. Infrastructure as Code Implementation

#### A. CDK Stack Definition
```python
# infrastructure/cdk/digest_stack.py
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    Duration
)
from constructs import Construct

class DigestStack(Stack):
    def __init__(self, scope: Construct, id: str, env: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create Secrets
        motion_api_secret = secretsmanager.Secret(
            self, "MotionApiSecret",
            secret_name=f"/digest/{env}/motion-api-key"
        )
        
        weather_api_secret = secretsmanager.Secret(
            self, "WeatherApiSecret",
            secret_name=f"/digest/{env}/weather-api-key"
        )

        # Lambda Function
        digest_lambda = _lambda.Function(
            self, "DigestFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("src"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.minutes(5),
            memory_size=256,
            environment={
                "ENVIRONMENT": env,
                "TIMEZONE": "Australia/Sydney"
            }
        )

        # Grant Lambda access to secrets
        motion_api_secret.grant_read(digest_lambda)
        weather_api_secret.grant_read(digest_lambda)

        # EventBridge Rule
        rule = events.Rule(
            self, "DigestSchedule",
            schedule=events.Schedule.cron(
                minute="30",
                hour="6",
                timezone="Australia/Sydney"
            )
        )
        rule.add_target(targets.LambdaFunction(digest_lambda))
```

#### B. Monitoring Stack
```python
# infrastructure/cdk/monitoring_stack.py
from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_cloudwatch_actions as cloudwatch_actions
)

class MonitoringStack(Stack):
    def __init__(self, scope: Construct, id: str, env: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # SNS Topic for alerts
        alert_topic = sns.Topic(
            self, "DigestAlerts",
            topic_name=f"digest-{env}-alerts"
        )

        # CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self, "DigestDashboard",
            dashboard_name=f"digest-{env}-dashboard"
        )

        # Add Lambda metrics
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Invocations",
                left=[digest_lambda.metric_invocations()]
            ),
            cloudwatch.GraphWidget(
                title="Lambda Errors",
                left=[digest_lambda.metric_errors()]
            )
        )
```

### 3. CI/CD Pipeline Implementation

#### A. GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy Digest

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  AWS_REGION: ap-southeast-2
  CDK_DEFAULT_ACCOUNT: ${{ secrets.AWS_ACCOUNT_ID }}
  CDK_DEFAULT_REGION: ap-southeast-2

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          npm install -g aws-cdk
          
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
          
      - name: Run tests
        run: pytest tests/
        
      - name: Deploy to staging
        if: github.ref == 'refs/heads/main'
        run: |
          cdk deploy --require-approval never DigestStack-staging
          
      - name: Deploy to production
        if: github.ref == 'refs/heads/main' && github.event_name == 'workflow_dispatch'
        run: |
          cdk deploy --require-approval never DigestStack-prod
```

### 4. Deployment Scripts

#### A. Deployment Script
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=$1
VERSION=$(git rev-parse --short HEAD)

# Validate environment
if [[ ! $ENVIRONMENT =~ ^(staging|production)$ ]]; then
    echo "Invalid environment. Use 'staging' or 'production'"
    exit 1
fi

# Build and package Lambda
echo "Building Lambda package..."
pip install -r requirements.txt -t build/
cp src/* build/
cd build && zip -r ../deployment.zip . && cd ..

# Deploy infrastructure
echo "Deploying infrastructure..."
cdk deploy DigestStack-$ENVIRONMENT --require-approval never

# Update Lambda code
echo "Updating Lambda function..."
aws lambda update-function-code \
    --function-name digest-$ENVIRONMENT \
    --zip-file fileb://deployment.zip \
    --publish

# Tag deployment
aws lambda tag-resource \
    --resource arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:digest-$ENVIRONMENT \
    --tags "Version=$VERSION,Environment=$ENVIRONMENT"

echo "Deployment complete!"
```

#### B. Rollback Script
```bash
#!/bin/bash
# scripts/rollback.sh

set -e

ENVIRONMENT=$1
VERSION=$2

# Validate inputs
if [[ ! $ENVIRONMENT =~ ^(staging|production)$ ]]; then
    echo "Invalid environment. Use 'staging' or 'production'"
    exit 1
fi

if [[ -z $VERSION ]]; then
    echo "Version required"
    exit 1
fi

# Rollback Lambda
echo "Rolling back Lambda to version $VERSION..."
aws lambda update-function-code \
    --function-name digest-$ENVIRONMENT \
    --revision-id $VERSION

echo "Rollback complete!"
```

### 5. Monitoring and Alerting Setup

#### A. CloudWatch Alarms
```python
# infrastructure/cdk/monitoring_stack.py
# Add to MonitoringStack class

# Lambda Error Rate Alarm
error_alarm = cloudwatch.Alarm(
    self, "LambdaErrorAlarm",
    metric=digest_lambda.metric_errors(),
    threshold=1,
    evaluation_periods=1,
    alarm_description="Digest Lambda function errors",
    actions_enabled=True,
    alarm_actions=[alert_topic]
)

# Lambda Duration Alarm
duration_alarm = cloudwatch.Alarm(
    self, "LambdaDurationAlarm",
    metric=digest_lambda.metric_duration(),
    threshold=240000,  # 4 minutes
    evaluation_periods=1,
    alarm_description="Digest Lambda function duration exceeded",
    actions_enabled=True,
    alarm_actions=[alert_topic]
)
```

### 6. Operational Procedures

#### A. Deployment Process
1. **Staging Deployment**
   ```bash
   # Deploy to staging
   ./scripts/deploy.sh staging
   
   # Verify deployment
   aws lambda invoke --function-name digest-staging --payload '{}' response.json
   ```

2. **Production Deployment**
   ```bash
   # Deploy to production
   ./scripts/deploy.sh production
   
   # Verify deployment
   aws lambda invoke --function-name digest-production --payload '{}' response.json
   ```

#### B. Monitoring Process
1. **Daily Checks**
   - Review CloudWatch logs
   - Check Lambda execution metrics
   - Verify EventBridge rule triggers
   - Monitor error rates

2. **Weekly Checks**
   - Review CloudWatch dashboards
   - Check cost reports
   - Verify secret rotation
   - Review alert history

#### C. Incident Response
1. **Error Detection**
   - Monitor CloudWatch alarms
   - Check SNS notifications
   - Review Lambda logs

2. **Rollback Procedure**
   ```bash
   # Rollback to previous version
   ./scripts/rollback.sh production <version>
   ```

### 7. Security Considerations

1. **Secret Management**
   - Use AWS Secrets Manager for API keys
   - Rotate secrets regularly
   - Implement least privilege access

2. **Network Security**
   - Use VPC endpoints if needed
   - Implement security groups
   - Enable AWS WAF if required

3. **Compliance**
   - Enable CloudTrail logging
   - Implement AWS Config rules
   - Regular security audits

# Daily Digest Assistant - Architecture Document

## 1. System Overview
- Purpose: Deliver personalized morning briefings via email at 6:30 AM Sydney time
- Components: Motion API integration, Weather API integration, Email delivery
- Architecture: Serverless (AWS Lambda + EventBridge)

## 2. Technical Decisions
### 2.1 API Request Handling
- Sequential processing for simplicity
- Retry mechanism with exponential backoff
- Error handling with graceful degradation

### 2.2 Data Flow
- Motion API → Calendar Data Processing → Email Generation
- Weather API → Weather Data Processing → Email Generation
- Email Generation → Delivery → Monitoring

### 2.3 Hosting Solution
- AWS Lambda for compute
- EventBridge for scheduling
- DynamoDB for state management
- CloudWatch for monitoring

## 3. Security & Compliance
### 3.1 Credential Management
- AWS Secrets Manager for API keys
- Regular rotation schedule
- Least privilege access

### 3.2 Data Protection
- No PII storage
- Secure logging
- API key encryption

## 4. Monitoring & Operations
### 4.1 Key Metrics
- Lambda execution success/failure
- Email delivery status
- API response times
- Error rates

### 4.2 Alerting
- Lambda errors
- Delivery failures
- Schedule misses
- API timeouts

## 5. Disaster Recovery
### 5.1 Recovery Procedures
- Lambda function rollback
- API fallback procedures
- Email delivery retry logic

### 5.2 Backup Strategies
- State management in DynamoDB
- Log retention in CloudWatch
- Configuration versioning

## 6. Cost Management
### 6.1 Cost Structure
- Lambda execution costs
- EventBridge scheduling
- DynamoDB operations
- CloudWatch monitoring

### 6.2 Optimization
- Memory allocation
- Execution time limits
- Log retention policies

## 7. Future Considerations
### 7.1 Scalability
- Multi-user support (if needed)
- Additional data sources
- Enhanced monitoring

### 7.2 Maintenance
- Regular dependency updates
- Security patch management
- Performance optimization