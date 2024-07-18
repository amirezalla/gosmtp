import asyncio
import ssl
from aiosmtpd.controller import Controller
from email.parser import BytesParser
import email
import mysql.connector
import requests
import socket

# Create database connection
db_config = {
    'host': '35.198.135.195',
    'user': 'amir',
    'password': 'Amir208079@',
    'database': 'sendgrid'
}
db = mysql.connector.connect(**db_config)
cursor = db.cursor()

print('Connected to database.')

# SSL/TLS Options
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile='sendgrid.icoa.it.crt', keyfile='sendgrid.icoa.it-key.pem')

class CustomMessageHandler:
    async def handle_DATA(self, server, session, envelope):
        msg = BytesParser().parsebytes(envelope.content)
        from_address = msg['from']
        to_address = msg['to']
        subject = msg['subject']
        
        # Convert the email message to a string to forward it
        body = msg.get_payload(decode=True).decode('utf-8', errors='replace')

        print(f'Received email from: {from_address}')
        
        # Forward email
        self.forward_email(from_address, to_address, subject, body)

        return '250 Message processed'

    def forward_email(self, from_address, to_address, subject, body):
        try:
            response = requests.post('https://sendgrid-hlixxcbawa-uc.a.run.app/api/sendEmail', json={
                'from': from_address,
                'recipients': to_address,
                'subject': subject,
                'message': body
            })
            print('Email forwarded:', response.status_code, response.json())
        except requests.exceptions.RequestException as e:
            print('Failed to forward email:', e)

    def authenticate_user(self, username, password):
        query = "SELECT * FROM `smtp` WHERE `username` = %s AND `password` = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchall()
        if result:
            update_query = "UPDATE `smtp` SET `usage` = `usage` + 1 WHERE `username` = %s"
            cursor.execute(update_query, (username,))
            db.commit()
            print(f'Authenticated and incremented {username} successfully.')
            return True
        return False

def get_server_ip_address():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

async def start_server():
    handler = CustomMessageHandler()
    controller = Controller(handler, hostname='0.0.0.0', port=1025, ssl_context=ssl_context)
    controller.start()
    print(f'SMTP server running on port 1025 with SSL')
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        controller.stop()

if __name__ == '__main__':
    asyncio.run(start_server())
