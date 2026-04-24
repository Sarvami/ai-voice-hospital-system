"""
Run: venv/Scripts/python.exe test_email_brevo.py your@email.com
Sends a raw email and prints every SMTP server response.
"""
import sys, os, smtplib
from pathlib import Path
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

host     = os.getenv("EMAIL_HOST", "smtp-relay.brevo.com")
port     = int(os.getenv("EMAIL_PORT", "587"))
login    = os.getenv("EMAIL_LOGIN", "")
password = os.getenv("EMAIL_PASSWORD", "")
sender   = os.getenv("EMAIL_SENDER", login)   # fallback to login if sender not set
to       = sys.argv[1] if len(sys.argv) > 1 else login

print(f"Host    : {host}:{port}")
print(f"Login   : {login}")
print(f"From    : {sender}")
print(f"To      : {to}")
print()

msg = MIMEMultipart()
msg["From"]    = f"SwasthSewa Hospital <{login}>"   # use login as From for Brevo
msg["To"]      = to
msg["Subject"] = "Your OTP - SwasthSewa Hospital"
msg.attach(MIMEText("<p>Your OTP is <b>123456</b></p>", "html"))

try:
    s = smtplib.SMTP(host, port, timeout=15)
    s.set_debuglevel(1)          # prints every SMTP command + response
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(login, password)
    result = s.sendmail(login, [to], msg.as_string())
    s.quit()
    print()
    if result:
        print(f"REJECTED by server: {result}")
    else:
        print("sendmail() returned no errors — email accepted by Brevo.")
        print("If it still doesn't arrive, check spam or verify sender in Brevo dashboard.")
except Exception as e:
    print(f"ERROR: {e}")
