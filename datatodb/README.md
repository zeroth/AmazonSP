# Amazon SP-API Data Integration

A Python application to fetch data from Amazon Seller Partner API and store it in Google Cloud BigTable, Google Sheets, or local CSV files. Supports both standalone execution and AWS Lambda deployment.

## Features

- Fetch orders and financial events from Amazon SP-API
- Multiple storage options:
  - Google Cloud BigTable
  - Google Sheets
  - Local CSV files
- AWS Lambda deployment for scheduled execution
- Comprehensive error handling and notifications
- Support for Amazon India marketplace

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Getting Amazon SP-API Credentials](#getting-amazon-sp-api-credentials)
- [Configuration](#configuration)
- [Usage](#usage)
- [AWS Lambda Deployment](#aws-lambda-deployment)
- [Project Structure](#project-structure)

## Prerequisites

- Python 3.8 or higher
- Amazon Seller Central account
- (Optional) Google Cloud account for BigTable/Sheets integration
- (Optional) AWS account for Lambda deployment

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AmazonSP
```

2. Install dependencies:
```bash
pip install -r datatodb/requirements.txt
```

## Getting Amazon SP-API Credentials

To use this application, you need Amazon SP-API credentials. Follow these steps for Amazon India:

### Step 1: Register as Amazon Seller

1. Go to [Amazon Seller Central India](https://sellercentral.amazon.in/)
2. Sign up for a seller account (Individual or Professional)
3. Complete registration with required documents:
   - PAN Card
   - GST Registration (for Professional sellers)
   - Bank account details
   - Business address proof

### Step 2: Register as SP-API Developer

1. Log in to [Seller Central India](https://sellercentral.amazon.in/)
2. Navigate to **Settings** > **User Permissions**
3. Click on **Apps & Services** tab
4. Click **Develop apps** button
5. Accept the Amazon Marketplace Developer Agreement

### Step 3: Create a Developer Application

1. In Developer Central, click **Add new app client**
2. Fill in application details:
   - **Application Name**: e.g., "My SP-API Integration"
   - **OAuth Login URI**: `http://localhost:8000`
   - **OAuth Redirect URI**: `http://localhost:8000/callback`

   **Note**: These are for the OAuth authorization flow. You can either run a simple local server or extract the authorization code manually from the browser URL (see Step 4 for details).

3. Select required SP-API roles:
   - Orders (read orders data)
   - Finances (read financial events)
   - Reports (optional, for additional reports)
4. Click **Save and exit**
5. Save the credentials provided:
   - **LWA Client ID** (Login with Amazon Client Identifier)
   - **LWA Client Secret** (Login with Amazon Client Secret)

### Step 4: Generate Refresh Token

This is the most critical step. You need to get an authorization code and exchange it for a refresh token.

#### Option A: Manual Method (No Server Required - Recommended)

1. Create the authorization URL (replace `YOUR_CLIENT_ID`):
```
https://sellercentral.amazon.in/apps/authorize/consent?application_id=YOUR_CLIENT_ID&state=stateexample&version=beta&redirect_uri=http://localhost:8000/callback
```

2. Open this URL in your browser while logged into Seller Central
3. Click **Authorize** to grant permissions
4. You'll be redirected to: `http://localhost:8000/callback?spapi_oauth_code=...&state=...`
5. **Your browser will show "Unable to connect" or similar error - THIS IS EXPECTED!**
6. **Don't close the browser!** Copy the entire URL from the address bar
7. Extract the `spapi_oauth_code` value from the URL (everything between `spapi_oauth_code=` and `&state`)

Example URL:
```
http://localhost:8000/callback?spapi_oauth_code=ANaXRolbLSxT&state=stateexample
```
The code here is: `ANaXRolbLSxT`

8. Exchange the code for a refresh token **within 5 minutes**:

```python
import requests

# Replace with your actual values
LWA_CLIENT_ID = 'amzn1.application-oa2-client.xxxxx'
LWA_CLIENT_SECRET = 'your_secret_here'
SPAPI_OAUTH_CODE = 'the_code_you_copied'  # From step 7

response = requests.post(
    'https://api.amazon.in/auth/o2/token',
    data={
        'grant_type': 'authorization_code',
        'code': SPAPI_OAUTH_CODE,
        'client_id': LWA_CLIENT_ID,
        'client_secret': LWA_CLIENT_SECRET
    }
)

if response.status_code == 200:
    token_data = response.json()
    print("✓ Success!")
    print("\nRefresh Token:", token_data['refresh_token'])
    print("\nSave this refresh token in your config.json file!")
    print("This token doesn't expire and can be used indefinitely.")
else:
    print("✗ Error:", response.status_code)
    print(response.json())
```

#### Option B: Using Automated Helper Script (Recommended)

The easiest method! We provide a helper script that automates the entire process:

```bash
python datatodb/scripts/get_refresh_token.py
```

The script will:
1. Ask for your Client ID and Client Secret
2. Let you select your marketplace (India/US/UK)
3. Start a local server on port 8000
4. Open your browser to the authorization page
5. Automatically capture the authorization code
6. **Immediately exchange it for a refresh token** (happens in seconds - no need to worry about the 5-minute expiry!)
7. Display your refresh token and a sample config.json

Just follow the prompts and click "Authorize" when the browser opens!

**Important Notes**:
- **Manual method only**: The authorization code expires in 5 minutes, so you must exchange it quickly
- **Automated script**: Handles everything instantly - no timing concerns!
- The refresh token doesn't expire and can be reused indefinitely
- Save the refresh token securely in your config.json

### Step 5: Get AWS IAM Credentials (for API signing)

#### Why do I need AWS credentials?

This is a common question! Amazon SP-API uses **AWS Signature Version 4** to authenticate all API requests. Even though you're accessing your seller data (not AWS cloud services), every API call must be cryptographically signed with AWS credentials.

**Two-part authentication:**
- **LWA credentials** (Steps 3-4): Prove you're an authorized Amazon seller
- **AWS IAM credentials** (this step): Sign each API request with AWS security

Both are mandatory - the SP-API architecture requires it.

**Don't worry about costs**: You need an AWS account, but SP-API calls are FREE for sellers. You won't be charged for using these credentials with SP-API.

#### Steps to create AWS IAM credentials:

1. **Create AWS Account** (if you don't have one)
   - Go to [aws.amazon.com](https://aws.amazon.com)
   - Sign up (free account, credit card required but you won't be charged for SP-API)

2. **Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)**
   - Log in with your AWS account

3. **Create a new IAM user:**
   - Click **Users** → **Add users**
   - User name: `sp-api-user` (or any name you prefer)
   - Access type: Select **Programmatic access** ✓ (NOT AWS Console access)
   - Click **Next: Permissions**

4. **Create and attach policy:**
   - Click **Attach existing policies directly**
   - Click **Create policy** button (opens in new tab)
   - Click **JSON** tab
   - Paste this policy:

   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": "execute-api:Invoke",
               "Resource": "arn:aws:execute-api:*:*:*"
           }
       ]
   }
   ```

   - Click **Review policy**
   - Policy name: `SellingPartnerAPIPolicy`
   - Description: `Allows signing of Amazon SP-API requests`
   - Click **Create policy**

5. **Attach policy to user:**
   - Go back to the "Add user" tab
   - Click the refresh button next to "Create policy"
   - Search for `SellingPartnerAPIPolicy`
   - Check the box next to it
   - Click **Next: Tags** (skip tags)
   - Click **Next: Review**
   - Click **Create user**

6. **Save your credentials** (IMPORTANT!):
   - You'll see your credentials on the success screen
   - **Access Key ID**: (e.g., `AKIAIOSFODNN7EXAMPLE`)
   - **Secret Access Key**: Click "Show" to reveal it

   **⚠️ CRITICAL**: This is the ONLY time you'll see the Secret Access Key!
   - Download the CSV file OR copy both values immediately
   - Store them securely - you'll need them for config.json

#### What these credentials do:

- They're used to cryptographically sign API requests to Amazon
- They prove the request is coming from an authorized source
- They're NOT used for billing (SP-API is free for sellers)
- They only have permission to call API endpoints, nothing else in AWS

### Step 6: Important Details for Amazon India

- **Marketplace ID**: `A21TJRUUN4KGV`
- **Region**: `eu-west-1` (India uses EU endpoint)
- **Endpoint**: `https://sellingpartnerapi-eu.amazon.com`

### Useful Links

- [SP-API Documentation](https://developer-docs.amazon.com/sp-api/)
- [Seller Central India](https://sellercentral.amazon.in/)
- [SP-API Developer Guide](https://developer-docs.amazon.com/sp-api/docs/what-is-the-selling-partner-api)
- [SP-API Authorization](https://developer-docs.amazon.com/sp-api/docs/authorizing-selling-partner-api-applications)

## Configuration

Create a configuration file at `datatodb/config/config.json`:

```json
{
  "amazon_sp_api": {
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "lwa_client_id": "YOUR_LWA_CLIENT_ID",
    "lwa_client_secret": "YOUR_LWA_CLIENT_SECRET",
    "aws_access_key": "YOUR_AWS_ACCESS_KEY",
    "aws_secret_key": "YOUR_AWS_SECRET_KEY",
    "role_arn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_ROLE",
    "marketplace_id": "A21TJRUUN4KGV",
    "region": "eu-west-1",
    "endpoint": "https://sellingpartnerapi-eu.amazon.com"
  },
  "google_cloud": {
    "project_id": "your-gcp-project-id",
    "instance_id": "your-bigtable-instance",
    "spreadsheet_id": "your-google-sheet-id"
  },
  "notifications": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "recipient_email": "recipient@example.com"
  }
}
```

**Note**: Google Cloud and notifications sections are optional if using CSV export mode.

## Usage

### Option 1: CSV Export (Recommended for Getting Started)

Export data to local CSV files without needing cloud services:

```bash
# Basic usage - saves to 'data' directory
python datatodb/main_csv.py

# Custom output directory
python datatodb/main_csv.py --output-dir exports

# Fetch data from last 60 days
python datatodb/main_csv.py --days-back 60

# Combine options
python datatodb/main_csv.py --output-dir /path/to/exports --days-back 7
```

**Output files:**
- `amazon_orders_YYYYMMDD_HHMMSS.csv`
- `amazon_finances_YYYYMMDD_HHMMSS.csv`

**Features:**
- No cloud dependencies required
- Automatic nested data flattening
- Timestamped filenames to prevent overwrites
- Console summary of fetched records

### Option 2: Cloud Storage (BigTable + Google Sheets)

Store data in Google Cloud services:

```bash
python datatodb/main.py
```

**Requirements:**
- Google Cloud project with BigTable enabled
- Service account credentials
- Google Sheets API enabled

**Features:**
- Persistent storage in BigTable
- Automatic Google Sheets updates with dated tabs
- Email notifications on success/failure

### Option 3: AWS Lambda (Scheduled Execution)

Deploy as a Lambda function for automated scheduled runs:

See [AWS Lambda Deployment](#aws-lambda-deployment) section below.

## AWS Lambda Deployment

Deploy the application to AWS Lambda for scheduled, automated execution.

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. IAM role for Lambda with these permissions:
   - `AWSLambdaBasicExecutionRole` (managed policy)
   - Custom policy for Google Cloud access
   - Custom policy for Amazon SP-API access
   - Custom policy for Parameter Store access

### Deployment Steps

1. Store configuration in AWS Parameter Store:

```bash
aws ssm put-parameter \
    --name "/amazon-sp-api/config" \
    --type "SecureString" \
    --value "$(cat datatodb/config/config.json)" \
    --overwrite
```

2. Set environment variables:

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
```

3. Deploy the Lambda function:

```bash
cd datatodb
python scripts/deploy_lambda.py
```

### Lambda Function Behavior

The deployed Lambda function will:
1. Run on the specified schedule (default: every hour)
2. Fetch data from Amazon SP-API
3. Update Google BigTable and Sheets
4. Send email notifications on success/failure
5. Log all activities to CloudWatch Logs

### Key Features

- Secure configuration management using Parameter Store
- Comprehensive error handling
- CloudWatch logging and monitoring
- Automatic scheduling via CloudWatch Events
- Easy deployment and updates

## Project Structure

```
datatodb/
├── main.py                    # Main application (BigTable/Sheets)
├── main_csv.py               # CSV export application
├── lambda_function.py        # AWS Lambda handler
├── config/
│   └── config.json          # Configuration file
├── models/
│   ├── orders.py            # Orders data manager
│   └── finances.py          # Financial events manager
├── utils/
│   ├── sp_api_auth.py       # SP-API authentication
│   ├── google_cloud_utils.py # BigTable operations
│   ├── sheets_utils.py      # Google Sheets integration
│   ├── csv_utils.py         # CSV file operations
│   ├── notification_utils.py # Email notifications
│   └── logger.py            # Logging utility
├── scripts/
│   └── deploy_lambda.py     # Lambda deployment script
└── requirements.txt         # Python dependencies
```

## Data Schema

### Orders Data

- `order_id`: Amazon order identifier
- `purchase_date`: Order purchase timestamp
- `order_status`: Current order status
- `order_total`: Total order amount
- `shipping_address`: Delivery address details

### Financial Events Data

- `event_type`: Type of financial event
- `posted_date`: Event posting timestamp
- `amount`: Transaction amount
- `currency`: Currency code

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify all credentials in config.json
   - Check refresh token hasn't expired
   - Ensure IAM user has correct permissions

2. **No Data Retrieved**
   - Check date range (default: 30 days)
   - Verify you have orders/transactions in the period
   - Check marketplace ID matches your region

3. **CSV File Errors**
   - Ensure output directory has write permissions
   - Check disk space availability

4. **Lambda Deployment Issues**
   - Verify AWS credentials are configured
   - Check IAM role has necessary permissions
   - Ensure Parameter Store has configuration

## License

This project is for educational and personal use. Ensure compliance with Amazon's SP-API terms of service.

## Support

For issues or questions:
- Check [SP-API Documentation](https://developer-docs.amazon.com/sp-api/)
- Review [Seller Central Help](https://sellercentral.amazon.in/help/hub)
