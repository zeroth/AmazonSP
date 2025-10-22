from datetime import datetime, timedelta
from ..utils.sp_api_auth import SPAPIAuth

class FinancesManager:
    def __init__(self, sp_api_auth: SPAPIAuth):
        self.finances_api = sp_api_auth.get_finances_api()
    
    def get_financial_events(self, days_back=30):
        posted_after = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        try:
            response = self.finances_api.get_financial_events(
                PostedAfter=posted_after
            )
            
            financial_events = []
            for event in response.payload.get('FinancialEvents', []):
                financial_events.append({
                    'event_type': event.get('FinancialEventType'),
                    'posted_date': event.get('PostedDate'),
                    'amount': event.get('Amount', {}).get('Amount'),
                    'currency': event.get('Amount', {}).get('CurrencyCode')
                })
            
            return financial_events
            
        except Exception as e:
            print(f"Error fetching financial events: {str(e)}")
            return [] 