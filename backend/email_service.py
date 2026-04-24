import smtplib
import random
import string
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)


def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


def send_email(to_email: str, subject: str, body: str) -> bool:
    # Read at call-time so dotenv is guaranteed to be loaded
    host     = os.getenv("EMAIL_HOST", "smtp-relay.brevo.com")
    port     = int(os.getenv("EMAIL_PORT", "587"))
    sender   = os.getenv("EMAIL_SENDER", "")
    login    = os.getenv("EMAIL_LOGIN", sender)
    password = os.getenv("EMAIL_PASSWORD", "")

    if not sender or not login or not password:
        print("Email error: EMAIL_SENDER / EMAIL_LOGIN / EMAIL_PASSWORD not configured in .env")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = f"SwasthSewa Hospital <{sender}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP(host, port)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(login, password)
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        
        print(f"Email sent to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"Email error: Authentication failed — check EMAIL_SENDER and EMAIL_PASSWORD in .env")
        print(f"  Details: {e}")
        return False
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_otp_email(to_email: str, otp: str, patient_name: str) -> bool:
    subject = "Your OTP - SwasthSewa Hospital"
    body = f"""
    <div style="font-family:sans-serif;max-width:400px;margin:auto;padding:32px;background:#0a0f1e;color:#e8eaf6;border-radius:16px;">
      <h2 style="color:#4fc3f7;">SwasthSeva 🏥</h2>
      <p>Hello <b>{patient_name}</b>,</p>
      <p>Your OTP for login is:</p>
      <div style="font-size:36px;font-weight:700;letter-spacing:8px;color:#4fc3f7;margin:24px 0;">{otp}</div>
      <p style="color:#7986cb;">This OTP is valid for <b>5 minutes</b>. Do not share it with anyone.</p>
    </div>
    """
    return send_email(to_email, subject, body)


def send_cancellation_email(to_email: str, patient_name: str, doctor_name: str, date: str, time: str, reason: str) -> bool:
    subject = "SwasthSeva — Appointment Cancelled"
    body = f"""
    <div style="font-family:sans-serif;max-width:400px;margin:auto;padding:32px;background:#0a0f1e;color:#e8eaf6;border-radius:16px;">
      <h2 style="color:#ef9a9a;">Appointment Cancelled ❌</h2>
      <p>Hello <b>{patient_name}</b>,</p>
      <p>Your appointment has been cancelled.</p>
      <table style="width:100%;margin:16px 0;color:#e8eaf6;">
        <tr><td style="color:#7986cb;">Doctor</td><td><b>{doctor_name}</b></td></tr>
        <tr><td style="color:#7986cb;">Date</td><td>{date}</td></tr>
        <tr><td style="color:#7986cb;">Time</td><td>{time}</td></tr>
        <tr><td style="color:#7986cb;">Reason</td><td>{reason}</td></tr>
      </table>
      <p style="color:#7986cb;">Please book a new appointment if needed.</p>
    </div>
    """
    return send_email(to_email, subject, body)


def send_meet_email(to_email: str, patient_name: str, doctor_name: str, meet_link: str, scheduled_time: str) -> bool:
    subject = "Video Consultation Link - SwasthSewa Hospital"
    body = f"""
    <div style="font-family:sans-serif;max-width:400px;margin:auto;padding:32px;background:#0a0f1e;color:#e8eaf6;border-radius:16px;">
      <h2 style="color:#4fc3f7;">Video Consultation 🎥</h2>
      <p>Hello <b>{patient_name}</b>,</p>
      <p>Dr. {doctor_name} has scheduled a video consultation with you.</p>
      <p><b>Time:</b> {scheduled_time}</p>
      <div style="margin:24px 0;">
        <a href="{meet_link}" style="background:#4fc3f7;color:#0a0f1e;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">Join Google Meet</a>
      </div>
      <p style="color:#7986cb;font-size:12px;">Link: {meet_link}</p>
    </div>
    """
    return send_email(to_email, subject, body)
