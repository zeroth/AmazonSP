#!/usr/bin/env python3
"""
Local testing script for Amazon SP-API
Fetches marketplace information and stores in SQLite database
No AWS, Google Cloud, or email dependencies required
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from sp_api.api import Catalog, Orders
from sp_api.base import Marketplaces
from sp_api.base.credentials import Credentials

class LocalSPAPITester:
    def __init__(self, config_path='config/config_local.json'):
        """Initialize with local configuration"""
        self.config_path = Path(config_path)
        self.db_path = Path('data/amazon_sp_api.db')
        self.db_path.parent.mkdir(exist_ok=True)

        # Load configuration
        with open(self.config_path) as f:
            self.config = json.load(f)['sp_api']

        # Initialize credentials - AWS creds are optional
        cred_params = {
            'refresh_token': self.config['refresh_token'],
            'lwa_app_id': self.config['lwa_app_id'],
            'lwa_client_secret': self.config['lwa_client_secret']
        }

        # Only add AWS credentials if provided (for third-party apps)
        if self.config.get('aws_access_key') and self.config.get('aws_secret_key'):
            cred_params['aws_access_key'] = self.config['aws_access_key']
            cred_params['aws_secret_key'] = self.config['aws_secret_key']
            if self.config.get('role_arn'):
                cred_params['role_arn'] = self.config['role_arn']

        self.credentials = Credentials(**cred_params)

        # Get marketplace
        self.marketplace = Marketplaces[self.config.get('marketplace_id', 'US')]

        # Initialize database
        self.init_database()

    def init_database(self):
        """Create SQLite tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create marketplaces table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketplaces (
                id TEXT PRIMARY KEY,
                name TEXT,
                country_code TEXT,
                default_currency_code TEXT,
                default_language_code TEXT,
                domain_name TEXT,
                fetched_at TIMESTAMP
            )
        ''')

        # Create products table for catalog items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                asin TEXT PRIMARY KEY,
                title TEXT,
                brand TEXT,
                product_group TEXT,
                marketplace_id TEXT,
                fetched_at TIMESTAMP
            )
        ''')

        # Create orders table (simplified)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                purchase_date TEXT,
                order_status TEXT,
                order_total TEXT,
                currency_code TEXT,
                marketplace_id TEXT,
                fetched_at TIMESTAMP
            )
        ''')

        # Create api_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT,
                status TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        print(f"✓ Database initialized at: {self.db_path}")

    def log_api_call(self, endpoint, status, message=""):
        """Log API call to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO api_logs (endpoint, status, message) VALUES (?, ?, ?)",
            (endpoint, status, message)
        )
        conn.commit()
        conn.close()

    def fetch_marketplace_info(self):
        """Fetch and store marketplace information"""
        print("\n🔍 Fetching marketplace information...")

        try:
            # Store current marketplace info
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            marketplace_data = {
                'id': self.marketplace.marketplace_id,
                'name': self.marketplace.name,
                'country_code': self.marketplace.country_code,
                'default_currency_code': getattr(self.marketplace, 'currency', 'USD'),
                'default_language_code': getattr(self.marketplace, 'language', 'en_US'),
                'domain_name': getattr(self.marketplace, 'domain', 'amazon.com'),
                'fetched_at': datetime.now().isoformat()
            }

            cursor.execute('''
                INSERT OR REPLACE INTO marketplaces
                (id, name, country_code, default_currency_code, default_language_code, domain_name, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                marketplace_data['id'],
                marketplace_data['name'],
                marketplace_data['country_code'],
                marketplace_data['default_currency_code'],
                marketplace_data['default_language_code'],
                marketplace_data['domain_name'],
                marketplace_data['fetched_at']
            ))

            conn.commit()
            conn.close()

            print(f"✓ Stored marketplace: {marketplace_data['name']} ({marketplace_data['id']})")
            self.log_api_call("marketplaces", "success", f"Stored {marketplace_data['name']}")

            return marketplace_data

        except Exception as e:
            error_msg = f"Error fetching marketplace info: {str(e)}"
            print(f"✗ {error_msg}")
            self.log_api_call("marketplaces", "error", error_msg)
            return None

    def fetch_catalog_items(self, keywords="laptop", max_items=5):
        """Fetch sample catalog items"""
        print(f"\n🔍 Fetching catalog items for keyword: '{keywords}'...")

        try:
            catalog = Catalog(credentials=self.credentials, marketplace=self.marketplace)

            # Search for items
            response = catalog.search_catalog_items(
                keywords=keywords,
                includedData=['attributes', 'summaries']
            )

            if not response or not response.payload:
                print("No items found")
                return []

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            items_stored = 0
            items = response.payload.get('items', [])[:max_items]

            for item in items:
                asin = item.get('asin', '')
                attributes = item.get('attributes', {})
                title = attributes.get('item_name', [{}])[0].get('value', 'Unknown')
                brand = attributes.get('brand', [{}])[0].get('value', 'Unknown')
                product_group = attributes.get('product_group', [{}])[0].get('value', 'Unknown')

                cursor.execute('''
                    INSERT OR REPLACE INTO products
                    (asin, title, brand, product_group, marketplace_id, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    asin,
                    title[:200],  # Truncate long titles
                    brand,
                    product_group,
                    self.marketplace.marketplace_id,
                    datetime.now().isoformat()
                ))

                items_stored += 1
                print(f"  • {title[:50]}... (ASIN: {asin})")

            conn.commit()
            conn.close()

            print(f"✓ Stored {items_stored} catalog items")
            self.log_api_call("catalog", "success", f"Stored {items_stored} items")

            return items

        except Exception as e:
            error_msg = f"Error fetching catalog items: {str(e)}"
            print(f"✗ {error_msg}")
            self.log_api_call("catalog", "error", error_msg)
            return []

    def fetch_recent_orders(self, max_orders=5):
        """Fetch recent orders"""
        print(f"\n🔍 Fetching recent orders...")

        try:
            orders_api = Orders(credentials=self.credentials, marketplace=self.marketplace)

            # Get orders from last 7 days
            from datetime import timedelta
            created_after = (datetime.now() - timedelta(days=7)).isoformat()

            response = orders_api.get_orders(
                CreatedAfter=created_after,
                MaxResultsPerPage=max_orders
            )

            if not response or not response.payload:
                print("No orders found")
                return []

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            orders_stored = 0
            orders = response.payload.get('Orders', [])

            for order in orders:
                order_id = order.get('AmazonOrderId', '')
                purchase_date = order.get('PurchaseDate', '')
                order_status = order.get('OrderStatus', '')
                order_total = order.get('OrderTotal', {})

                cursor.execute('''
                    INSERT OR REPLACE INTO orders
                    (order_id, purchase_date, order_status, order_total, currency_code, marketplace_id, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_id,
                    purchase_date,
                    order_status,
                    order_total.get('Amount', '0'),
                    order_total.get('CurrencyCode', 'USD'),
                    self.marketplace.marketplace_id,
                    datetime.now().isoformat()
                ))

                orders_stored += 1
                print(f"  • Order {order_id} - Status: {order_status}")

            conn.commit()
            conn.close()

            print(f"✓ Stored {orders_stored} orders")
            self.log_api_call("orders", "success", f"Stored {orders_stored} orders")

            return orders

        except Exception as e:
            error_msg = f"Error fetching orders: {str(e)}"
            print(f"✗ {error_msg}")
            self.log_api_call("orders", "error", error_msg)
            return []

    def display_database_summary(self):
        """Display summary of data in database"""
        print("\n📊 Database Summary:")
        print("=" * 50)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count records in each table
        tables = ['marketplaces', 'products', 'orders', 'api_logs']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} records")

        # Show recent API logs
        print("\n📝 Recent API Calls:")
        cursor.execute("""
            SELECT endpoint, status, message, timestamp
            FROM api_logs
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        logs = cursor.fetchall()
        for log in logs:
            print(f"  [{log[3][:19]}] {log[0]}: {log[1]} - {log[2][:50]}")

        conn.close()
        print("=" * 50)

    def run_test(self):
        """Run the test sequence"""
        print("\n🚀 Starting Local SP-API Test")
        print("=" * 50)

        # Test 1: Marketplace info
        marketplace = self.fetch_marketplace_info()

        # Test 2: Catalog items (only if we have valid credentials)
        if marketplace:
            try:
                self.fetch_catalog_items(keywords="electronics", max_items=3)
            except Exception as e:
                print(f"⚠️  Catalog API not available: {e}")

        # Test 3: Recent orders (only if we have valid credentials)
        if marketplace:
            try:
                self.fetch_recent_orders(max_orders=3)
            except Exception as e:
                print(f"⚠️  Orders API not available: {e}")

        # Display summary
        self.display_database_summary()

        print(f"\n✅ Test completed! Data stored in: {self.db_path}")


def main():
    """Main entry point"""
    tester = LocalSPAPITester()
    tester.run_test()


if __name__ == "__main__":
    main()