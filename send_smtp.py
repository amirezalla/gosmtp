import smtplib
from email.mime.text import MIMEText

# Replace these values with your actual data
smtp_host = '34.29.73.169'  # Use the IP of the machine where the SMTP server is running
smtp_port = 1025  # The port your SMTP server is listening on
from_addr = 'd.mazzucchi@icoa.it'  # Sender's email address
to_addr = 'allahverdiamirreza@gmail.com'  # Recipient's email address

# Create a text/plain message
msg = MIMEText('This is the body of the test email.')
msg['Subject'] = 'Test Email from smtp'
msg['From'] = from_addr
msg['To'] = to_addr

try:
    # Send the message via our own SMTP server
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.send_message(msg)
        print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
