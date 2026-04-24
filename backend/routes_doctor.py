import sqlite3
from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from datetime import date
from models import CancelAppointmentRequest
from database import get_db
from repositories import doctor_repo, appointment_repo

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password[:72], hashed)

def db_error(e):
    print("DB ERROR:", e)
    return JSONResponse({"error": "Database error", "detail": str(e)}, status_code=500)

@router.post("/doctor/login")
def doctor_login(doc_id: str = Form(...), password: str = Form(...),
                 db: sqlite3.Connection = Depends(get_db)):
    try:
        doctor = doctor_repo.get_doctor_by_doc_id(db, doc_id)
        if not doctor or not verify_password(password, doctor["password_hash"]):
            return {"status": "invalid"}
        return {"status": "success", "doctor": {
            "id": doctor["doctor_id"], "name": doctor["name"], "department": doctor["department"]
        }}
    except Exception as e:
        return db_error(e)

@router.get("/doctor/dashboard")
def doctor_dashboard(doctor_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        doc = doctor_repo.get_doctor_by_id(db, doctor_id)
        if not doc:
            return {"error": "Not found"}
        today_str = date.today().strftime("%Y-%m-%d")
        return {
            "name": doc["name"],
            "specialization": doc["department"],
            "qualification": doc["qualification"],
            "available_days": doc["available_days"],
            "phone": doc["contact_phone"],
            "email": doc["email"],
            "region": doc["region"],
            "appointments_today": doctor_repo.get_doctor_appointments_today(db, doctor_id, today_str),
            "total_patients": doctor_repo.get_doctor_total_patients(db, doctor_id),
            "rating": round(doc["rating"] or 4.5, 1)
        }
    except Exception as e:
        return db_error(e)

@router.get("/doctor/patients")
def get_doctor_patients(doctor_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        return appointment_repo.get_patients_by_doctor(db, doctor_id)
    except Exception as e:
        return db_error(e)

@router.get("/doctor/patient-reports/{patient_id}")
def get_patient_reports_for_doctor(patient_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        from repositories import report_repo
        reports = report_repo.get_reports_by_patient(db, patient_id)
        print(f"DEBUG: Fetching reports for patient {patient_id}. Found {len(reports)} reports.")
        return {"reports": reports}
    except Exception as e:
        print(f"ERROR: Failed to fetch reports for patient {patient_id}: {e}")
        return db_error(e)

@router.get("/doctor/ratings")
def get_doctor_ratings(doctor_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        return {"ratings": appointment_repo.get_ratings_by_doctor(db, doctor_id)}
    except Exception as e:
        return db_error(e)

@router.get("/doctor/appointments")
def doctor_appointments(doctor_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        return appointment_repo.get_appointments_by_doctor(db, doctor_id)
    except Exception as e:
        return db_error(e)


@router.post("/doctor/appointments/{appointment_id}/cancel")
def doctor_cancel_appointment(
    appointment_id: int,
    req: CancelAppointmentRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        result = appointment_repo.cancel_appointment_by_doctor(
            db, appointment_id, req.doctor_id, req.cancellation_reason
        )
        if not result.get("success"):
            return JSONResponse({"success": False, "message": result["message"]}, status_code=400)
        return {"success": True, "message": "Appointment cancelled and patient notified."}
    except Exception as e:
        return db_error(e)


# ── MESSAGING ─────────────────────────────────────────────────────────────────

from fastapi import Request
from repositories import patient_repo

@router.post("/doctor/send-message")
async def doctor_send_message(request: Request, db: sqlite3.Connection = Depends(get_db)):
    try:
        data = await request.json()
        doctor_id = data.get("doctor_id")
        patient_id = data.get("patient_id")
        appointment_id = data.get("appointment_id")
        message = data.get("message", "").strip()

        if not doctor_id or not patient_id or not message:
            return {"success": False, "message": "Missing fields"}

        db.execute("""
            INSERT INTO messages (sender_id, sender_role, receiver_id, receiver_role, appointment_id, message_text)
            VALUES (?, 'doctor', ?, 'patient', ?, ?)
        """, (doctor_id, patient_id, appointment_id, message))
        db.commit()
        msg_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"success": True, "message_id": msg_id}
    except Exception as e:
        print("ERROR in doctor_send_message:", e)
        return {"success": False, "message": "Could not send message."}


@router.get("/doctor/messages")
def doctor_get_messages(doctor_id: int, patient_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute("""
            SELECT message_id, sender_id, sender_role, message_text, is_read, created_at
            FROM messages
            WHERE (sender_id=? AND sender_role='doctor' AND receiver_id=? AND receiver_role='patient')
               OR (sender_id=? AND sender_role='patient' AND receiver_id=? AND receiver_role='doctor')
            ORDER BY created_at ASC
        """, (doctor_id, patient_id, patient_id, doctor_id)).fetchall()
        return {"messages": [dict(r) for r in rows]}
    except Exception as e:
        print("ERROR in doctor_get_messages:", e)
        return {"messages": []}


@router.get("/doctor/conversations")
def doctor_get_conversations(doctor_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute("""
            SELECT DISTINCT
                CASE WHEN sender_role='doctor' THEN receiver_id ELSE sender_id END AS patient_id
            FROM messages
            WHERE (sender_id=? AND sender_role='doctor') OR (receiver_id=? AND receiver_role='doctor')
        """, (doctor_id, doctor_id)).fetchall()

        conversations = []
        for row in rows:
            pid = row["patient_id"]
            patient = patient_repo.get_patient_by_id(db, pid)
            if not patient:
                continue

            last_msg = db.execute("""
                SELECT message_text, created_at FROM messages
                WHERE (sender_id=? AND sender_role='doctor' AND receiver_id=? AND receiver_role='patient')
                   OR (sender_id=? AND sender_role='patient' AND receiver_id=? AND receiver_role='doctor')
                ORDER BY created_at DESC LIMIT 1
            """, (doctor_id, pid, pid, doctor_id)).fetchone()

            unread = db.execute("""
                SELECT COUNT(*) FROM messages
                WHERE sender_id=? AND sender_role='patient' AND receiver_id=? AND receiver_role='doctor' AND is_read=0
            """, (pid, doctor_id)).fetchone()[0]

            conversations.append({
                "patient_id": pid,
                "patient_name": patient["name"],
                "last_message": last_msg["message_text"] if last_msg else "",
                "last_time": last_msg["created_at"] if last_msg else "",
                "unread_count": unread
            })

        return {"conversations": conversations}
    except Exception as e:
        print("ERROR in doctor_get_conversations:", e)
        return {"conversations": []}


@router.post("/doctor/mark-read")
async def doctor_mark_read(request: Request, db: sqlite3.Connection = Depends(get_db)):
    try:
        data = await request.json()
        doctor_id = data.get("doctor_id")
        patient_id = data.get("patient_id")
        db.execute("""
            UPDATE messages SET is_read=1
            WHERE sender_id=? AND sender_role='patient' AND receiver_id=? AND receiver_role='doctor'
        """, (patient_id, doctor_id))
        db.commit()
        return {"success": True}
    except Exception as e:
        print("ERROR in doctor_mark_read:", e)
        return {"success": False}


# ── GOOGLE MEET ───────────────────────────────────────────────────────────────

import random
import string
from email_service import send_meet_email

def _generate_meet_link() -> str:
    part = lambda n: ''.join(random.choices(string.ascii_lowercase, k=n))
    return f"https://meet.google.com/{part(3)}-{part(4)}-{part(3)}"


@router.post("/doctor/create-meet")
async def create_meet(request: Request, db: sqlite3.Connection = Depends(get_db)):
    try:
        data           = await request.json()
        doctor_id      = data.get("doctor_id")
        patient_id     = data.get("patient_id")
        appointment_id = data.get("appointment_id")
        scheduled_time = data.get("scheduled_time", "")

        if not doctor_id or not patient_id:
            return {"success": False, "message": "Missing fields"}

        meet_link = _generate_meet_link()

        db.execute("""
            INSERT INTO meet_links (doctor_id, patient_id, appointment_id, meet_link, scheduled_time)
            VALUES (?, ?, ?, ?, ?)
        """, (doctor_id, patient_id, appointment_id, meet_link, scheduled_time))
        db.commit()

        # Email patient if they have an email on file
        try:
            patient = patient_repo.get_patient_by_id(db, patient_id)
            doc     = doctor_repo.get_doctor_by_id(db, doctor_id)
            if patient and patient.get("email") and doc:
                send_meet_email(
                    patient["email"], patient["name"],
                    doc["name"], meet_link, scheduled_time
                )
        except Exception as mail_err:
            print("Meet email skipped:", mail_err)

        return {"success": True, "meet_link": meet_link}
    except Exception as e:
        print("ERROR in create_meet:", e)
        return {"success": False, "message": "Could not create meet link."}


@router.get("/doctor/meet-links")
def doctor_meet_links(doctor_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute("""
            SELECT m.*, p.name AS patient_name
            FROM meet_links m
            JOIN patients p ON m.patient_id = p.patient_id
            WHERE m.doctor_id = ?
            ORDER BY m.created_at DESC
        """, (doctor_id,)).fetchall()
        return {"meet_links": [dict(r) for r in rows]}
    except Exception as e:
        print("ERROR in doctor_meet_links:", e)
        return {"meet_links": []}
