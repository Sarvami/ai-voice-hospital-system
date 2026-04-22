import sqlite3
from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from datetime import date
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
