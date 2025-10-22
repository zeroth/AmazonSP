from google.cloud import bigtable
from google.cloud.bigtable import column_family
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

class GoogleCloudUtils:
    def __init__(self, config_path='config/config.json'):
        with open(config_path) as f:
            self.config = json.load(f)['google_cloud']
        
        self.credentials = service_account.Credentials.from_service_account_file(
            self.config['credentials_file']
        )
        
        self.bigtable_client = bigtable.Client(
            project=self.config['project_id'],
            credentials=self.credentials,
            admin=True
        )
        
        self.instance = self.bigtable_client.instance(self.config['bigtable_instance'])
    
    def create_table(self, table_name, column_families=None):
        table = self.instance.table(table_name)
        
        if not table.exists():
            column_families = column_families or {
                'data': column_family.MaxVersionsGCRule(1)
            }
            table.create(column_families=column_families)
        
        return table
    
    def write_to_bigtable(self, table_name, row_key, data, column_family='data'):
        table = self.instance.table(table_name)
        row = table.row(row_key)
        
        for key, value in data.items():
            row.set_cell(
                column_family,
                key.encode('utf-8'),
                str(value).encode('utf-8')
            )
        
        row.commit() 