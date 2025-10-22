import json
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from utils.sp_api_auth import SPAPIAuth
from utils.google_cloud_utils import GoogleCloudUtils
from utils.sheets_utils import GoogleSheetsUtils
from utils.notification_utils import NotificationManager
from models.orders import OrdersManager
from models.finances import FinancesManager
import uuid
from datetime import datetime

# Initialize logger
logger = Logger(service="amazon-sp-api-sync")

def load_config():
    """Load configuration from AWS Parameter Store"""
    try:
        # Get configuration from AWS Parameter Store
        config = parameters.get_parameter('/amazon-sp-api/config', transform='json')
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise

def process_data():
    """Main data processing function"""
    try:
        logger.info("Starting Amazon SP-API data fetch process")
        
        # Initialize all utilities
        sp_api_auth = SPAPIAuth()
        google_cloud = GoogleCloudUtils()
        sheets_utils = GoogleSheetsUtils()
        notification = NotificationManager()
        
        # Initialize managers
        orders_manager = OrdersManager(sp_api_auth)
        finances_manager = FinancesManager(sp_api_auth)
        
        # Create tables if they don't exist
        logger.info("Creating/verifying BigTable tables")
        orders_table = google_cloud.create_table('amazon_orders')
        finances_table = google_cloud.create_table('amazon_finances')
        
        # Fetch and process orders
        logger.info("Fetching orders data")
        orders = orders_manager.get_orders()
        for order in orders:
            row_key = f"order_{order['order_id']}"
            google_cloud.write_to_bigtable('amazon_orders', row_key, order)
        
        # Fetch and process financial events
        logger.info("Fetching financial data")
        financial_events = finances_manager.get_financial_events()
        for event in financial_events:
            row_key = f"finance_{uuid.uuid4().hex}"
            google_cloud.write_to_bigtable('amazon_finances', row_key, event)
        
        return {
            'orders_processed': len(orders),
            'financial_events_processed': len(financial_events)
        }
        
    except Exception as e:
        logger.error(f"Error in data processing: {str(e)}")
        raise

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    try:
        # Process the data
        results = process_data()
        
        # Send success notification
        notification = NotificationManager()
        notification.send_email(
            subject="Amazon SP-API Data Sync Completed",
            message=f"""
            Data sync completed successfully:
            - Orders processed: {results['orders_processed']}
            - Financial events processed: {results['financial_events_processed']}
            
            Data has been written to BigTable.
            """
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data sync completed successfully',
                'results': results
            })
        }
        
    except Exception as e:
        error_message = f"Error in Amazon SP-API sync: {str(e)}"
        logger.error(error_message)
        
        # Send error notification
        try:
            notification = NotificationManager()
            notification.send_email(
                subject="ERROR: Amazon SP-API Data Sync Failed",
                message=error_message
            )
        except Exception as notify_error:
            logger.error(f"Failed to send error notification: {str(notify_error)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_message
            })
        } 