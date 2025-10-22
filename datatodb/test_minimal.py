#!/usr/bin/env python3
"""
Minimal test script for Amazon SP-API
Tests basic connectivity and stores marketplace info in SQLite
Requires only SP-API credentials, no cloud services
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

def test_marketplace_connection():
    """Test basic marketplace connection without any API calls"""
    from sp_api.base import Marketplaces

    print("\n🌍 Available Marketplaces:")
    print("=" * 50)

    # Create database
    db_path = Path('data/marketplaces.db')
    db_path.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marketplaces (
            marketplace_id TEXT PRIMARY KEY,
            name TEXT,
            country_code TEXT,
            region TEXT,
            endpoint TEXT,
            fetched_at TIMESTAMP
        )
    ''')

    # List all available marketplaces
    marketplaces_data = []
    for marketplace_name in dir(Marketplaces):
        if not marketplace_name.startswith('_'):
            try:
                marketplace = getattr(Marketplaces, marketplace_name)
                if hasattr(marketplace, 'marketplace_id'):
                    data = {
                        'marketplace_id': marketplace.marketplace_id,
                        'name': marketplace.name,
                        'country_code': marketplace.country_code,
                        'region': getattr(marketplace, 'region', 'Unknown'),
                        'endpoint': getattr(marketplace, 'endpoint', 'Unknown')
                    }
                    marketplaces_data.append(data)

                    # Store in database
                    cursor.execute('''
                        INSERT OR REPLACE INTO marketplaces
                        (marketplace_id, name, country_code, region, endpoint, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        data['marketplace_id'],
                        data['name'],
                        data['country_code'],
                        data['region'],
                        data['endpoint'],
                        datetime.now().isoformat()
                    ))

                    print(f"  • {data['name']} ({data['marketplace_id']}) - {data['country_code']}")
            except Exception:
                pass

    conn.commit()

    # Display summary
    print(f"\n✓ Stored {len(marketplaces_data)} marketplaces in {db_path}")

    # Query and display stored data
    print("\n📊 Database Contents:")
    cursor.execute("SELECT * FROM marketplaces ORDER BY name")
    rows = cursor.fetchall()
    print(f"  Total records: {len(rows)}")

    conn.close()


def test_with_credentials():
    """Test with actual credentials if available"""
    config_path = Path('config/config_local.json')

    if not config_path.exists():
        print("\n⚠️  No config file found. Creating template...")
        config_path.parent.mkdir(exist_ok=True)
        template = {
            "sp_api": {
                "refresh_token": "YOUR_REFRESH_TOKEN",
                "lwa_app_id": "YOUR_LWA_APP_ID",
                "lwa_client_secret": "YOUR_LWA_CLIENT_SECRET",
                "marketplace_id": "US"
            }
        }
        with open(config_path, 'w') as f:
            json.dump(template, f, indent=4)
        print(f"✓ Created template at: {config_path}")
        print("  Please add your credentials and run again.")
        return

    # Load config
    with open(config_path) as f:
        config = json.load(f)['sp_api']

    if config['refresh_token'] == 'YOUR_REFRESH_TOKEN':
        print("\n⚠️  Please update config_local.json with your actual credentials")
        return

    print("\n🔑 Credentials found, testing connection...")

    try:
        from sp_api.base.credentials import Credentials
        from sp_api.base import Marketplaces

        credentials = Credentials(
            refresh_token=config['refresh_token'],
            lwa_app_id=config['lwa_app_id'],
            lwa_client_secret=config['lwa_client_secret']
        )

        marketplace = Marketplaces[config.get('marketplace_id', 'US')]

        print(f"✓ Credentials loaded for marketplace: {marketplace.name}")

        # Try a simple API call
        try:
            from sp_api.api import Sellers
            sellers_api = Sellers(credentials=credentials, marketplace=marketplace)
            response = sellers_api.get_marketplace_participations()

            if response and response.payload:
                print("✓ API connection successful!")
                participations = response.payload
                print(f"  Found {len(participations)} marketplace participations")
            else:
                print("⚠️  API responded but no data returned")

        except Exception as api_error:
            print(f"⚠️  API call failed: {api_error}")
            print("  This might be due to permissions or incorrect credentials")

    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Main entry point"""
    print("\n🚀 Amazon SP-API Minimal Test")
    print("=" * 50)

    # Test 1: List all marketplaces (no credentials needed)
    test_marketplace_connection()

    # Test 2: Test with credentials if available
    test_with_credentials()

    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()