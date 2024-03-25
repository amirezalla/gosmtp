import asyncio
import aiohttp
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import Envelope, Session
import socket
from email import message_from_bytes
from email.message import EmailMessage

def get_local_ip_address():
    """Attempt to find the local IP address of the machine."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Use Google's DNS server to find local IP
            return s.getsockname()[0]
    except Exception:
        return 'localhost'  # Fallback to localhost if unable to determine IP

class CustomHandler:
    async def handle_DATA(self, server, session, envelope):
        mail_from = envelope.mail_from
        rcpt_tos = envelope.rcpt_tos
        data = envelope.content  # Email content in bytes
        
        message = message_from_bytes(data)
        subject = message.get('Subject', 'No Subject')
        body = ''
        
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode('utf-8', errors='replace')
                    break  # Only interested in the first text/plain part
        else:
            payload = message.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='replace')
            else:
                body = ' [No content] '
        
        payload = {
            "from": mail_from,
            "recipients": list(rcpt_tos),
            "subject": subject,
            "message": body,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://sendgrid-hlixxcbawa-uc.a.run.app/api/sendEmail', json=payload) as response:
                print(f"POST request response: {response.status}, {await response.text()}")
        
        # Ensure response is in bytes
        return b'250 Message accepted for delivery'


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