import smtplib
from email.mime.text import MIMEText

# SMTP server configuration
smtp_host = '192.168.10.14'  # Replace with the IP of your SMTP server
smtp_port = 1025  # Ensure this is the port your SMTP server is listening on
to_addr = 'a.allahverdi@icoa.it'  # Sender's email address
from_addr = 's.akbarzadeh@icoa.it'  # Recipient's email address
username = 'f.castelli@icoa.it'  # SMTP username
password = 'f.castelli@icoa.it'  # SMTP password

# Create a text/plain message
msg = MIMEText('This is a test message.')
msg['Subject'] = 'Testing SMTP Server'
msg['From'] = from_addr
msg['To'] = to_addr

try:
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls() 
        server.ehlo()
        server.login(username, password)  # Authenticate
        server.send_message(msg)  # Send the email
        print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
