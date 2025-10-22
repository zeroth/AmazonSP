from datetime import datetime, timedelta, UTC
from ..utils.sp_api_auth import SPAPIAuth

class OrdersManager:
    def __init__(self, sp_api_auth: SPAPIAuth):
        self.orders_api = sp_api_auth.get_orders_api()
    
    def get_orders(self, days_back=30):
        created_after = (datetime.now(UTC) - timedelta(days=days_back)).isoformat()
        
        try:
            response = self.orders_api.get_orders(
                CreatedAfter=created_after,
                OrderStatuses=['Shipped', 'Pending', 'Unshipped']
            )
            
            orders = []
            for order in response.payload['Orders']:
                orders.append({
                    'order_id': order.get('AmazonOrderId'),
                    'purchase_date': order.get('PurchaseDate'),
                    'order_status': order.get('OrderStatus'),
                    'order_total': order.get('OrderTotal', {}).get('Amount'),
                    'shipping_address': order.get('ShippingAddress')
                })
            
            return orders
            
        except Exception as e:
            print(f"Error fetching orders: {str(e)}")
            return [] 