# Local Testing Guide for Amazon SP-API

This guide explains how to test the Amazon SP-API integration locally without needing AWS, Google Cloud, or email services.

## Quick Start (No Credentials Required)

Test basic functionality without any credentials:

```bash
# Install minimal requirements
pip install sp-api-client

# Run minimal test (lists all marketplaces)
python datatodb/test_minimal.py
```

This will:
- List all available Amazon marketplaces
- Store them in a local SQLite database at `data/marketplaces.db`
- No API credentials required!

## Testing with SP-API Credentials

If you have SP-API credentials, you can test actual API calls:

### 1. Setup Configuration

Create or edit `datatodb/config/config_local.json`:

```json
{
    "sp_api": {
        "refresh_token": "Atzr|IwEBI...",
        "lwa_app_id": "amzn1.application-oa2-client.xxxxx",
        "lwa_client_secret": "your-client-secret",
        "marketplace_id": "US"
    }
}
```

**Note:** AWS IAM credentials (aws_access_key, aws_secret_key, role_arn) are NOT required if you're only accessing your own seller account data. They're only needed for third-party applications.

### 2. Run Tests

```bash
# Run minimal test with credentials
python datatodb/test_minimal.py

# Run full local test (fetches catalog items, orders)
python datatodb/test_local.py
```

## What Gets Tested

### Without Credentials (`test_minimal.py`):
- Lists all Amazon marketplaces
- Stores marketplace data in SQLite
- Verifies library installation

### With Credentials (`test_local.py`):
- Connects to Amazon SP-API
- Fetches marketplace information
- Retrieves catalog items (products)
- Gets recent orders (if available)
- Stores all data in local SQLite database

## Database Location

All test data is stored in SQLite databases:
- `data/marketplaces.db` - Marketplace information only
- `data/amazon_sp_api.db` - Full test data (products, orders, API logs)

## View Database Contents

You can inspect the SQLite database using:

```bash
# Using sqlite3 command line
sqlite3 data/amazon_sp_api.db

# In sqlite3 prompt:
.tables                    # List all tables
SELECT * FROM marketplaces; # View marketplace data
SELECT * FROM products;     # View product data
SELECT * FROM api_logs;     # View API call logs
.quit                      # Exit

# Or use a GUI tool like DB Browser for SQLite
```

## Marketplace IDs Reference

Common marketplace IDs for configuration:
- `US` - United States (ATVPDKIKX0DER)
- `CA` - Canada (A2EUQ1WTGCTBG2)
- `MX` - Mexico (A1AM78C64UM0Y8)
- `BR` - Brazil (A2Q3Y263D00KWC)
- `GB` - United Kingdom (A1F83G8C2ARO7P)
- `DE` - Germany (A1PA6795UKMFR9)
- `FR` - France (A13V1IB3VIYZZH)
- `ES` - Spain (A1RKKUPIHCS9HS)
- `IT` - Italy (APJ6JRA9NG5V4)
- `JP` - Japan (A1VC38T7YXB528)
- `AU` - Australia (A39IBJ37TRP1C6)
- `IN` - India (A21TJRUUN4KGV)

## Troubleshooting

### "No module named 'sp_api'"
```bash
pip install sp-api-client
```

### "Invalid refresh token"
- Ensure your refresh token is valid and not expired
- Check that LWA app ID and secret match your application
- Verify the marketplace ID matches your seller account region

### "Access denied" errors
- Your SP-API app may not have the required permissions
- Check your app's authorized data access in Seller Central

### SQLite database locked
- Close any other programs accessing the database
- Delete the `.db` file and run the test again

## Benefits of Local Testing

✅ **No Cloud Dependencies** - No AWS, GCP, or email setup required
✅ **Fast Iteration** - Test changes immediately without deployment
✅ **Cost-Free** - No cloud service charges during development
✅ **Easy Debugging** - Direct access to SQLite database for inspection
✅ **Safe Testing** - No risk of affecting production data

## Next Steps

Once local testing is successful:
1. Set up AWS credentials for Lambda deployment
2. Configure Google Cloud for BigTable storage
3. Set up email notifications
4. Deploy using `python scripts/deploy_lambda.py`