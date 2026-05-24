"""Analytics queries for admin dashboard charts."""
from datetime import datetime, timedelta


def get_appointments_per_day(conn, days: int = 14):
    since = (datetime.utcnow() - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    rows = conn.execute(
        """SELECT appointment_date AS day, COUNT(*) AS count
           FROM appointments
           WHERE appointment_date >= ?
           GROUP BY appointment_date
           ORDER BY appointment_date ASC""",
        (since,),
    ).fetchall()
    return [{"day": r["day"], "count": r["count"]} for r in rows]


def get_appointments_by_department(conn):
    rows = conn.execute(
        """SELECT d.department AS department, COUNT(*) AS count
           FROM appointments a
           JOIN doctors d ON a.doctor_id = d.doctor_id
           WHERE LOWER(a.status) NOT IN ('cancelled')
           GROUP BY d.department
           ORDER BY count DESC"""
    ).fetchall()
    return [{"department": r["department"], "count": r["count"]} for r in rows]


def get_patients_by_region(conn):
    rows = conn.execute(
        """SELECT COALESCE(NULLIF(TRIM(region), ''), 'Unknown') AS region, COUNT(*) AS count
           FROM patients
           GROUP BY region
           ORDER BY count DESC"""
    ).fetchall()
    return [{"region": r["region"], "count": r["count"]} for r in rows]
