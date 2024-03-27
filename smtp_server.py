from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
import requests
import asyncio
import socket
import re
import psycopg2
import os



def get_local_ip_address():
    """Attempt to find the local IP address of the machine."""
    try:
        # Attempt to connect to a well-known remote server and read the local endpoint's IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Google's DNS server
            return s.getsockname()[0]
    except Exception:
        return 'localhost'  # Fallback to localhost

class CustomHandler(Message):
    def __init__(self):
        # Database connection parameters should be retrieved from environment variables for security
        self.db_host = os.getenv('DB_HOST')
        self.db_username = os.getenv('DB_USERNAME')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_name = os.getenv('DB_NAME')  # The name of the database

    def create_db_connection(self):
        # Establish a connection to the database
        return psycopg2.connect(
            host=self.db_host,
            user=self.db_username,
            password=self.db_password,
            dbname=self.db_name
        )
    
    def authenticate_and_increment(self, username, password):
        conn = self.create_db_connection()
        cursor = conn.cursor()

        # Check if the username and password exist in the database
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            # User is authenticated, increment the usage counter
            cursor.execute("UPDATE users SET usage = usage + 1 WHERE id=?", (user[0],))
            conn.commit()
            return True
        else:
            # Authentication failed
            return False

    def extract_body(self, message):
        """Extracts the email body from a message object, handling both singlepart and multipart messages."""
        if message.is_multipart():
            # Initialize an empty list to hold the decoded parts
            parts = []
            for part in message.get_payload():
                # Recursively extract and decode each part
                part_payload = self.extract_body(part)
                if part_payload is not None:
                    # Ensure the part is decoded to a string before adding it to the list
                    parts.append(part_payload.decode('utf-8') if isinstance(part_payload, bytes) else part_payload)
            # Join the decoded parts with a newline (or other delimiter as needed)
            return "\n".join(parts)
        else:
            # For singlepart messages, directly return the decoded payload
            payload = message.get_payload(decode=True)
            # Check if the payload is bytes and decode it; if it's str, use it as is
            return payload.decode('utf-8') if isinstance(payload, bytes) else payload
        
    
    def handle_message(self, message):
        mail_from = message['from']
        rcpt_tos = message['to']
        subject = message['subject']
        body = self.extract_body(message)

        smtp_username = 'icoa'
        smtp_password = 'Amir208079@'

        # Authenticate and increment usage
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
        # Forwarding the email via a POST request
        response = requests.post('https://sendgrid-hlixxcbawa-uc.a.run.app/api/sendEmail', json={
            "from": from_email,  # Use the extracted email
            "name": name,  # Optionally, include the name if your API supports it
            "recipients": rcpt_tos,
            "message": body,
            "subject": subject
        })

        print(f"POST request response: {response.status_code}, {response.text}")
        
        return '250 Message accepted for delivery'

if __name__ == "__main__":


    os.environ.setdefault('DB_HOST', '34.77.161.76')
    os.environ.setdefault('DB_USERNAME', 'root')
    os.environ.setdefault('DB_PASSWORD', 'Amir208079@')
    os.environ.setdefault('DB_NAME', 'sendgrid')
    
    hostname = get_local_ip_address()
    port = 1025
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    handler = CustomHandler()
    controller = Controller(handler, hostname=hostname, port=port)
    controller.start()

    print(f"SMTP server is running at {hostname}:{port}")
    print("Press Ctrl+C to shut down.")

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        controller.stop()