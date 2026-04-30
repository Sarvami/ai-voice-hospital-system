import os
import uuid
import sqlite3
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, FileResponse
from gtts import gTTS
from models import DateRequest, RegionRequest, RateRequest, OtpRequest, VerifyOtpRequest
from voice_service import gt_from_english
from repositories.session_repo import get_session, set_session, delete_session
from passlib.context import CryptContext
from database import get_db
from repositories import patient_repo, doctor_repo, appointment_repo, report_repo
from email_service import generate_otp, send_otp_email, send_cancellation_email
from datetime import datetime, timedelta
from websocket_manager import manager
import asyncio

router = APIRouter()
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")
TEMP_DIR = "temp"

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password[:72], hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

# ── AUTH ──────────────────────────────────────────────────────────────────────

@router.post("/login")
async def login(request: Request, db: sqlite3.Connection = Depends(get_db)):
    try:
        data     = await request.json()
        password = data.get("password", "")
        role     = data.get("role", "patient")

        if role == "admin":
            ADMIN_EMAIL = "admin@gmail.com"
            ADMIN_HASH  = "$2b$12$mgPAyiAist809bcfiCRiZ.vHkExIqX5Jlc316MBU2M2E3Drt2Wwjy"
            if data.get("email", "").strip() == ADMIN_EMAIL and verify_password(password, ADMIN_HASH):
                return {"success": True, "user": {"id": 0, "name": "Admin", "role": "admin"}}
            return {"success": False, "message": "Invalid admin credentials"}

        if role == "patient":
            phone = data.get("phone", "").strip()
            if not phone or not password:
                return {"success": False, "message": "Missing fields"}
            user = patient_repo.get_patient_by_phone(db, phone)
            if not user:
                return {"success": False, "message": "User not found"}
            if not verify_password(password, user["password_hash"]):
                return {"success": False, "message": "Incorrect password"}
            return {"success": True, "user": {
                "id": user["patient_id"], "name": user["name"],
                "phone": user["phone"],
                "preferred_language": user.get("preferred_language") or "en",
                "has_email": bool(user.get("email"))
            }}

        if role == "doctor":
            doc_id = data.get("doctor_id", "").strip()
            if not doc_id or not password:
                return {"success": False, "message": "Missing fields"}
            user = doctor_repo.get_doctor_by_doc_id(db, doc_id)
            if not user:
                return {"success": False, "message": "Doctor not found"}
            if not verify_password(password, user["password_hash"]):
                return {"success": False, "message": "Incorrect password"}
            return {"success": True, "user": {
                "id": user["doctor_id"], "name": user["name"], "role": "doctor"
            }}

        return {"success": False, "message": "Invalid role"}
    except Exception as e:
        print("ERROR in login:", e)
        return {"success": False, "message": "Server error. Please try again."}


@router.post("/register")
async def register_patient(request: Request, db: sqlite3.Connection = Depends(get_db)):
    try:
        data     = await request.json()
        name     = data.get("name", "").strip()
        phone    = data.get("phone", "").strip()
        password = data.get("password", "")
        age      = data.get("age", 0)
        gender   = data.get("gender", "Unknown")
        language = data.get("preferred_language", "en")
        region   = data.get("region", "Unknown")
        email    = data.get("email", "").strip() or None

        if not name or not phone or not password:
            return {"success": False, "message": "Missing fields"}
        if email and ("@" not in email or "." not in email):
            return {"success": False, "message": "Invalid email address"}
        if patient_repo.patient_phone_exists(db, phone):
            return {"success": False, "message": "Phone number already registered"}

        patient_repo.create_patient(db, name, age, gender, phone, language, region, hash_password(password), email)
        return {"success": True}
    except Exception as e:
        print("ERROR in register:", e)
        return {"success": False, "message": "Server error. Please try again."}

# ── APPOINTMENTS ──────────────────────────────────────────────────────────────

@router.get("/patient/appointments")
def patient_appointments(patient_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        return appointment_repo.get_appointments_by_patient(db, patient_id)
    except Exception as e:
        print("ERROR in patient_appointments:", e)
        return []


@router.post("/set-appointment-date")
def set_appointment_date_api(req: DateRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        uid = str(req.patient_id)
        state, data = get_session(uid)
        
        data["doctor_id"] = req.doctor_id
        data["date"] = req.date
        set_session(uid, "waiting_time", data)

        avail_hours = data.get("available_hours", "8:00 AM - 8:00 PM")
        reply = f"Got it, {req.date}. At what time?"
        final = gt_from_english(reply, req.lang) + f" ({avail_hours})"
        out   = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
        gTTS(text=final, lang=req.lang).save(out)
        return {"success": True, "text": final, "audio_url": f"/temp-audio/{os.path.basename(out)}"}
    except Exception as e:
        print("ERROR in set_appointment_date:", e)
        return {"success": False, "message": "Could not set date. Please try again."}


@router.post("/set-region")
def set_region_api(req: RegionRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        uid = str(req.patient_id)
        state, data = get_session(uid)
        data["region"] = req.region
        set_session(uid, state, data)
        patient_repo.update_patient_region(db, req.patient_id, req.region)
        text  = f"Region set to {req.region}."
        final = gt_from_english(text, req.lang)
        out   = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
        gTTS(text=final, lang=req.lang).save(out)
        return {"text": final, "audio_url": f"/temp-audio/{os.path.basename(out)}"}
    except Exception as e:
        print("ERROR in set_region:", e)
        return {"text": "", "audio_url": ""}

# ── RATINGS ───────────────────────────────────────────────────────────────────

@router.post("/patient/rate-appointment")
def rate_appointment(req: RateRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        appt = appointment_repo.get_appointment_by_id(db, req.appointment_id)
        if not appt or appt["status"].lower() != "completed" or appt["rating"]:
            return {"success": False, "message": "Invalid rating request"}

        appointment_repo.set_appointment_rating(db, req.appointment_id, req.rating)
        if req.review:
            appointment_repo.set_appointment_review(db, req.appointment_id, req.review)

        stats = doctor_repo.get_doctor_rating_stats(db, appt["doctor_id"])
        old_r = stats["rating"] or 4.5
        old_c = stats["rating_count"] or 0
        new_c = old_c + 1
        new_r = ((old_r * old_c) + req.rating) / new_c
        doctor_repo.update_doctor_rating(db, appt["doctor_id"], new_r, new_c)
        return {"success": True, "avg": round(new_r, 1)}
    except Exception as e:
        print("ERROR in rate_appointment:", e)
        return {"success": False, "message": "Could not submit rating."}

# ── REPORTS ───────────────────────────────────────────────────────────────────

@router.post("/patient/upload-report")
async def upload_report(
    patient_id: str = Form(...),
    report_type: str = Form(...),
    file: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        allowed = {".pdf", ".jpg", ".jpeg", ".png"}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            return {"success": False, "message": "Invalid file type. Use PDF, JPG, or PNG."}
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            return {"success": False, "message": "File too large. Max 5MB."}
        safe_name = f"{uuid.uuid4()}{ext}"
        with open(os.path.join(REPORTS_DIR, safe_name), "wb") as f:
            f.write(contents)
        report_repo.create_report(db, patient_id, report_type, file.filename, safe_name)
        return {"success": True}
    except Exception as e:
        print("ERROR in upload_report:", e)
        return {"success": False, "message": "Upload failed."}


@router.get("/patient/reports")
def get_patient_reports(patient_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        return {"reports": report_repo.get_reports_by_patient(db, patient_id)}
    except Exception as e:
        print("ERROR in get_patient_reports:", e)
        return {"reports": []}


@router.get("/patient/report-file/{report_id}")
def get_report_file(report_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = report_repo.get_report_by_id(db, report_id)
    if not row:
        return JSONResponse({"error": "Not found"}, status_code=404)
    path = os.path.join(REPORTS_DIR, row["filepath"])
    return FileResponse(path, filename=row["filename"])


@router.delete("/patient/report/{report_id}")
def delete_report(report_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        row = report_repo.get_report_by_id(db, report_id)
        if not row:
            return {"success": False, "message": "Report not found"}
        filepath = os.path.join(REPORTS_DIR, row["filepath"])
        if os.path.exists(filepath):
            os.remove(filepath)
        report_repo.delete_report(db, report_id)
        return {"success": True}
    except Exception as e:
        print("ERROR in delete_report:", e)
        return {"success": False, "message": "Could not delete report."}


@router.get("/doctors/by-region/{region}")
def doctors_by_region(region: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        return doctor_repo.get_doctors_by_region(db, region)
    except Exception as e:
        print("ERROR in doctors_by_region:", e)
        return []

# ── OTP ───────────────────────────────────────────────────────────────────────

@router.post("/send-otp")
async def send_otp(req: OtpRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        user = patient_repo.get_patient_by_phone(db, req.phone)
        if not user:
            return {"success": False, "message": "User not found"}
        if not user.get("email"):
            return {"success": False, "message": "No email registered"}

        otp = generate_otp()
        expiry = (datetime.utcnow() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        patient_repo.set_otp(db, req.phone, otp, expiry)
        
        sent = send_otp_email(user["email"], otp, user["name"])
        if sent:
            return {"success": True, "message": "OTP sent"}
        else:
            return {"success": False, "message": "Failed to deliver OTP email. Please check your email settings."}
    except Exception as e:
        print("ERROR in send_otp:", e)
        return {"success": False, "message": "Could not send OTP. Please try again."}


@router.post("/verify-otp")
async def verify_otp(req: VerifyOtpRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        user = patient_repo.get_patient_by_phone(db, req.phone)
        if not user:
            return {"success": False, "message": "User not found"}

        stored_otp    = user.get("otp")
        stored_expiry = user.get("otp_expiry")

        if not stored_otp or not stored_expiry:
            return {"success": False, "message": "No OTP requested"}

        if datetime.utcnow() > datetime.strptime(stored_expiry, "%Y-%m-%d %H:%M:%S"):
            return {"success": False, "message": "Invalid or expired OTP"}

        if req.otp.strip() != stored_otp:
            return {"success": False, "message": "Invalid or expired OTP"}

        patient_repo.clear_otp(db, req.phone)
        return {"success": True, "user": {
            "id": user["patient_id"], "name": user["name"],
            "phone": user["phone"],
            "preferred_language": user.get("preferred_language") or "en",
            "has_email": True
        }}
    except Exception as e:
        print("ERROR in verify_otp:", e)
        return {"success": False, "message": "Server error. Please try again."}

# ── CANCEL APPOINTMENT ────────────────────────────────────────────────────────

@router.post("/patient/cancel-appointment/{appointment_id}")
def cancel_appointment(appointment_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        appt = appointment_repo.get_appointment_by_id(db, appointment_id)
        if not appt:
            return {"success": False, "message": "Appointment not found"}
        if appt["status"].lower() == "cancelled":
            return {"success": False, "message": "Already cancelled"}

        db.execute(
            "UPDATE appointments SET status='Cancelled' WHERE appointment_id=?",
            (appointment_id,)
        )
        db.commit()

        # Send cancellation email if patient has one — fail silently
        try:
            patient = patient_repo.get_patient_by_id(db, appt["patient_id"])
            if patient and patient.get("email"):
                doc = doctor_repo.get_doctor_by_id(db, appt["doctor_id"])
                doc_name = doc["name"] if doc else "Doctor"
                send_cancellation_email(
                    patient["email"], patient["name"], doc_name,
                    appt.get("appointment_date", ""), appt.get("appointment_time", ""),
                    appt.get("reason", "N/A")
                )
        except Exception as mail_err:
            print("Cancellation email skipped:", mail_err)

        return {"success": True}
    except Exception as e:
        print("ERROR in cancel_appointment:", e)
        return {"success": False, "message": "Could not cancel appointment."}


# ── MESSAGING ─────────────────────────────────────────────────────────────────

@router.post("/patient/send-message")
async def patient_send_message(request: Request, db: sqlite3.Connection = Depends(get_db)):
    try:
        data = await request.json()
        patient_id = data.get("patient_id")
        doctor_id = data.get("doctor_id")
        appointment_id = data.get("appointment_id")
        message = data.get("message", "").strip()

        if patient_id is None or doctor_id is None or not message:
            return {"success": False, "message": "Missing fields (patient_id, doctor_id, or message)"}

        receiver_role = 'admin' if doctor_id == 0 else 'doctor'

        db.execute("""
            INSERT INTO messages (sender_id, sender_role, receiver_id, receiver_role, appointment_id, message_text)
            VALUES (?, 'patient', ?, ?, ?, ?)
        """, (patient_id, doctor_id, receiver_role, appointment_id, message))
        db.commit()
        msg_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Notify receiver via WebSocket
        asyncio.create_task(manager.send_personal_message(
            {"type": "new_message", "message_id": msg_id},
            receiver_role,
            doctor_id
        ))
        
        return {"success": True, "message_id": msg_id}
    except Exception as e:
        print("ERROR in patient_send_message:", e)
        return {"success": False, "message": "Could not send message."}


@router.get("/patient/messages")
def patient_get_messages(patient_id: int, doctor_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute("""
            SELECT message_id, sender_id, sender_role, message_text, is_read, created_at
            FROM messages
            WHERE ((sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?))
            ORDER BY created_at ASC
        """, (patient_id, doctor_id, doctor_id, patient_id)).fetchall()
        return {"messages": [dict(r) for r in rows]}
    except Exception as e:
        print("ERROR in patient_get_messages:", e)
        return {"messages": []}


@router.get("/patient/conversations")
def patient_get_conversations(patient_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute("""
            SELECT DISTINCT
                CASE WHEN sender_role='patient' THEN receiver_id ELSE sender_id END AS doctor_id
            FROM messages
            WHERE (sender_id=? AND sender_role='patient') OR (receiver_id=? AND receiver_role='patient')
        """, (patient_id, patient_id)).fetchall()

        conversations = []
        for row in rows:
            doc_id = row["doctor_id"]
            doc_name = ""
            
            if doc_id == 0:
                doc_name = "Hospital Admin"
            else:
                doc = doctor_repo.get_doctor_by_id(db, doc_id)
                if not doc: continue
                doc_name = doc["name"]

            last_msg = db.execute("""
                SELECT message_text, created_at, sender_role
                FROM messages
                WHERE (sender_id=? AND sender_role='patient' AND receiver_id=? AND receiver_role IN ('doctor', 'admin'))
                   OR (sender_id=? AND sender_role IN ('doctor', 'admin') AND receiver_id=? AND receiver_role='patient')
                ORDER BY created_at DESC LIMIT 1
            """, (patient_id, doc_id, doc_id, patient_id)).fetchone()

            unread = db.execute("""
                SELECT COUNT(*) FROM messages
                WHERE sender_id=? AND sender_role IN ('doctor', 'admin') AND receiver_id=? AND receiver_role='patient' AND is_read=0
            """, (doc_id, patient_id)).fetchone()[0]

            conversations.append({
                "doctor_id": doc_id,
                "doctor_name": doc_name,
                "last_message": last_msg["message_text"] if last_msg else "",
                "last_time": last_msg["created_at"] if last_msg else "",
                "unread_count": unread
            })

        return {"conversations": conversations}
    except Exception as e:
        print("ERROR in patient_get_conversations:", e)
        return {"conversations": []}


@router.post("/patient/mark-read")
async def patient_mark_read(request: Request, db: sqlite3.Connection = Depends(get_db)):
    try:
        data = await request.json()
        patient_id = data.get("patient_id")
        doctor_id = data.get("doctor_id")
        db.execute("""
            UPDATE messages SET is_read=1
            WHERE sender_id=? AND sender_role IN ('doctor', 'admin') AND receiver_id=? AND receiver_role='patient'
        """, (doctor_id, patient_id))
        db.commit()
        return {"success": True}
    except Exception as e:
        print("ERROR in patient_mark_read:", e)
        return {"success": False}


# ── MEET LINKS ────────────────────────────────────────────────────────────────

@router.get("/patient/meet-links")
def patient_meet_links(patient_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute("""
            SELECT m.*, d.name AS doctor_name
            FROM meet_links m
            JOIN doctors d ON m.doctor_id = d.doctor_id
            WHERE m.patient_id = ?
            ORDER BY m.created_at DESC
        """, (patient_id,)).fetchall()
        return {"meet_links": [dict(r) for r in rows]}
    except Exception as e:
        print("ERROR in patient_meet_links:", e)
        return {"meet_links": []}

@router.get("/patient/active-alerts")
def get_active_alerts(patient_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute(
            "SELECT * FROM emergency_alerts WHERE patient_id = ? AND status = 'Active' ORDER BY created_at DESC",
            (patient_id,)
        ).fetchall()
        return {"alerts": [dict(r) for r in rows]}
    except Exception as e:
        return {"alerts": []}

@router.post("/patient/dismiss-alert/{alert_id}")
def dismiss_alert(alert_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute("UPDATE emergency_alerts SET status = 'Resolved' WHERE id = ?", (alert_id,))
        db.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False}
