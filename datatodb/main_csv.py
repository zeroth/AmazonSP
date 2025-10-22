"""
Standalone script for fetching Amazon SP-API data and storing it in CSV files locally.

This script is similar to main.py but instead of storing data in Google BigTable and Sheets,
it saves the data to CSV files in a local directory.

Usage:
    python datatodb/main_csv.py [--output-dir DATA_DIR] [--days-back DAYS]

Arguments:
    --output-dir: Directory to store CSV files (default: 'data')
    --days-back: Number of days to look back for data (default: 30)
"""

from utils.sp_api_auth import SPAPIAuth
from utils.csv_utils import CSVUtils
from utils.logger import Logger
from models.orders import OrdersManager
from models.finances import FinancesManager
import argparse
from datetime import datetime


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Fetch Amazon SP-API data and save to CSV files'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Directory to store CSV files (default: data)'
    )
    parser.add_argument(
        '--days-back',
        type=int,
        default=30,
        help='Number of days to look back for data (default: 30)'
    )
    args = parser.parse_args()

    # Initialize logger
    logger = Logger('amazon_sp_api_csv')

    try:
        logger.info("Starting Amazon SP-API data fetch process (CSV mode)")
        logger.info(f"Output directory: {args.output_dir}")
        logger.info(f"Looking back {args.days_back} days")

        # Initialize utilities
        sp_api_auth = SPAPIAuth()
        csv_utils = CSVUtils(output_dir=args.output_dir)

        # Initialize managers
        orders_manager = OrdersManager(sp_api_auth)
        finances_manager = FinancesManager(sp_api_auth)

        # Fetch orders data
        logger.info("Fetching orders data")
        orders = orders_manager.get_orders(days_back=args.days_back)
        logger.info(f"Retrieved {len(orders)} orders")

        # Fetch financial events
        logger.info("Fetching financial data")
        financial_events = finances_manager.get_financial_events(days_back=args.days_back)
        logger.info(f"Retrieved {len(financial_events)} financial events")

        # Write data to CSV files
        logger.info("Writing data to CSV files")

        if orders:
            orders_file = csv_utils.write_to_csv(
                data=orders,
                filename='amazon_orders',
                flatten=True
            )
            logger.info(f"Orders written to: {orders_file}")
        else:
            logger.warning("No orders data to write")

        if financial_events:
            finances_file = csv_utils.write_to_csv(
                data=financial_events,
                filename='amazon_finances',
                flatten=True
            )
            logger.info(f"Financial events written to: {finances_file}")
        else:
            logger.warning("No financial events data to write")

        # Print summary
        print("\n" + "=" * 60)
        print("Amazon SP-API Data Fetch Summary")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Orders processed: {len(orders)}")
        print(f"Financial events processed: {len(financial_events)}")
        print(f"Output directory: {args.output_dir}")
        print("=" * 60 + "\n")

        logger.info("Process completed successfully")

    except Exception as e:
        error_message = f"Error in Amazon SP-API CSV sync: {str(e)}"
        logger.error(error_message)
        print(f"\nERROR: {error_message}\n")
        raise


if __name__ == "__main__":
    main()
