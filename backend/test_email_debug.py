"""
Run: venv/Scripts/python.exe test_email_debug.py
"""
import smtplib
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

sender   = os.getenv("EMAIL_SENDER", "")
password = os.getenv("EMAIL_PASSWORD", "")

print(f"Sender  : {sender}")
print(f"Password: {repr(password)}")
print(f"Length  : {len(password)} chars")
print()

# Check for common mistakes
if " " in password:
    print("WARNING: password contains spaces — remove all spaces from the App Password")
if len(password) != 16:
    print(f"WARNING: App Passwords are exactly 16 chars, yours is {len(password)}")
if password == password.lower() and password.isalpha():
    print("OK: looks like a valid App Password format (16 lowercase letters)")

print()
print("Connecting to smtp.gmail.com:465 ...")
try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        print("Connected OK")
        print("Logging in ...")
        server.login(sender, password)
        print("Login SUCCESS — credentials are correct!")
except smtplib.SMTPAuthenticationError as e:
    print(f"Auth FAILED: {e}")
    print()
    print("Fix steps:")
    print("  1. Go to https://myaccount.google.com/security")
    print("  2. Make sure 2-Step Verification is ON")
    print("  3. Go to https://myaccount.google.com/apppasswords")
    print("  4. Create a new App Password (App: Mail, Device: Other)")
    print("  5. Copy the 16-char code — NO spaces — into .env as EMAIL_PASSWORD")
except Exception as e:
    print(f"Other error: {e}")
