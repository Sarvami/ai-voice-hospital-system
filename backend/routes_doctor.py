import os
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from database import get_db_connection
from passlib.context import CryptContext
from datetime import date

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password[:72], hashed)

def db_error(e):
    print("DB ERROR:", e)
    return JSONResponse({"error": "Database error", "detail": str(e)}, status_code=500)

@router.post("/doctor/login")
def doctor_login(doc_id: str = Form(...), password: str = Form(...)):
    try:
        conn = get_db_connection()
        doctor = conn.execute("SELECT * FROM doctors WHERE doc_id=?", (doc_id,)).fetchone()
        conn.close()
        if not doctor or not verify_password(password, doctor["password_hash"]):
            return {"status": "invalid"}
        return {
            "status": "success",
            "doctor": {"id": doctor["doctor_id"], "name": doctor["name"], "department": doctor["department"]}
        }
    except Exception as e:
        return db_error(e)

@router.get("/doctor/dashboard")
def doctor_dashboard(doctor_id: int):
    try:
        conn = get_db_connection()
        doc = conn.execute("""
            SELECT name, department, rating, qualification, available_days, contact_phone, email, region
            FROM doctors WHERE doctor_id=?
        """, (doctor_id,)).fetchone()
        if not doc:
            conn.close(); return {"error": "Not found"}
        today_str = date.today().strftime("%Y-%m-%d")
        appt_today = conn.execute("SELECT COUNT(*) FROM appointments WHERE doctor_id=? AND appointment_date=?", (doctor_id, today_str)).fetchone()[0]
        total_p    = conn.execute("SELECT COUNT(DISTINCT patient_id) FROM appointments WHERE doctor_id=?", (doctor_id,)).fetchone()[0]
        conn.close()
        return {
            "name": doc["name"],
            "specialization": doc["department"],
            "qualification": doc["qualification"],
            "available_days": doc["available_days"],
            "phone": doc["contact_phone"],
            "email": doc["email"],
            "region": doc["region"],
            "appointments_today": appt_today,
            "total_patients": total_p,
            "rating": round(doc["rating"] or 4.5, 1)
        }
    except Exception as e:
        return db_error(e)

@router.get("/doctor/patients")
def get_doctor_patients(doctor_id: int):
    try:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT DISTINCT p.patient_id, p.name, p.age, p.gender, p.phone
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            WHERE a.doctor_id = ?
        """, (doctor_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return db_error(e)

@router.get("/doctor/ratings")
def get_doctor_ratings(doctor_id: int):
    try:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT p.name AS patient_name, a.rating, a.review, a.appointment_date AS date
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            WHERE a.doctor_id = ? AND a.rating IS NOT NULL
            ORDER BY a.appointment_date DESC
        """, (doctor_id,)).fetchall()
        conn.close()
        return {"ratings": [dict(r) for r in rows]}
    except Exception as e:
        return db_error(e)

@router.get("/doctor/appointments")
def doctor_appointments(doctor_id: int):
    try:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT a.appointment_id AS id, p.name AS patient_name, a.appointment_date AS date,
                   a.appointment_time AS time, a.status, a.reason
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            WHERE a.doctor_id=?
            ORDER BY a.appointment_date DESC
        """, (doctor_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return db_error(e)
