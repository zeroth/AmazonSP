from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import pandas as pd
from datetime import datetime

class GoogleSheetsUtils:
    def __init__(self, config_path='config/config.json'):
        with open(config_path) as f:
            self.config = json.load(f)['google_cloud']
        
        self.credentials = service_account.Credentials.from_service_account_file(
            self.config['credentials_file'],
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheets = self.service.spreadsheets()
    
    def create_or_update_sheet(self, spreadsheet_id, data, sheet_name):
        try:
            # Convert data to DataFrame if it's a list of dictionaries
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame(data)
            
            # Prepare values for Google Sheets
            values = [df.columns.tolist()]
            values.extend(df.values.tolist())
            
            # Clear existing content
            range_name = f'{sheet_name}!A1:ZZ'
            self.sheets.values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            # Update with new data
            body = {
                'values': values
            }
            
            self.sheets.values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
            
        except Exception as e:
            raise Exception(f"Error updating Google Sheet: {str(e)}") 