# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Amazon SP-API data integration project that fetches data from Amazon Seller Partner API and stores it in Google Cloud BigTable and Google Sheets. The project can run as a standalone Python application or as an AWS Lambda function.

## Key Commands

### Local Development
```bash
# Install dependencies
pip install -r datatodb/requirements.txt

# Run the main application
python datatodb/main.py

# Deploy to AWS Lambda
python datatodb/scripts/deploy_lambda.py
```

### AWS Deployment
```bash
# Store configuration in AWS Parameter Store (required before deployment)
aws ssm put-parameter \
    --name "/amazon-sp-api/config" \
    --type "SecureString" \
    --value "$(cat datatodb/config/config.json)" \
    --overwrite

# Deploy Lambda function (requires AWS_REGION and AWS_ACCOUNT_ID env vars)
cd datatodb && python scripts/deploy_lambda.py
```

## Architecture

### Core Components

**Main Entry Points:**
- `datatodb/main.py`: Standalone Python application for local/server execution
- `datatodb/lambda_function.py`: AWS Lambda handler with Parameter Store configuration loading

**Data Managers (datatodb/models/):**
- `orders.py`: OrdersManager - Fetches and processes Amazon order data
- `finances.py`: FinancesManager - Fetches and processes financial events

**Integration Utilities (datatodb/utils/):**
- `sp_api_auth.py`: SPAPIAuth - Handles Amazon SP-API authentication
- `google_cloud_utils.py`: GoogleCloudUtils - Manages BigTable operations
- `sheets_utils.py`: GoogleSheetsUtils - Updates Google Sheets
- `notification_utils.py`: NotificationManager - Sends email notifications
- `logger.py`: Logger - Centralized logging with CloudWatch support in Lambda

### Data Flow

1. **Authentication**: SPAPIAuth handles credential management for Amazon SP-API
2. **Data Fetching**: OrdersManager and FinancesManager retrieve data from Amazon
3. **Storage**: Data is written to Google BigTable with structured row keys:
   - Orders: `order_{order_id}`
   - Finances: `finance_{uuid}`
4. **Visualization**: Data is also exported to Google Sheets with dated tabs
5. **Monitoring**: NotificationManager sends success/failure emails

### Configuration

Configuration is stored in `datatodb/config/config.json` and includes:
- Amazon SP-API credentials
- Google Cloud project settings
- Notification email settings

For Lambda deployment, configuration must be stored in AWS Parameter Store at `/amazon-sp-api/config`.

### Lambda Deployment

The deployment script (`scripts/deploy_lambda.py`) automates:
- Creating deployment package with dependencies
- Updating Lambda function code
- Setting up CloudWatch Events for scheduling (default: hourly)
- Configuring necessary permissions

Required IAM permissions for Lambda:
- AWSLambdaBasicExecutionRole
- Custom policy for Google Cloud access
- Custom policy for Amazon SP-API access
- Custom policy for Parameter Store access