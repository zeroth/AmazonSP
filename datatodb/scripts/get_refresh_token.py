#!/usr/bin/env python3
"""
Helper script to obtain Amazon SP-API refresh token.

This script simplifies the OAuth flow by:
1. Running a temporary local server to capture the authorization code
2. Opening the authorization URL in the browser
3. Automatically exchanging the code for a refresh token

Usage:
    python scripts/get_refresh_token.py
"""

import requests
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import sys


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler to capture OAuth callback."""

    authorization_code = None

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_GET(self):
        """Handle GET request with OAuth callback."""
        # Parse the query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        if 'spapi_oauth_code' in query_params:
            # Store the authorization code
            OAuthCallbackHandler.authorization_code = query_params['spapi_oauth_code'][0]

            # Send success response to browser
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            success_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authorization Successful</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 500px;
                    }
                    h1 {
                        color: #2ecc71;
                        margin-top: 0;
                    }
                    .checkmark {
                        width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        background: #2ecc71;
                        color: white;
                        font-size: 50px;
                        line-height: 80px;
                        margin: 0 auto 20px;
                    }
                    p {
                        color: #666;
                        line-height: 1.6;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="checkmark">✓</div>
                    <h1>Authorization Successful!</h1>
                    <p>The authorization code has been captured successfully.</p>
                    <p>You can close this window and return to the terminal.</p>
                    <p style="margin-top: 30px; font-size: 12px; color: #999;">
                        The script is now exchanging the code for your refresh token...
                    </p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
        else:
            # Handle error case
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            error_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authorization Failed</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 500px;
                    }
                    h1 {
                        color: #e74c3c;
                        margin-top: 0;
                    }
                    .error-icon {
                        width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        background: #e74c3c;
                        color: white;
                        font-size: 50px;
                        line-height: 80px;
                        margin: 0 auto 20px;
                    }
                    p {
                        color: #666;
                        line-height: 1.6;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error-icon">✗</div>
                    <h1>Authorization Failed</h1>
                    <p>No authorization code received.</p>
                    <p>Please try again or use the manual method.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())


def get_refresh_token(lwa_client_id, lwa_client_secret, marketplace='india'):
    """
    Get refresh token through OAuth flow.

    Args:
        lwa_client_id: Login with Amazon Client ID
        lwa_client_secret: Login with Amazon Client Secret
        marketplace: Marketplace region (default: 'india')

    Returns:
        Refresh token string or None if failed
    """
    # Marketplace configurations
    marketplace_config = {
        'india': {
            'auth_url': 'https://sellercentral.amazon.in/apps/authorize/consent',
            'token_url': 'https://api.amazon.in/auth/o2/token'
        },
        'us': {
            'auth_url': 'https://sellercentral.amazon.com/apps/authorize/consent',
            'token_url': 'https://api.amazon.com/auth/o2/token'
        },
        'uk': {
            'auth_url': 'https://sellercentral.amazon.co.uk/apps/authorize/consent',
            'token_url': 'https://api.amazon.co.uk/auth/o2/token'
        }
    }

    config = marketplace_config.get(marketplace.lower())
    if not config:
        print(f"Error: Unknown marketplace '{marketplace}'")
        print(f"Available: {', '.join(marketplace_config.keys())}")
        return None

    # Server configuration
    redirect_uri = 'http://localhost:8000/callback'
    port = 8000

    # Build authorization URL
    auth_url = (
        f"{config['auth_url']}?"
        f"application_id={lwa_client_id}&"
        f"state=stateexample&"
        f"version=beta&"
        f"redirect_uri={redirect_uri}"
    )

    print("\n" + "="*70)
    print("Amazon SP-API Refresh Token Generator")
    print("="*70)
    print("\nStep 1: Starting local server on port 8000...")

    # Start local server
    server = HTTPServer(('localhost', port), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.daemon = True
    server_thread.start()

    print("✓ Server started successfully")
    print("\nStep 2: Opening authorization URL in your browser...")
    print(f"\nIf the browser doesn't open automatically, visit this URL:")
    print(f"\n{auth_url}\n")

    # Open browser
    webbrowser.open(auth_url)

    print("Step 3: Please authorize the application in your browser...")
    print("Waiting for authorization...\n")

    # Wait for the server to receive the callback
    server_thread.join(timeout=300)  # 5 minute timeout

    if not OAuthCallbackHandler.authorization_code:
        print("\n✗ Error: No authorization code received")
        print("The authorization may have timed out or been cancelled.")
        print("\nTry the manual method instead:")
        print("1. Visit the URL above")
        print("2. Copy the 'spapi_oauth_code' from the redirect URL")
        print("3. Use the manual exchange script")
        return None

    print("✓ Authorization code received!")
    print("\nStep 4: Exchanging code for refresh token...")

    # Exchange authorization code for refresh token
    try:
        response = requests.post(
            config['token_url'],
            data={
                'grant_type': 'authorization_code',
                'code': OAuthCallbackHandler.authorization_code,
                'client_id': lwa_client_id,
                'client_secret': lwa_client_secret
            },
            timeout=10
        )

        if response.status_code == 200:
            token_data = response.json()
            refresh_token = token_data.get('refresh_token')

            print("\n" + "="*70)
            print("✓ SUCCESS! Refresh Token Generated")
            print("="*70)
            print(f"\nRefresh Token:\n{refresh_token}")
            print("\n" + "="*70)
            print("\nIMPORTANT:")
            print("1. Save this refresh token in your config.json file")
            print("2. This token does not expire and can be used indefinitely")
            print("3. Keep it secure - treat it like a password")
            print("="*70 + "\n")

            return refresh_token
        else:
            print(f"\n✗ Error: Failed to get refresh token (Status: {response.status_code})")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"\n✗ Error exchanging code: {str(e)}")
        return None
    finally:
        server.shutdown()


def main():
    """Main function."""
    print("\n" + "="*70)
    print("Amazon SP-API Refresh Token Generator")
    print("="*70)
    print("\nThis script will help you obtain a refresh token for Amazon SP-API.")
    print("You'll need your LWA Client ID and Client Secret from Seller Central.")
    print("\nPrerequisites:")
    print("1. Registered as Amazon Seller")
    print("2. Created a developer application in Seller Central")
    print("3. Have your LWA Client ID and Client Secret")
    print("="*70)

    # Get user inputs
    print("\nPlease enter your credentials:")
    lwa_client_id = input("\nLWA Client ID: ").strip()
    lwa_client_secret = input("LWA Client Secret: ").strip()

    if not lwa_client_id or not lwa_client_secret:
        print("\n✗ Error: Both Client ID and Client Secret are required")
        sys.exit(1)

    # Select marketplace
    print("\nSelect your marketplace:")
    print("1. India (amazon.in)")
    print("2. United States (amazon.com)")
    print("3. United Kingdom (amazon.co.uk)")

    marketplace_choice = input("\nEnter choice (1-3) [default: 1]: ").strip() or '1'

    marketplace_map = {
        '1': 'india',
        '2': 'us',
        '3': 'uk'
    }

    marketplace = marketplace_map.get(marketplace_choice, 'india')

    # Get refresh token
    refresh_token = get_refresh_token(lwa_client_id, lwa_client_secret, marketplace)

    if refresh_token:
        # Offer to save to config file
        save_choice = input("\nWould you like to see a sample config.json? (y/n): ").strip().lower()

        if save_choice == 'y':
            sample_config = f"""
{{
  "amazon_sp_api": {{
    "refresh_token": "{refresh_token}",
    "lwa_client_id": "{lwa_client_id}",
    "lwa_client_secret": "{lwa_client_secret}",
    "aws_access_key": "YOUR_AWS_ACCESS_KEY",
    "aws_secret_key": "YOUR_AWS_SECRET_KEY",
    "role_arn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_ROLE",
    "marketplace_id": "A21TJRUUN4KGV",
    "region": "eu-west-1",
    "endpoint": "https://sellingpartnerapi-eu.amazon.com"
  }}
}}
            """
            print("\nSample config.json:")
            print(sample_config)
            print("\nCopy this to datatodb/config/config.json and fill in the AWS credentials.")

        sys.exit(0)
    else:
        print("\n✗ Failed to obtain refresh token")
        print("\nPlease try the manual method described in the README.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
