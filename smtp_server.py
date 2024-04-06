from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
from aiosmtpd.smtp import SMTP, AuthResult, LoginPassword
import requests
import asyncio
import socket
import re
import mysql.connector
import base64
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

    

class CustomSMTPHandler(Message):

    def factory(self):
        """Return a new instance of the custom SMTP class on each call."""
        return SMTP(self.handler)
    
    async def handle_AUTH(self, server, session, envelope, mechanism, auth_data):
        if mechanism != 'LOGIN':
            return AuthResult(success=False, handled=False)

        # Decode the credentials
        username = base64.b64decode(auth_data.login).decode()
        password = base64.b64decode(auth_data.password).decode()

        # Log or use the credentials here for your custom authentication
        print(f"Username: {username}, Password: {password}")

        # Implement your authentication logic here
        # For demonstration, we're assuming authentication always succeeds
        return AuthResult(success=True)
    
class CustomHandler(Message,SMTP):

    
        

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_class = EmailMessage
        self.authenticated_user = None
        self.server=None

        self.db_host = os.getenv('DB_HOST')
        self.db_username = os.getenv('DB_USERNAME')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_name = os.getenv('DB_NAME')

    async def smtp_AUTH(self, arg):
        mechanism, credentials = arg.split(' ', 1)
        if mechanism.upper() == 'LOGIN':
            username = await self._reader.readline()
            password = await self._reader.readline()
            username = username.strip().decode('utf-8')
            password = password.strip().decode('utf-8')
            
            # Implement your authentication check here
            # For demonstration, assuming authentication always succeeds
            print(f"Authenticating: {username}")
            # If authentication succeeds:
            self.session.authenticated = True
            return AuthResult(success=True)


    def create_db_connection(self):
        """Establishes a connection to the MySQL database."""
        return mysql.connector.connect(
            host=self.db_host,
            user=self.db_username,
            passwd=self.db_password,
            database=self.db_name
        )

    def authenticate_and_increment(self, username, password):
        """Authenticates the user and increments usage counter."""
        try:
            conn = self.create_db_connection()
            cursor = conn.cursor()
            # Adjusted the query for MySQL
            cursor.execute("SELECT id FROM smtp WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()

            if user:
                # Increment usage
                cursor.execute("UPDATE smtp SET `usage` = `usage` + 1 WHERE id = %s", (user[0],))
                conn.commit()
                return user
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
        finally:
            if conn.is_connected():
                conn.close()
        return False
            

    def extract_body(self, message):
        if message.is_multipart():
            parts = [self.extract_body(part) for part in message.get_payload()]
            return "\n".join(filter(None, parts))
        else:
            payload = message.get_payload(decode=True)
            return payload.decode('utf-8') if isinstance(payload, bytes) else payload

    def handle_message(self, server, session, message):
        if not getattr(session, 'authenticated', False):
            print("Rejecting unauthenticated message.")
            return '535 Authentication required'
        mail_from = message['from']
        rcpt_tos = message['to']
        subject = message['subject']
        body = self.extract_body(message)

        # smtp_username = 'icoa'
        # smtp_password = 'Amir208079@'
        print('server',self.server)
        if not self.authenticated_user:
            print("No authenticated user.")
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
    # For demonstration purposes; replace with secure configuration handling in production  ----587
    os.environ['DB_HOST'] = '34.77.161.76'
    os.environ['DB_USERNAME'] = 'root'
    os.environ['DB_PASSWORD'] = 'Amir208079@'
    os.environ['DB_NAME'] = 'sendgrid'

    hostname = get_local_ip_address()
    ports = [1025]
    controllers = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for port in ports:
        handler = CustomHandler()
        controller = Controller(handler, hostname=hostname, port=port) 
        controller.start()
        print(f"SMTP server is running at {hostname}:{port}")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        for controller in controllers:
            controller.stop()
