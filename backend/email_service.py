import smtplib
import random
import string
import os
import requests as _requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

# FIX: PermissionError [Errno 13] when urllib3 tries to write to a restricted SSLKEYLOGFILE path
if "SSLKEYLOGFILE" in os.environ:
    os.environ.pop("SSLKEYLOGFILE")


def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


def send_email(to_email: str, subject: str, body: str) -> bool:
    api_key = os.getenv("BREVO_API_KEY", "")

    if not api_key:
        print("Email error: BREVO_API_KEY not set in .env")
        return False

    try:
        sender_name  = os.getenv("EMAIL_SENDER_NAME", "SwasthSewa Hospital")
        sender_email = os.getenv("EMAIL_SENDER", "swasthsewa.voiceagent1@gmail.com")

        resp = _requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "sender":     {"name": sender_name, "email": sender_email},
                "to":         [{"email": to_email}],
                "subject":    subject,
                "htmlContent": body
            },
            timeout=15
        )

        if resp.status_code in (200, 201):
            print(f"Email sent to {to_email} via Brevo API")
            return True
        else:
            try:
                err_data = resp.json()
                msg = err_data.get("message", resp.text)
                print(f"Brevo API error {resp.status_code}: {msg}")
            except:
                print(f"Brevo API error {resp.status_code}: {resp.text}")
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


def send_reminder_email(to_email: str, patient_name: str, doctor_name: str, date: str, time: str) -> bool:
    subject = "Appointment Reminder — SwasthSeva"
    body = f"""
    <div style="font-family:sans-serif;max-width:400px;margin:auto;padding:32px;background:#0a0f1e;color:#e8eaf6;border-radius:16px;">
      <h2 style="color:#4fc3f7;">Appointment Reminder 📅</h2>
      <p>Hello <b>{patient_name}</b>,</p>
      <p>This is a reminder that you have an appointment <b>tomorrow</b>.</p>
      <table style="width:100%;margin:16px 0;color:#e8eaf6;">
        <tr><td style="color:#7986cb;">Doctor</td><td><b>{doctor_name}</b></td></tr>
        <tr><td style="color:#7986cb;">Date</td><td>{date}</td></tr>
        <tr><td style="color:#7986cb;">Time</td><td>{time}</td></tr>
      </table>
      <p style="color:#7986cb;">Please arrive 10 minutes early. Stay healthy!</p>
    </div>
    """
    return send_email(to_email, subject, body)


def send_sos_email(to_email: str, patient_name: str) -> bool:
    subject = "🚨 EMERGENCY ALERT — SwasthSeva"
    body = f"""
    <div style="font-family:sans-serif;max-width:400px;margin:auto;padding:32px;background:#1a0000;color:#e8eaf6;border-radius:16px;border:2px solid #ef5350;">
      <h2 style="color:#ef5350;">🚨 EMERGENCY DETECTED</h2>
      <p>Hello <b>{patient_name}</b>,</p>
      <p>An emergency keyword was detected during your voice session.</p>
      <p style="font-size:20px;font-weight:700;color:#ef5350;">Please call <b>108</b> immediately for emergency services.</p>
      <p style="color:#7986cb;">If this was a mistake, please ignore this message.</p>
    </div>
    """
    return send_email(to_email, subject, body)


def send_reschedule_email(to_email: str, patient_name: str, doctor_name: str, new_date: str, new_time: str) -> bool:
    subject = "Appointment Rescheduled — SwasthSeva"
    body = f"""
    <div style="font-family:sans-serif;max-width:400px;margin:auto;padding:32px;background:#0a0f1e;color:#e8eaf6;border-radius:16px;">
      <h2 style="color:#4fc3f7;">Appointment Rescheduled 🔄</h2>
      <p>Hello <b>{patient_name}</b>,</p>
      <p>Your appointment has been rescheduled.</p>
      <table style="width:100%;margin:16px 0;color:#e8eaf6;">
        <tr><td style="color:#7986cb;">Doctor</td><td><b>{doctor_name}</b></td></tr>
        <tr><td style="color:#7986cb;">New Date</td><td>{new_date}</td></tr>
        <tr><td style="color:#7986cb;">New Time</td><td>{new_time}</td></tr>
      </table>
      <p style="color:#7986cb;">Please arrive 10 minutes early.</p>
    </div>
    """
    return send_email(to_email, subject, body)


def send_waitlist_notification_email(to_email: str, patient_name: str, doctor_name: str, department: str) -> bool:
    subject = "Slot Available — SwasthSeva Waitlist"
    body = f"""
    <div style="font-family:sans-serif;max-width:400px;margin:auto;padding:32px;background:#0a0f1e;color:#e8eaf6;border-radius:16px;">
      <h2 style="color:#4fc3f7;">Good News! A Slot is Available 🎉</h2>
      <p>Hello <b>{patient_name}</b>,</p>
      <p>A slot has opened up for <b>{department}</b> with <b>Dr. {doctor_name}</b>.</p>
      <p>Please log in to SwasthSeva and book your appointment before it fills up.</p>
      <p style="color:#7986cb;">This notification was sent because you joined the waitlist.</p>
    </div>
    """
    return send_email(to_email, subject, body)
