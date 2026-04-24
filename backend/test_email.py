"""
Run this to test email sending directly:
  venv/Scripts/python.exe test_email.py your_target@gmail.com
"""
import sys
import os
import smtplib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

host     = os.getenv("EMAIL_HOST", "smtp-relay.brevo.com")
port     = int(os.getenv("EMAIL_PORT", "587"))
sender   = os.getenv("EMAIL_SENDER", "")
login    = os.getenv("EMAIL_LOGIN", sender)
password = os.getenv("EMAIL_PASSWORD", "")

print(f"EMAIL_HOST     = {host}")
print(f"EMAIL_PORT     = {port}")
print(f"EMAIL_SENDER   = {sender!r}")
print(f"EMAIL_LOGIN    = {login!r}")
print(f"EMAIL_PASSWORD = {'*' * len(password) if password else '(empty)'}")
print()

if not sender:
    print("ERROR: EMAIL_SENDER is not set in .env")
    sys.exit(1)
if not password or password == "<brevo_smtp_key>":
    print("ERROR: EMAIL_PASSWORD is not set — replace <brevo_smtp_key> with your actual Brevo SMTP key in .env")
    sys.exit(1)

# Raw SMTP login test first
print(f"Connecting to {host}:{port} ...")
try:
    server = smtplib.SMTP(host, port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(login, password)
    print("LOGIN SUCCESS — credentials are correct!")
    server.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"Auth FAILED: {e}")
    print()
    print("Fix: Go to https://app.brevo.com → SMTP & API → SMTP tab")
    print("     Copy the SMTP key and paste it as EMAIL_PASSWORD in .env")
    sys.exit(1)
except Exception as e:
    print(f"Connection error: {e}")
    sys.exit(1)

# Now send a real test email
to = sys.argv[1] if len(sys.argv) > 1 else sender
print(f"\nSending test OTP email to: {to}")

from email_service import send_otp_email
result = send_otp_email(to, "123456", "Test User")
print("Result:", "SUCCESS — check your inbox!" if result else "FAILED — check the error above")
