"""Daily appointment reminder scheduler using APScheduler."""
from apscheduler.schedulers.background import BackgroundScheduler
from database import get_db_connection
from email_service import send_reminder_email
from datetime import datetime, timedelta


def send_daily_reminders():
    """Send reminder emails for appointments scheduled for tomorrow."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """SELECT a.appointment_id, p.name, p.email,
                      d.name AS doctor, a.appointment_date, a.appointment_time
               FROM appointments a
               JOIN patients p ON a.patient_id = p.patient_id
               JOIN doctors d ON a.doctor_id = d.doctor_id
               WHERE a.appointment_date = ? AND a.status = 'Booked'
               AND p.email IS NOT NULL""",
            (tomorrow,)
        ).fetchall()
    finally:
        conn.close()

    for r in rows:
        try:
            send_reminder_email(
                r["email"], r["name"], r["doctor"],
                r["appointment_date"], r["appointment_time"]
            )
        except Exception as e:
            print(f"Reminder email failed for {r['email']}: {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_reminders, "cron", hour=9, minute=0)
scheduler.start()
