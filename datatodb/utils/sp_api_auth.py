import json
from sp_api.api import Orders, Finances
from sp_api.base import Marketplaces
from sp_api.base.credentials import Credentials

class SPAPIAuth:
    def __init__(self, config_path='config/config.json'):
        with open(config_path) as f:
            self.config = json.load(f)['sp_api']
        
        self.credentials = Credentials(
            refresh_token=self.config['refresh_token'],
            lwa_app_id=self.config['lwa_app_id'],
            lwa_client_secret=self.config['lwa_client_secret'],
            aws_access_key=self.config['aws_access_key'],
            aws_secret_key=self.config['aws_secret_key'],
            role_arn=self.config['role_arn']
        )
        
        self.marketplace = Marketplaces[self.config['marketplace_id']]
    
    def get_orders_api(self):
        return Orders(credentials=self.credentials, marketplace=self.marketplace)
    
    def get_finances_api(self):
        return Finances(credentials=self.credentials, marketplace=self.marketplace) 