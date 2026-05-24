import csv
import io
import random
import sqlite3
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from models import AddDoctorRequest, UpdateDoctorRequest, UpdatePatientRequest, MessageRequest, AnnouncementBroadcast
from passlib.context import CryptContext
from database import get_db
from repositories import patient_repo, doctor_repo, appointment_repo
from repositories import analytics_repo
from audit_service import log_audit, get_audit_logs
from push_service import send_push_to_all
from websocket_manager import manager
import asyncio

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return pwd_context.hash(p[:72])

def db_error(e):
    print("DB ERROR:", e)
    return JSONResponse({"success": False, "message": f"Database error: {str(e)}"}, status_code=500)


@router.get("/overview")
def get_admin_overview(db: sqlite3.Connection = Depends(get_db)):
    try:
        return appointment_repo.get_overview_counts(db)
    except Exception as e:
        return db_error(e)


@router.get("/analytics")
def get_analytics(db: sqlite3.Connection = Depends(get_db)):
    try:
        return {
            "appointments_per_day": analytics_repo.get_appointments_per_day(db),
            "by_department": analytics_repo.get_appointments_by_department(db),
            "patients_by_region": analytics_repo.get_patients_by_region(db),
        }
    except Exception as e:
        return db_error(e)


@router.get("/audit-log")
def admin_audit_log(limit: int = 200, db: sqlite3.Connection = Depends(get_db)):
    try:
        return get_audit_logs(db, min(limit, 500))
    except Exception as e:
        return db_error(e)


@router.get("/announcements")
def list_announcements(db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute(
            "SELECT id, title, message, created_by, created_at FROM announcements ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        return db_error(e)


@router.post("/announcements/broadcast")
async def broadcast_announcement(req: AnnouncementBroadcast, db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute(
            "INSERT INTO announcements (title, message, created_by) VALUES (?, ?, ?)",
            (req.title.strip(), req.message.strip(), req.actor),
        )
        ann_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.commit()
        log_audit(db, req.actor, "broadcast", "announcement", str(ann_id), {"title": req.title})

        push_count = send_push_to_all(db, req.title, req.message)

        rows = db.execute("SELECT patient_id FROM patients").fetchall()
        for row in rows:
            pid = row["patient_id"]
            asyncio.create_task(manager.send_personal_message(
                {"type": "announcement", "id": ann_id, "title": req.title, "message": req.message},
                "patient",
                pid,
            ))

        return {"success": True, "id": ann_id, "push_sent": push_count, "patients_notified": len(rows)}
    except Exception as e:
        return db_error(e)


@router.post("/doctors/bulk-import")
async def bulk_import_doctors(file: UploadFile = File(...), db: sqlite3.Connection = Depends(get_db)):
    try:
        raw = await file.read()
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        required = {"name", "department", "qualification", "experience_years", "available_days", "doc_id", "password", "region"}
        created, skipped, errors = 0, 0, []

        for i, row in enumerate(reader, start=2):
            keys = {k.strip().lower().replace(" ", "_") for k in row.keys()}
            row_norm = {k.strip().lower().replace(" ", "_"): (v or "").strip() for k, v in row.items()}
            if not required.issubset(set(row_norm.keys())):
                errors.append(f"Row {i}: missing columns (need {', '.join(sorted(required))})")
                skipped += 1
                continue
            doc_id = row_norm["doc_id"]
            if doctor_repo.doc_id_exists(db, doc_id):
                errors.append(f"Row {i}: doc_id {doc_id} already exists")
                skipped += 1
                continue
            parts = row_norm["name"].lower().replace("dr.", "").strip().split()
            email = row_norm.get("email") or (".".join(parts) + "@hospital.com")
            phone = row_norm.get("phone") or ("9" + str(random.randint(100000000, 999999999)))
            hours = row_norm.get("available_hours") or "8:00 AM - 8:00 PM"
            try:
                exp = int(row_norm["experience_years"])
            except ValueError:
                errors.append(f"Row {i}: invalid experience_years")
                skipped += 1
                continue
            doctor_repo.create_doctor(
                db, row_norm["name"], row_norm["department"], row_norm["qualification"], exp,
                row_norm["available_days"], hours, doc_id,
                hash_password(row_norm["password"]), email, phone, row_norm["region"],
            )
            log_audit(db, "admin", "create", "doctor", doc_id, {"name": row_norm["name"], "source": "bulk_csv"})
            created += 1

        return {"success": True, "created": created, "skipped": skipped, "errors": errors[:20]}
    except Exception as e:
        return db_error(e)


@router.get("/patients")
def get_admin_patients(db: sqlite3.Connection = Depends(get_db)):
    try:
        return patient_repo.get_all_patients(db)
    except Exception as e:
        return db_error(e)


@router.delete("/patients/{patient_id}")
def delete_patient_admin(patient_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        p = patient_repo.get_patient_by_id(db, patient_id)
        if not p:
            return {"success": False, "message": "Patient not found"}
        ok = patient_repo.delete_patient(db, patient_id)
        if ok:
            log_audit(db, "admin", "delete", "patient", str(patient_id), {"name": p.get("name")})
        return {"success": ok}
    except Exception as e:
        return db_error(e)


@router.get("/doctors")
def get_admin_doctors(db: sqlite3.Connection = Depends(get_db)):
    try:
        return doctor_repo.get_all_doctors(db)
    except Exception as e:
        return db_error(e)

@router.post("/add-doctor")
def add_doctor(req: AddDoctorRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        if doctor_repo.doc_id_exists(db, req.doc_id):
            return {"success": False, "message": "Doctor ID already exists"}
        parts = req.name.lower().replace("dr.", "").strip().split()
        email = ".".join(parts) + "@hospital.com"
        phone = "9" + str(random.randint(100000000, 999999999))
        doctor_repo.create_doctor(
            db, req.name, req.department, req.qualification, req.experience_years,
            req.available_days, req.available_hours, req.doc_id,
            hash_password(req.password), email, phone, req.region
        )
        log_audit(db, "admin", "create", "doctor", req.doc_id, {"name": req.name})
        return {"success": True}
    except Exception as e:
        return db_error(e)

@router.put("/update-doctor")
def update_doctor(req: UpdateDoctorRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        doctor_repo.update_doctor(
            db, req.doctor_id, req.name, req.department, req.qualification,
            req.experience_years, req.doc_id, req.region, req.available_days,
            req.available_hours, req.contact_phone, req.email
        )
        log_audit(db, "admin", "update", "doctor", str(req.doctor_id), {"name": req.name})
        return {"success": True}
    except Exception as e:
        return db_error(e)

@router.put("/update-patient")
def update_patient(req: UpdatePatientRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        patient_repo.update_patient(
            db, req.patient_id, req.name, req.age,
            req.gender, req.phone, req.preferred_language, req.email
        )
        log_audit(db, "admin", "update", "patient", str(req.patient_id), {"name": req.name})
        return {"success": True}
    except Exception as e:
        return db_error(e)

@router.get("/appointments")
def get_admin_appointments(patient_id: int = None, db: sqlite3.Connection = Depends(get_db)):
    try:
        return appointment_repo.get_all_appointments(db, patient_id)
    except Exception as e:
        return db_error(e)

@router.get("/ratings")
def get_admin_ratings(db: sqlite3.Connection = Depends(get_db)):
    try:
        return appointment_repo.get_all_ratings(db)
    except Exception as e:
        return db_error(e)

@router.post("/leave")
def add_leave(data: dict, db: sqlite3.Connection = Depends(get_db)):
    log_audit(db, "admin", "leave", "staff", data.get("name"), {"date": data.get("date")})
    return {"message": f"Leave recorded for {data.get('name')} on {data.get('date')}"}

@router.post("/send-message")
def admin_send_message(req: MessageRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute("""
            INSERT INTO messages (sender_id, sender_role, receiver_id, receiver_role, message_text)
            VALUES (?, ?, ?, ?, ?)
        """, (req.sender_id, req.sender_role, req.receiver_id, req.receiver_role, req.message_text))
        db.commit()
        msg_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        asyncio.create_task(manager.send_personal_message(
            {"type": "new_message", "message_id": msg_id},
            req.receiver_role,
            req.receiver_id
        ))
        
        return {"success": True, "message": "Message sent successfully"}
    except Exception as e:
        return db_error(e)

@router.get("/conversations")
def get_admin_conversations(db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute("""
            SELECT DISTINCT 
                CASE WHEN sender_role='admin' THEN receiver_id ELSE sender_id END AS patient_id
            FROM messages
            WHERE sender_role='admin' OR receiver_role='admin'
        """).fetchall()
        
        conversations = []
        for row in rows:
            p_id = row["patient_id"]
            patient = patient_repo.get_patient_by_id(db, p_id)
            if not patient: continue
            
            last_msg = db.execute("""
                SELECT message_text, created_at
                FROM messages
                WHERE (sender_id=0 AND receiver_id=?) OR (sender_id=? AND receiver_id=0)
                ORDER BY created_at DESC LIMIT 1
            """, (p_id, p_id)).fetchone()
            
            conversations.append({
                "patient_id": p_id,
                "patient_name": patient["name"],
                "last_message": last_msg["message_text"] if last_msg else "",
                "last_time": last_msg["created_at"] if last_msg else ""
            })
        return conversations
    except Exception as e:
        return db_error(e)

@router.get("/messages/{patient_id}")
def get_admin_messages(patient_id: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute("""
            SELECT message_id, sender_id, sender_role, message_text, created_at
            FROM messages
            WHERE (sender_id=0 AND receiver_id=?) OR (sender_id=? AND receiver_id=0)
            ORDER BY created_at ASC
        """, (patient_id, patient_id)).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        return db_error(e)
