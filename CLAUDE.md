# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Amazon SP-API data integration project that fetches data from Amazon Seller Partner API and stores it in Google Cloud BigTable and Google Sheets. The project can run as a standalone Python application or as an AWS Lambda function.

## Key Commands

### Local Development
```bash
# Install dependencies
pip install -r datatodb/requirements.txt

# Run the main application (stores data in BigTable and Google Sheets)
python datatodb/main.py

# Run CSV export mode (stores data locally in CSV files)
python datatodb/main_csv.py

# CSV export with custom options
python datatodb/main_csv.py --output-dir exports --days-back 60

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
- `datatodb/main.py`: Standalone Python application for local/server execution (stores in BigTable/Sheets)
- `datatodb/main_csv.py`: Standalone Python application for CSV export (stores locally)
- `datatodb/lambda_function.py`: AWS Lambda handler with Parameter Store configuration loading

**Data Managers (datatodb/models/):**
- `orders.py`: OrdersManager - Fetches and processes Amazon order data
- `finances.py`: FinancesManager - Fetches and processes financial events

**Integration Utilities (datatodb/utils/):**
- `sp_api_auth.py`: SPAPIAuth - Handles Amazon SP-API authentication
- `google_cloud_utils.py`: GoogleCloudUtils - Manages BigTable operations
- `sheets_utils.py`: GoogleSheetsUtils - Updates Google Sheets
- `csv_utils.py`: CSVUtils - Writes data to local CSV files with flattening support
- `notification_utils.py`: NotificationManager - Sends email notifications
- `logger.py`: Logger - Centralized logging with CloudWatch support in Lambda

### Data Flow

**Standard Mode (main.py):**
1. **Authentication**: SPAPIAuth handles credential management for Amazon SP-API
2. **Data Fetching**: OrdersManager and FinancesManager retrieve data from Amazon
3. **Storage**: Data is written to Google BigTable with structured row keys:
   - Orders: `order_{order_id}`
   - Finances: `finance_{uuid}`
4. **Visualization**: Data is also exported to Google Sheets with dated tabs
5. **Monitoring**: NotificationManager sends success/failure emails

**CSV Mode (main_csv.py):**
1. **Authentication**: SPAPIAuth handles credential management for Amazon SP-API
2. **Data Fetching**: OrdersManager and FinancesManager retrieve data from Amazon
3. **Local Storage**: Data is written to timestamped CSV files:
   - Orders: `amazon_orders_YYYYMMDD_HHMMSS.csv`
   - Finances: `amazon_finances_YYYYMMDD_HHMMSS.csv`
4. **Features**: Automatic nested dictionary flattening, configurable output directory, console summary

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

## Getting Amazon SP-API Credentials (India)

To use this project, you need to register as an Amazon Seller and obtain SP-API credentials. Here's the process for Amazon India:

### Step 1: Register as Amazon Seller
1. Go to [Amazon Seller Central India](https://sellercentral.amazon.in/)
2. Sign up for a seller account (Individual or Professional)
3. Complete the registration process with required documents (PAN, GST, Bank details)

### Step 2: Register as SP-API Developer
1. Log in to [Seller Central India](https://sellercentral.amazon.in/)
2. Navigate to **Settings** > **User Permissions**
3. Click on **Apps & Services** tab
4. Click **Develop apps** button
5. Accept the Amazon Marketplace Developer Agreement

### Step 3: Create a Developer Application
1. In the Developer Central, click **Add new app client**
2. Fill in the application details:
   - **Application Name**: Your application name (e.g., "My SP-API Integration")
   - **OAuth Login URI**: `http://localhost:8000` (for local development)
   - **OAuth Redirect URI**: `http://localhost:8000/callback` (for local development)

   **Note**: These URIs are used during the authorization process. You can use a simple local server or just extract the code from the browser URL manually (see Step 4).

3. Select the **SP-API** roles your app needs:
   - Check required permissions (e.g., Orders, Finances, Reports)
4. Click **Save and exit**
5. You'll receive:
   - **LWA Client ID** (Login with Amazon Client Identifier)
   - **LWA Client Secret** (Login with Amazon Client Secret)

### Step 4: Generate Refresh Token

**Option A: Manual Method (Easiest - No Server Required)**

1. Create the authorization URL (replace `YOUR_CLIENT_ID` and `YOUR_REDIRECT_URI`):
```
https://sellercentral.amazon.in/apps/authorize/consent?application_id=YOUR_CLIENT_ID&state=stateexample&version=beta&redirect_uri=http://localhost:8000/callback
```

2. Open this URL in browser while logged into Seller Central
3. Authorize the application
4. You'll be redirected to `http://localhost:8000/callback?spapi_oauth_code=...&state=...`
5. **The browser will show an error (server not found) - this is expected!**
6. **Copy the full URL from the browser address bar** - you need the `spapi_oauth_code` parameter
7. Extract the `spapi_oauth_code` value from the URL
8. Run the provided helper script or use the code below to exchange it for a refresh token

**Option B: Using Helper Script (Automated - Recommended)**

Use the provided helper script that runs a temporary local server and handles everything automatically:
```bash
python datatodb/scripts/get_refresh_token.py
```

This script will:
- Start a local server on port 8000
- Open your browser to the authorization page
- Automatically capture the authorization code
- Immediately exchange it for a refresh token (no 5-minute expiry worry!)
- Display your refresh token and sample config

**Manual Token Exchange:**

If doing manually, exchange the authorization code for a refresh token within 5 minutes:

```python
import requests

# Replace with your actual values
LWA_CLIENT_ID = 'your_lwa_client_id'
LWA_CLIENT_SECRET = 'your_lwa_client_secret'
SPAPI_OAUTH_CODE = 'the_code_from_url'  # From step 7 above

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
    print("Refresh Token:", response.json()['refresh_token'])
    print("\nSave this refresh token in your config.json file!")
else:
    print("Error:", response.json())
```

**Important**: The `spapi_oauth_code` expires in 5 minutes, so exchange it quickly!

### Step 5: Get AWS IAM User Credentials (for API Request Signing)

**Why do I need AWS credentials for selling on Amazon?**

Amazon SP-API uses AWS Signature Version 4 to sign all API requests. This is a security requirement by Amazon - every API call must be cryptographically signed using AWS credentials, even though you're accessing seller data (not AWS services).

Think of it as two-factor authentication:
- **LWA credentials** (from Step 3-4): Prove you're an authorized seller
- **AWS IAM credentials** (this step): Sign/authenticate each API request

Both are mandatory - SP-API won't work without AWS credentials.

**Steps to get AWS IAM credentials:**

1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
   - If you don't have an AWS account, create one (it's free - you won't be charged for SP-API calls)

2. Create a new IAM user:
   - Click **Users** → **Add users**
   - User name: e.g., "sp-api-user"
   - Access type: Select **Programmatic access** (NOT console access)
   - Click **Next: Permissions**

3. Attach permissions policy:
   - Click **Attach existing policies directly**
   - Click **Create policy** (opens new tab)
   - Select **JSON** tab and paste:

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
   - Name: "SellingPartnerAPIPolicy"
   - Click **Create policy**
   - Go back to the user creation tab, refresh policies, and select "SellingPartnerAPIPolicy"

4. Complete user creation and **save the credentials**:
   - **Access Key ID** (e.g., AKIAIOSFODNN7EXAMPLE)
   - **Secret Access Key** (e.g., wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY)

   **Important**: This is the ONLY time you'll see the Secret Access Key - save it securely!

**Note**: These AWS credentials are only used to sign API requests. You won't be charged for SP-API usage (it's free for sellers).

### Step 6: Configure the Application
Add all credentials to `datatodb/config/config.json`:

```json
{
  "amazon_sp_api": {
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "lwa_client_id": "YOUR_LWA_CLIENT_ID",
    "lwa_client_secret": "YOUR_LWA_CLIENT_SECRET",
    "aws_access_key": "YOUR_AWS_ACCESS_KEY",
    "aws_secret_key": "YOUR_AWS_SECRET_KEY",
    "role_arn": "arn:aws:iam::YOUR_ACCOUNT:role/YOUR_ROLE",
    "marketplace_id": "A21TJRUUN4KGV",
    "region": "eu-west-1",
    "endpoint": "https://sellingpartnerapi-eu.amazon.com"
  }
}
```

**Important Notes for Amazon India:**
- **Marketplace ID**: `A21TJRUUN4KGV` (for Amazon.in)
- **Region**: `eu-west-1` (India sellers use EU endpoint)
- **Endpoint**: `https://sellingpartnerapi-eu.amazon.com`

### Useful Links
- [SP-API Documentation](https://developer-docs.amazon.com/sp-api/)
- [Seller Central India](https://sellercentral.amazon.in/)
- [SP-API Developer Guide](https://developer-docs.amazon.com/sp-api/docs/what-is-the-selling-partner-api)