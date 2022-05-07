from __init__ import SMTPPROXY
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

message = MIMEMultipart()
message["From"] = "nobody@localhost"
message["To"] = "noreply@localhost"
message["Subject"] = "SMTP Proxy Test Subject"
message.attach(MIMEText("SMTP Proxy Test Body", "plain"))

smtp_client = SMTPPROXY('localhost', 8025)
smtp_client.send("nobody@localhost", "noreply@localhost", message.as_string())
smtp_client.close()

smtp_client = SMTPPROXY('localhost', 8025, proxy=dict(addr='localhost', port=8080))
smtp_client.send("nobody@localhost", "noreply@localhost", message.as_string())
smtp_client.close()
