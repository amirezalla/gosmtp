import asyncio
import aiohttp
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
from email import message_from_bytes
import socket

def get_local_ip_address():
    """Attempt to find the local IP address of the machine."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Use Google's DNS server to find local IP
            return s.getsockname()[0]
    except Exception:
        return 'localhost'  # Fallback to localhost if unable to determine IP

class CustomHandler(Message):
    async def handle_message(self,envelope):
        mail_from = envelope.mail_from
        rcpt_tos = envelope.rcpt_tos
        data = envelope.content  # Email content in bytes

        # Convert the bytes data to a message object
        message = message_from_bytes(data)

        # Extract subject and body, assuming plain text for simplicity
        subject = message.get('Subject', 'No Subject')
        body = message.get_payload(decode=True).decode('utf-8', errors='replace')

        # Prepare the payload for the POST request
        payload = {
            "from": mail_from,
            "recipients": rcpt_tos,
            "subject": subject,
            "message": body,
        }

        # Use aiohttp to send the POST request asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.post('https://sendgrid-hlixxcbawa-uc.a.run.app/api/sendEmail', json=payload) as response:
                print(f"POST request response: {response.status}, {await response.text()}")

        # Return SMTP server response to indicate successful handling
        return '250 Message accepted for delivery'

if __name__ == "__main__":
    ip_address = get_local_ip_address()
    port = 1025
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    handler = CustomHandler()
    controller = Controller(handler, hostname=ip_address, port=port)

    print(f"SMTP server is running at {ip_address}:{port}. Press Ctrl+C to shut down.")
    controller.start()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        controller.stop()