import os
import uuid
import random
from fastapi import APIRouter, Request, JSONResponse
from gtts import gTTS
from database import get_db_connection
from models import DateRequest, RegionRequest, RateRequest
from voice_service import (
    user_state, user_data, gt_from_english, 
    get_or_create_patient, get_doctors_by_department
)
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TEMP_DIR = "temp"

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password[:72], hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

@router.post("/login")
async def login(request: Request):
    data     = await request.json()
    password = data.get("password", "")
    role     = data.get("role", "patient")

    if role == "admin":
        ADMIN_EMAIL = "admin@gmail.com"
        ADMIN_HASH  = "$2b$12$D4FWvBXmgrJLpN.JmmCnLexIzMOchI/56oQUdn3JQGaL8knIDoI.."
        email = data.get("email", "").strip()
        if email == ADMIN_EMAIL and verify_password(password, ADMIN_HASH):
            return {"success": True, "user": {"id": 0, "name": "Admin", "role": "admin"}}
        return {"success": False, "message": "Invalid admin credentials"}

    phone = data.get("phone", "").strip()
    if role == "doctor":
        phone = data.get("doctor_id", "").strip()

    if not phone or not password:
        return {"success": False, "message": "Missing fields"}

    conn = get_db_connection()
    if role == "patient":
        user = conn.execute("SELECT * FROM patients WHERE phone=?", (phone,)).fetchone()
        conn.close()
        if not user: return {"success": False, "message": "User not found"}
        if not verify_password(password, user["password_hash"]):
            return {"success": False, "message": "Incorrect password"}
        return {
            "success": True,
            "user": {
                "id": user["patient_id"],
                "name": user["name"],
                "phone": user["phone"],
                "preferred_language": user["preferred_language"] or "en"
            }
        }
    conn.close()
    return {"success": False, "message": "Invalid role or handled elsewhere"}

@router.post("/register")
async def register_patient(request: Request):
    data = await request.json()
    name, age, phone = data.get("name", "").strip(), data.get("age", 0), data.get("phone", "").strip()
    password, language = data.get("password", ""), data.get("preferred_language", "en")
    gender, region = data.get("gender", "Unknown"), data.get("region", "Unknown")

    if not name or not phone or not password:
        return {"success": False, "message": "Missing fields"}

    conn = get_db_connection()
    if conn.execute("SELECT 1 FROM patients WHERE phone=?", (phone,)).fetchone():
        conn.close()
        return {"success": False, "message": "Already exists"}
    
    conn.execute("INSERT INTO patients (name, age, gender, phone, preferred_language, region, password_hash) VALUES (?,?,?,?,?,?,?)",
                 (name, age, gender, phone, language, region, hash_password(password)))
    conn.commit(); conn.close()
    return {"success": True}

@router.get("/patient/appointments")
def patient_appointments(patient_id: int):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT a.appointment_id, d.name AS doctor, d.email, d.contact_phone, d.region,
               a.appointment_date AS date, a.appointment_time AS time, a.status, a.reason, a.rating
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC
    """, (patient_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/set-appointment-date")
def set_appointment_date_api(req: DateRequest):
    user_id = req.patient_id
    if user_id not in user_state:
        user_state[user_id] = "waiting_time"
        user_data[user_id] = {"doctor_id": req.doctor_id, "date": req.date}
    else:
        user_state[user_id] = "waiting_time"
        user_data[user_id]["date"] = req.date
        if req.doctor_id: user_data[user_id]["doctor_id"] = req.doctor_id

    avail_hours = user_data[user_id].get("available_hours", "8:00 AM - 8:00 PM")
    reply = f"Got it, {req.date}. At what time?"
    final = gt_from_english(reply, req.lang) + f" ({avail_hours})"
    out = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=final, lang=req.lang).save(out)
    return {"success": True, "text": final, "audio_url": f"/temp-audio/{os.path.basename(out)}"}

@router.post("/set-region")
def set_region_api(req: RegionRequest):
    if req.patient_id not in user_data: user_data[req.patient_id] = {}
    user_data[req.patient_id]["region"] = req.region
    conn = get_db_connection()
    conn.execute("UPDATE patients SET region = ? WHERE patient_id = ?", (req.region, req.patient_id))
    conn.commit(); conn.close()
    
    text = f"Region set to {req.region}."
    final = gt_from_english(text, req.lang)
    out = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=final, lang=req.lang).save(out)
    return {"text": final, "audio_url": f"/temp-audio/{os.path.basename(out)}"}

@router.post("/patient/rate-appointment")
def rate_appointment(req: RateRequest):
    conn = get_db_connection()
    appt = conn.execute("SELECT * FROM appointments WHERE appointment_id=?", (req.appointment_id,)).fetchone()
    if not appt or appt["status"] != "Completed" or appt["rating"]:
        conn.close(); return {"success": False, "message": "Invalid rating request"}
    
    conn.execute("UPDATE appointments SET rating = ? WHERE appointment_id = ?", (req.rating, req.appointment_id))
    did = appt["doctor_id"]
    doc = conn.execute("SELECT rating, rating_count FROM doctors WHERE doctor_id=?", (did,)).fetchone()
    old_r, old_c = doc["rating"] or 4.5, doc["rating_count"] or 0
    new_c = old_c + 1
    new_r = ((old_r * old_c) + req.rating) / new_c
    conn.execute("UPDATE doctors SET rating = ?, rating_count = ? WHERE doctor_id = ?", (new_r, new_c, did))
    conn.commit(); conn.close()
    return {"success": True, "avg": round(new_r, 1)}

@router.get("/doctors/by-region/{region}")
def doctors_by_region(region: str):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM doctors WHERE region = ?", (region,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
