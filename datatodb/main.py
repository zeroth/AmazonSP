from utils.sp_api_auth import SPAPIAuth
from utils.google_cloud_utils import GoogleCloudUtils
from utils.sheets_utils import GoogleSheetsUtils
from utils.notification_utils import NotificationManager
from utils.logger import Logger
from models.orders import OrdersManager
from models.finances import FinancesManager
import uuid
from datetime import datetime

def main():
    # Initialize logger
    logger = Logger('amazon_sp_api')
    
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
        
        # Fetch orders and write to BigTable
        logger.info("Fetching orders data")
        orders = orders_manager.get_orders()
        for order in orders:
            row_key = f"order_{order['order_id']}"
            google_cloud.write_to_bigtable('amazon_orders', row_key, order)
        
        # Fetch financial events and write to BigTable
        logger.info("Fetching financial data")
        financial_events = finances_manager.get_financial_events()
        for event in financial_events:
            row_key = f"finance_{uuid.uuid4().hex}"
            google_cloud.write_to_bigtable('amazon_finances', row_key, event)
        
        # Update Google Sheets
        logger.info("Updating Google Sheets")
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Update Orders sheet
        sheets_utils.create_or_update_sheet(
            google_cloud.config['spreadsheet_id'],
            orders,
            f'Orders_{today}'
        )
        
        # Update Finances sheet
        sheets_utils.create_or_update_sheet(
            google_cloud.config['spreadsheet_id'],
            financial_events,
            f'Finances_{today}'
        )
        
        # Send success notification
        notification.send_email(
            subject="Amazon SP-API Data Sync Completed",
            message=f"""
            Data sync completed successfully:
            - Orders processed: {len(orders)}
            - Financial events processed: {len(financial_events)}
            
            Data has been written to BigTable and Google Sheets.
            """
        )
        
        logger.info("Process completed successfully")
        
    except Exception as e:
        error_message = f"Error in Amazon SP-API sync: {str(e)}"
        logger.error(error_message)
        
        # Send error notification
        notification.send_email(
            subject="ERROR: Amazon SP-API Data Sync Failed",
            message=error_message
        )
        raise

if __name__ == "__main__":
    main() 