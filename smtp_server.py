from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
import requests
import asyncio
import socket

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

    def extract_body(self, message):
        """Extracts the email body from a message object, handling both singlepart and multipart messages."""
        if message.is_multipart():
            # For multipart messages, get the payload for each part
            parts = [self.extract_body(part) for part in message.get_payload()]
            # Join the parts or handle them as needed (this example assumes you want plain text parts)
            return "\n".join(part for part in parts if part is not None)
        else:
            # For singlepart messages, just get the payload
            return message.get_payload(decode=True)
    
    def handle_message(self, message):
        mail_from = message['from']
        rcpt_tos = message['to']
        subject = message['subject']
        body_bytes = self.extract_body(message)
        body = body_bytes.decode('utf-8') if body_bytes is not None else ''

        print(f"Receiving message from: {mail_from}")
        print(f"Message addressed to: {rcpt_tos}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")

        # Forwarding the email via a POST request
        response = requests.post('https://sendgrid-hlixxcbawa-uc.a.run.app/api/sendEmail', json={
            "from": mail_from,
            "recipients": rcpt_tos,
            "message": body,
            "subject": subject
        })

        print(f"POST request response: {response.status_code}, {response.text}")
        
        return '250 Message accepted for delivery'

if __name__ == "__main__":
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