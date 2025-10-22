import boto3
import os
import shutil
import zipfile
import json

def create_deployment_package():
    """Create deployment package for Lambda"""
    # Create a temporary directory for deployment
    if os.path.exists('deployment'):
        shutil.rmtree('deployment')
    os.makedirs('deployment')
    
    # Copy required files
    files_to_copy = [
        'lambda_function.py',
        'utils/',
        'models/',
        'config/'
    ]
    
    for file in files_to_copy:
        if os.path.isdir(file):
            shutil.copytree(file, f'deployment/{file}')
        else:
            shutil.copy2(file, 'deployment/')
    
    # Install dependencies
    os.system('pip install -r requirements.txt -t deployment/')
    
    # Create ZIP file
    shutil.make_archive('deployment_package', 'zip', 'deployment')
    
    return 'deployment_package.zip'

def update_lambda(function_name, zip_file):
    """Update Lambda function code"""
    lambda_client = boto3.client('lambda')
    
    with open(zip_file, 'rb') as f:
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=f.read()
        )

def create_cloudwatch_rule(function_name, schedule):
    """Create or update CloudWatch Event Rule"""
    events_client = boto3.client('events')
    lambda_client = boto3.client('lambda')
    
    # Create rule
    rule_name = f"{function_name}-trigger"
    events_client.put_rule(
        Name=rule_name,
        ScheduleExpression=schedule,
        State='ENABLED'
    )
    
    # Add Lambda permission
    try:
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=f"{function_name}-EventBridge",
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=f"arn:aws:events:{os.environ['AWS_REGION']}:{os.environ['AWS_ACCOUNT_ID']}:rule/{rule_name}"
        )
    except lambda_client.exceptions.ResourceConflictException:
        # Permission already exists
        pass
    
    # Add target
    events_client.put_targets(
        Rule=rule_name,
        Targets=[
            {
                'Id': function_name,
                'Arn': f"arn:aws:lambda:{os.environ['AWS_REGION']}:{os.environ['AWS_ACCOUNT_ID']}:function:{function_name}"
            }
        ]
    )

def main():
    # Configuration
    function_name = 'amazon-sp-api-sync'
    schedule = 'rate(1 hour)'  # Run every hour
    
    # Create deployment package
    zip_file = create_deployment_package()
    
    # Update Lambda function
    update_lambda(function_name, zip_file)
    
    # Set up CloudWatch Event
    create_cloudwatch_rule(function_name, schedule)
    
    # Clean up
    os.remove(zip_file)
    shutil.rmtree('deployment')
    
    print(f"Deployment completed successfully. Function {function_name} will run {schedule}")

if __name__ == '__main__':
    main() 