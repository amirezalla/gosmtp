from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
import requests
import asyncio
import socket
from email import message_from_bytes
import json

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
    async def handle_DATA(self, server, session, envelope):
        mail_from = envelope.mail_from
        rcpt_tos = envelope.rcpt_tos
        data = envelope.content  # This is the raw email content

        # Convert the raw email data to a Message object
        message = message_from_bytes(data)

        # Assuming the body is plain text for simplicity; adjust as needed for MIME/multipart
        body = message.get_payload(decode=True).decode('utf-8', errors='replace')

        subject = message.get('Subject', '')

        # Convert to and recipients to simple lists for JSON serialization
        recipients = list(rcpt_tos)

        print(f"Receiving message from: {mail_from}")
        print(f"Message addressed to: {recipients}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")

        # Now, `recipients`, `mail_from`, `subject`, and `body` should be JSON serializable
        payload = {
            "from": mail_from,
            "recipients": recipients,
            "message": body,
            "subject": subject
        }

        # Ensure that you serialize payload to JSON when making the POST request
        response = requests.post('https://sendgrid-hlixxcbawa-uc.a.run.app/api/sendEmail', json=payload)

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
