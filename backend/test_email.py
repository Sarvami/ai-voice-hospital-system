"""
Run: venv/Scripts/python.exe test_email.py your@email.com
"""
import sys, os, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

# FIX: PermissionError [Errno 13] when urllib3 tries to write to a restricted SSLKEYLOGFILE path
if "SSLKEYLOGFILE" in os.environ:
    os.environ.pop("SSLKEYLOGFILE")

api_key = os.getenv("BREVO_API_KEY", "")
sender  = os.getenv("EMAIL_SENDER", "")
to      = sys.argv[1] if len(sys.argv) > 1 else sender

print(f"BREVO_API_KEY = {api_key[:20]}...")
print(f"EMAIL_SENDER  = {sender}")
print(f"Sending to    : {to}")
print()

if not api_key:
    print("ERROR: BREVO_API_KEY not set in .env")
    sys.exit(1)

resp = requests.post(
    "https://api.brevo.com/v3/smtp/email",
    headers={"api-key": api_key, "Content-Type": "application/json"},
    json={
        "sender":      {"name": "SwasthSewa Hospital", "email": sender},
        "to":          [{"email": to}],
        "subject":     "Your OTP - SwasthSewa Hospital",
        "htmlContent": "<p>Your OTP is <b>123456</b>. Valid for 5 minutes.</p>"
    },
    timeout=15
)

if resp.status_code in (200, 201):
    print("SUCCESS — check your inbox!")
else:
    print(f"FAILED {resp.status_code}: {resp.text}")
