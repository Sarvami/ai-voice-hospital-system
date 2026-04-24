import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load env from the backend directory
env_path = Path("backend/.env")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("BREVO_API_KEY")
sender_email = os.getenv("EMAIL_SENDER")
sender_name = os.getenv("EMAIL_SENDER_NAME")

print(f"API Key found: {bool(api_key)}")
print(f"Sender: {sender_name} <{sender_email}>")

if not api_key:
    print("ERROR: No API Key")
    exit(1)

test_recipient = "swasthsewa.voiceagent1@gmail.com" # Sending to self for test

resp = requests.post(
    "https://api.brevo.com/v3/smtp/email",
    headers={
        "api-key": api_key,
        "Content-Type": "application/json"
    },
    json={
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": test_recipient}],
        "subject": "Test Email from SwasthSeva",
        "htmlContent": "<h1>Connectivity Test</h1><p>This is a test to verify Brevo API.</p>"
    }
)

print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text}")
