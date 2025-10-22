To deploy the Lambda function:
1. First, ensure you have the AWS CLI configured with appropriate credentials.
2. Create an IAM role for the Lambda function with these permissions:
    - AWSLambdaBasicExecutionRole
    - Custom policy for Google Cloud access
    - Custom policy for Amazon SP-API access
    - Custom policy for Parameter Store access
3. Store the configuration in AWS Parameter Store:

```
aws ssm put-parameter \
    --name "/amazon-sp-api/config" \
    --type "SecureString" \
    --value "$(cat config/config.json)" \
    --overwrite
```
4. Deploy the Lambda function:
```
python scripts/deploy_lambda.py
```


The Lambda function will:
1. Run on the specified schedule (default: every hour)
2. Fetch data from Amazon SP-API
3. Update Google BigTable
4. Send notifications about success/failure
5. Log all activities to CloudWatch Logs

Key features of this Lambda setup:
1. Secure configuration management using Parameter Store
2. Error handling and notifications
3. CloudWatch logging
4. Automatic scheduling
5. Easy deployment process

