import random
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from database import get_db_connection
from models import AddDoctorRequest, UpdateDoctorRequest, UpdatePatientRequest
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def db_error(e):
    print("DB ERROR:", e)
    return JSONResponse({"error": "Database error", "detail": str(e)}, status_code=500)

@router.get("/admin/overview")
def get_admin_overview():
    try:
        conn = get_db_connection()
        p = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        d = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
        a = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        conn.close()
        return {"patients": p, "doctors": d, "appointments": a}
    except Exception as e:
        return db_error(e)

@router.get("/admin/patients")
def get_admin_patients():
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM patients ORDER BY patient_id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return db_error(e)

@router.get("/admin/doctors")
def get_admin_doctors():
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM doctors ORDER BY doctor_id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return db_error(e)

@router.post("/admin/add-doctor")
def add_doctor(req: AddDoctorRequest):
    try:
        conn = get_db_connection()
        if conn.execute("SELECT 1 FROM doctors WHERE doc_id=?", (req.doc_id,)).fetchone():
            conn.close(); return {"success": False, "message": "Already exists"}
        parts = req.name.lower().replace("dr.", "").strip().split()
        email = ".".join(parts) + "@hospital.com"
        phone = "9" + str(random.randint(100000000, 999999999))
        conn.execute("""INSERT INTO doctors (name, department, qualification, experience_years, available_days, available_hours, doc_id, password_hash, email, contact_phone, region)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                     (req.name, req.department, req.qualification, req.experience_years, req.available_days, req.available_hours, req.doc_id, hash_password(req.password), email, phone, req.region))
        conn.commit(); conn.close()
        return {"success": True}
    except Exception as e:
        return db_error(e)

@router.put("/admin/update-doctor")
def update_doctor(req: UpdateDoctorRequest):
    try:
        conn = get_db_connection()
        conn.execute("""UPDATE doctors SET name=?, department=?, qualification=?, experience_years=?, doc_id=?, region=?, available_days=?, available_hours=?, contact_phone=?, email=? WHERE doctor_id=?""",
                     (req.name, req.department, req.qualification, req.experience_years, req.doc_id, req.region, req.available_days, req.available_hours, req.contact_phone, req.email, req.doctor_id))
        conn.commit(); conn.close()
        return {"success": True}
    except Exception as e:
        return db_error(e)

@router.put("/admin/update-patient")
def update_patient(req: UpdatePatientRequest):
    try:
        conn = get_db_connection()
        conn.execute("UPDATE patients SET name=?, age=?, gender=?, phone=?, preferred_language=? WHERE patient_id=?",
                     (req.name, req.age, req.gender, req.phone, req.preferred_language, req.patient_id))
        conn.commit(); conn.close()
        return {"success": True}
    except Exception as e:
        return db_error(e)

@router.get("/admin/appointments")
def get_admin_appointments(patient_id: int = None):
    try:
        conn = get_db_connection()
        sql = """SELECT a.appointment_id AS id, p.name AS patient, d.name AS doctor, d.department, d.region,
                        a.appointment_date AS date, a.appointment_time AS time, a.status, a.reason
                 FROM appointments a
                 JOIN patients p ON a.patient_id = p.patient_id
                 JOIN doctors  d ON a.doctor_id  = d.doctor_id"""
        rows = conn.execute(sql + (" WHERE a.patient_id = ? ORDER BY a.appointment_date DESC" if patient_id else " ORDER BY a.appointment_date DESC"),
                            (patient_id,) if patient_id else ()).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return db_error(e)

@router.get("/admin/ratings")
def get_admin_ratings():
    try:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT p.name AS patient, d.name AS doctor, d.department,
                   a.rating, a.review, a.appointment_date AS date
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors  d ON a.doctor_id  = d.doctor_id
            WHERE a.rating IS NOT NULL
            ORDER BY a.rating ASC, a.appointment_date DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return db_error(e)

@router.post("/admin/leave")
def add_leave(data: dict):
    return {"message": f"Leave recorded for {data.get('name')} on {data.get('date')}"}
