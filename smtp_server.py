import smtpd
import ssl
import asyncio
import email
from email.parser import BytesParser
import requests
import mysql.connector
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

class CustomSMTPServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        msg = BytesParser().parsebytes(data)
        from_address = msg['from']
        to_address = msg['to']
        subject = msg['subject']
        body = msg.get_payload()

        print(f'Received email from: {from_address}')
        
        # Forward email
        self.forward_email(from_address, to_address, subject, body)

        return 'Message processed'

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

    def handle_AUTH(self, username, password):
        if self.authenticate_user(username, password):
            return '235 Authentication successful'
        else:
            return '535 Authentication credentials invalid'

def get_server_ip_address():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

async def start_server():
    loop = asyncio.get_event_loop()
    server = await loop.create_server(
        lambda: CustomSMTPServer(('0.0.0.0', 1025), None),
        ssl=ssl_context
    )
    print(f'SMTP server running on port 1025 with SSL')
    try:
        await server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    asyncio.run(start_server())
