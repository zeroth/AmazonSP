import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

class NotificationManager:
    def __init__(self, config_path='config/config.json'):
        with open(config_path) as f:
            self.config = json.load(f)['email']
        
    def send_email(self, subject, message, recipients=None):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['sender_email']
            msg['To'] = ', '.join(recipients or self.config['default_recipients'])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['smtp_username'], self.config['smtp_password'])
            
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            raise Exception(f"Error sending notification: {str(e)}") 