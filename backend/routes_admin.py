import random
import sqlite3
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from models import AddDoctorRequest, UpdateDoctorRequest, UpdatePatientRequest, MessageRequest
from passlib.context import CryptContext
from database import get_db
from repositories import patient_repo, doctor_repo, appointment_repo

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

@router.get("/patients")
def get_admin_patients(db: sqlite3.Connection = Depends(get_db)):
    try:
        return patient_repo.get_all_patients(db)
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
        return {"success": True}
    except Exception as e:
        return db_error(e)

@router.put("/update-patient")
def update_patient(req: UpdatePatientRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        patient_repo.update_patient(
            db, req.patient_id, req.name, req.age,
            req.gender, req.phone, req.preferred_language
        )
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
def add_leave(data: dict):
    return {"message": f"Leave recorded for {data.get('name')} on {data.get('date')}"}
@router.post("/send-message")
def admin_send_message(req: MessageRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute("""
            INSERT INTO messages (sender_id, sender_role, receiver_id, receiver_role, message_text)
            VALUES (?, ?, ?, ?, ?)
        """, (req.sender_id, req.sender_role, req.receiver_id, req.receiver_role, req.message_text))
        db.commit()
        return {"success": True, "message": "Message sent successfully"}
    except Exception as e:
        return db_error(e)
@router.get("/conversations")
def get_admin_conversations(db: sqlite3.Connection = Depends(get_db)):
    try:
        # Get unique patients that have messages with admin (ID 0)
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
