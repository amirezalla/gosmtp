from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
import requests
import asyncio
import socket
import re
import psycopg2
import os
from email.message import EmailMessage


def get_local_ip_address():
    """Attempt to find the local IP address of the machine."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return 'localhost'

class CustomHandler(Message):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_class = EmailMessage


        self.db_host = os.getenv('DB_HOST')
        self.db_username = os.getenv('DB_USERNAME')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_name = os.getenv('DB_NAME')

    def create_db_connection(self):
        return psycopg2.connect(
            host=self.db_host,
            user=self.db_username,
            password=self.db_password,
            dbname=self.db_name
        )

    def authenticate_and_increment(self, username, password):
        with self.create_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM users WHERE username=%s AND password=%s",
                    (username, password)
                )
                user = cursor.fetchone()

                if user:
                    cursor.execute(
                        "UPDATE users SET usage = usage + 1 WHERE id=%s",
                        (user[0],)
                    )
                    conn.commit()
                    return True
        return False

    def extract_body(self, message):
        if message.is_multipart():
            parts = [self.extract_body(part) for part in message.get_payload()]
            return "\n".join(filter(None, parts))
        else:
            payload = message.get_payload(decode=True)
            return payload.decode('utf-8') if isinstance(payload, bytes) else payload

    def handle_message(self, message):
        mail_from = message['from']
        rcpt_tos = message['to']
        subject = message['subject']
        body = self.extract_body(message)

        smtp_username = 'icoa'
        smtp_password = 'Amir208079@'

        if not self.authenticate_and_increment(smtp_username, smtp_password):
            print("Authentication failed")
            return '535 Authentication failed'

        print(f"Receiving message from: {mail_from}")
        print(f"Message addressed to: {rcpt_tos}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")

        match = re.match(r'(?P<name>.+?)\s*<(?P<email>\S+@\S+)>', mail_from)
        if match:
            name = match.group('name')
            from_email = match.group('email')
        else:
            name = ''
            from_email = mail_from
        
        response = requests.post('https://sendgrid-hlixxcbawa-uc.a.run.app/api/sendEmail', json={
            "from": from_email,
            "name": name,
            "recipients": rcpt_tos,
            "message": body,
            "subject": subject
        })

        print(f"POST request response: {response.status_code}, {response.text}")

        return '250 Message accepted for delivery'

if __name__ == "__main__":
    # For demonstration purposes; replace with secure configuration handling in production
    os.environ['DB_HOST'] = '34.77.161.76'
    os.environ['DB_USERNAME'] = 'root'
    os.environ['DB_PASSWORD'] = 'Amir208079@'
    os.environ['DB_NAME'] = 'sendgrid'

    hostname = get_local_ip_address()
    port = 1025
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    handler = CustomHandler()
    controller = Controller(handler, hostname=hostname, port=port)
    controller.start()

    print(f"SMTP server is running at {hostname}:{port}")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        controller.stop()
