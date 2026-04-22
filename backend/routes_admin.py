import random
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from models import AddDoctorRequest, UpdateDoctorRequest, UpdatePatientRequest
from passlib.context import CryptContext
from repositories import patient_repo, doctor_repo, appointment_repo

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return pwd_context.hash(p[:72])

def db_error(e):
    print("DB ERROR:", e)
    return JSONResponse({"error": "Database error", "detail": str(e)}, status_code=500)

@router.get("/admin/overview")
def get_admin_overview():
    try:
        return appointment_repo.get_overview_counts()
    except Exception as e:
        return db_error(e)

@router.get("/admin/patients")
def get_admin_patients():
    try:
        return patient_repo.get_all_patients()
    except Exception as e:
        return db_error(e)

@router.get("/admin/doctors")
def get_admin_doctors():
    try:
        return doctor_repo.get_all_doctors()
    except Exception as e:
        return db_error(e)

@router.post("/admin/add-doctor")
def add_doctor(req: AddDoctorRequest):
    try:
        if doctor_repo.doc_id_exists(req.doc_id):
            return {"success": False, "message": "Doctor ID already exists"}
        parts = req.name.lower().replace("dr.", "").strip().split()
        email = ".".join(parts) + "@hospital.com"
        phone = "9" + str(random.randint(100000000, 999999999))
        doctor_repo.create_doctor(
            req.name, req.department, req.qualification, req.experience_years,
            req.available_days, req.available_hours, req.doc_id,
            hash_password(req.password), email, phone, req.region
        )
        return {"success": True}
    except Exception as e:
        return db_error(e)

@router.put("/admin/update-doctor")
def update_doctor(req: UpdateDoctorRequest):
    try:
        doctor_repo.update_doctor(
            req.doctor_id, req.name, req.department, req.qualification,
            req.experience_years, req.doc_id, req.region, req.available_days,
            req.available_hours, req.contact_phone, req.email
        )
        return {"success": True}
    except Exception as e:
        return db_error(e)

@router.put("/admin/update-patient")
def update_patient(req: UpdatePatientRequest):
    try:
        patient_repo.update_patient(
            req.patient_id, req.name, req.age, req.gender,
            req.phone, req.preferred_language
        )
        return {"success": True}
    except Exception as e:
        return db_error(e)

@router.get("/admin/appointments")
def get_admin_appointments(patient_id: int = None):
    try:
        return appointment_repo.get_all_appointments(patient_id)
    except Exception as e:
        return db_error(e)

@router.get("/admin/ratings")
def get_admin_ratings():
    try:
        return appointment_repo.get_all_ratings()
    except Exception as e:
        return db_error(e)

@router.post("/admin/leave")
def add_leave(data: dict):
    return {"message": f"Leave recorded for {data.get('name')} on {data.get('date')}"}
