from database import SessionLocal, Patient
from googletrans import Translator
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from gtts import gTTS
import requests
import uuid
import os
import time
import difflib
import re
import sqlite3
import dateparser

from passlib.context import CryptContext
from pydantic import BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password[:72], hashed)

# ------------------ SETUP ------------------

translator = Translator()

load_dotenv()
API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

supported = ["en", "hi", "mr"]

MAX_STT_WAIT = 30
STT_POLL_INTERVAL = 2

# ------------------ DB CONNECTION ------------------
# FIX 1: get_db_connection was never defined — added here

DB_PATH = "../database/hospital.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ------------------ GOOGLETRANS ------------------

def gt_to_english(text: str) -> str:
    try:
        return translator.translate(text, dest="en").text
    except Exception:
        return text  # fallback: return original if translation fails

def gt_from_english(text: str, target_lang: str) -> str:
    if target_lang == "en":
        return text
    try:
        return translator.translate(text, dest=target_lang).text
    except Exception:
        return text  # fallback: return English if translation fails


# ------------------ MEMORY ------------------

user_state = {}
user_data = {}

# ------------------ DATA ------------------

problem_map = {
    "chest pain": "cardiology", "heart pain": "cardiology",
    "heart": "cardiology", "chest": "cardiology",
    "headache": "neurology", "migraine": "neurology", "seizure": "neurology",
    "fever": "general", "cold": "general", "cough": "general",
    "pain": "general", "ache": "general", "checkup": "general",
    "regular": "general", "routine": "general",
    "ear pain": "ent", "ear": "ent", "hearing": "ent",
    "tooth pain": "dentist", "tooth": "dentist", "teeth": "dentist", "dental": "dentist",
    "bone": "orthopedics", "joint": "orthopedics", "knee": "orthopedics",
    "back pain": "orthopedics", "fracture": "orthopedics",
    "pregnancy": "gynecology", "periods": "gynecology",
    "skin": "dermatology", "rash": "dermatology", "acne": "dermatology",
    "child": "pediatrics", "baby": "pediatrics", "kids": "pediatrics",
    "eye": "ophthalmology", "vision": "ophthalmology", "sight": "ophthalmology",
}

# ------------------ DATABASE FUNCTIONS ------------------

def get_doctors_by_department(dept):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM doctors WHERE LOWER(department)=LOWER(?)", (dept,))
    doctors = [row[0] for row in cursor.fetchall()]
    conn.close()
    return doctors

def find_doctor_by_name(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors WHERE LOWER(name)=?", (name.lower(),))
    doctor = cursor.fetchone()
    conn.close()
    return dict(doctor) if doctor else None

def get_or_create_patient(name, phone, language="en"):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients WHERE phone=?", (phone,))
    patient = cursor.fetchone()

    if patient:
        conn.close()
        return dict(patient)

    cursor.execute("""
        INSERT INTO patients (name, age, gender, phone, preferred_language)
        VALUES (?, ?, ?, ?, ?)
    """, (name, 30, "Unknown", phone, language))

    pid = cursor.lastrowid
    cursor.execute("SELECT * FROM patients WHERE patient_id=?", (pid,))
    new_patient = cursor.fetchone()

    conn.commit()
    conn.close()
    return dict(new_patient)

def create_appointment(pid, did, date, time_str, reason, language):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO appointments
        (patient_id, doctor_id, appointment_date, appointment_time,
         status, reason, booking_source, language_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (pid, did, date, time_str, "Booked", reason, "voice", language))

    aid = cursor.lastrowid
    conn.commit()
    conn.close()
    return aid

# ------------------ STT ------------------

def speech_to_text(audio_path):
    headers = {"authorization": API_KEY}

    with open(audio_path, "rb") as f:
        upload = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=f
        )

    audio_url = upload.json()["upload_url"]

    transcript = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json={"audio_url": audio_url}
    )

    tid = transcript.json()["id"]
    start_time = time.time()

    while True:
        res = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{tid}",
            headers=headers
        )

        status = res.json()["status"]

        if status == "completed":
            return res.json()["text"]

        if status == "error":
            raise Exception("STT failed")

        if time.time() - start_time > MAX_STT_WAIT:
            raise TimeoutError("STT timeout")

        time.sleep(STT_POLL_INTERVAL)

# ------------------ LOGIC ------------------

def fuzzy_match(text, keywords):
    words = text.lower().split()
    for word in words:
        matches = difflib.get_close_matches(word, keywords, 1, 0.7)
        if matches:
            return matches[0]
    return None

def generate_reply(text, user_id="user1", lang="en"):
    text = text.lower().strip()
    if "department" in text and ("which" in text or "what" in text or "belong" in text):
     for doc in ["mehta", "sharma", "rao", "shah",
                "desai", "gupta", "iyer", "malhotra",
                "bose", "chandra", "murthy", "menon",
                "sinha", "pandey", "hegde", "reddy"]:
        if doc in text:
            conn = get_db_connection()
            result = conn.execute(
                "SELECT name, department FROM doctors WHERE LOWER(name) LIKE ?",
                (f"%{doc}%",)
            ).fetchone()
            conn.close()
            if result:
                return f"{result['name']} belongs to the {result['department']} department."
     return "Sorry, I couldn't find that doctor."


    if user_id not in user_state:
        conn = get_db_connection()
        patient = conn.execute("SELECT * FROM patients WHERE patient_id=?", (user_id,)).fetchone()
        conn.close()
        user_data[user_id] = {}
        if patient:
            user_data[user_id]["name"] = patient["name"]
            user_data[user_id]["phone"] = patient["phone"]
            user_data[user_id]["patient_id"] = patient["patient_id"]
        user_state[user_id] = "idle"  # ← inside the if block now

    state = user_state[user_id]

    if state == "idle":
        if any(word in text for word in ["appointment", "book", "doctor", "consult"]):
            user_state[user_id] = "waiting_problem"
            return "What problem are you facing? You can also say regular checkup."
        else:
            return "Say 'book appointment' to get started."

    if state == "waiting_problem":
        matched_dept = None
        for key, dept in problem_map.items():
            if key in text:
                matched_dept = dept
                break
        if not matched_dept:
            # try fuzzy match as fallback
            match = fuzzy_match(text, list(problem_map.keys()))
            if match:
                matched_dept = problem_map[match]

        if matched_dept:
            user_data[user_id]["dept"] = matched_dept
            doctors = get_doctors_by_department(matched_dept)
            if not doctors:
                return "Sorry, no doctors available for that department right now."
            user_data[user_id]["available_doctors"] = doctors
            user_state[user_id] = "waiting_doctor"
            return f"Available doctors: {', '.join(doctors)}. Any preference?"

        return "Sorry, I didn't catch that. Please describe your problem."

    if state == "waiting_doctor":
        # FIX 3: Actually try to match what the user said to a doctor name
        available = user_data[user_id].get("available_doctors", [])
        chosen = None

        for doc in available:
            if doc.lower() in text or any(part in text for part in doc.lower().split()):
                chosen = doc
                break

        # fallback: pick first doctor if no match
        if not chosen and available:
            chosen = available[0]

        info = find_doctor_by_name(chosen)
        if not info:
            return "Could not find that doctor. Please try again."

        user_data[user_id]["doctor"] = chosen
        user_data[user_id]["doctor_id"] = info["doctor_id"]
        user_state[user_id] = "waiting_date"
        return f"Okay, {chosen}. On which date would you like the appointment?"

    if state == "waiting_date":
     parsed = dateparser.parse(text, settings={
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": __import__("datetime").datetime.now()
     })
     if not parsed:
        # try extracting just numbers and month names
        import re
        cleaned = re.sub(r"(i would like|an appointment on|appointment|please|book|schedule|chahungi|chahta|chahiye|mujhe|ko)", "", text).strip()
        parsed = dateparser.parse(cleaned, settings={"PREFER_DATES_FROM": "future"})
    
     if parsed:
        user_data[user_id]["date"] = parsed.strftime("%d %B %Y")
        user_state[user_id] = "waiting_time"
        return f"Got it, {user_data[user_id]['date']}. At what time?"
     else:
        return "Sorry, I didn't catch the date. Please say just the date, like 'March 23rd' or 'tomorrow'."

    if state == "waiting_time":
     parsed = dateparser.parse(text, settings={"PREFER_DATES_FROM": "future"})
     if parsed:
        user_data[user_id]["time"] = parsed.strftime("%I:%M %p")  # e.g. "11:00 AM"
        user_state[user_id] = "confirming"
        d = user_data[user_id]
        return f"Confirm appointment with {d['doctor']} on {d['date']} at {d['time']}?"
    else:
        return "Sorry, I didn't catch the time. Please say it again, like '11 AM' or '3 in the afternoon'."

    if state == "confirming":
        if "yes" in text or "confirm" in text or "ok" in text:
            d = user_data[user_id]
            # FIX 4: Pass actual language instead of hardcoded "en"
            patient = get_or_create_patient(d["name"], d["phone"], lang)

            aid = create_appointment(
                patient["patient_id"],
                d["doctor_id"],
                d["date"],
                d["time"],
                d["dept"],
                lang  # ← actual language now used
            )

            user_state[user_id] = "idle"
            user_data[user_id] = {}
            return f"Appointment confirmed. Your booking ID is {aid}."

        elif "no" in text or "cancel" in text:
            user_state[user_id] = "idle"
            user_data[user_id] = {}
            return "Appointment cancelled. Say 'book appointment' to start again."

        return "Please say yes to confirm or no to cancel."

    return "Sorry, I didn't understand. Please try again."

# ------------------ MAIN API ------------------

@app.post("/process-audio")
async def process_audio(
    audio: UploadFile = File(...),
    lang: str = Form(...),
    patient_id: int = Form(...)
):
    path = f"{TEMP_DIR}/{uuid.uuid4()}.wav"

    with open(path, "wb") as f:
        f.write(await audio.read())

    try:
        original = speech_to_text(path)
        english = gt_to_english(original)
        print(f"ORIGINAL: {original}")
        print(f"TRANSLATED: {english}")
        print(f"USER STATE: {user_state.get(str(patient_id), 'NOT FOUND')}")
        reply = generate_reply(english, user_id=str(patient_id), lang=lang)
        print(f"REPLY: {reply}")
        final = gt_from_english(reply, lang)

    except TimeoutError:
        final = "Sorry, the system is taking too long. Please try again."

    except Exception as e:
        print("ERROR in process_audio:", e)
        final = "Sorry, something went wrong. Please try again."

    finally:
        # clean up temp audio file
        if os.path.exists(path):
            os.remove(path)

    out = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=final, lang=lang).save(out)

    return FileResponse(out, media_type="audio/mpeg")

# ------------------ TEXT API ------------------

class TextInput(BaseModel):
    text: str
    lang: str = "en"
    patient_id: int = 0   # FIX 5: added missing patient_id field


@app.post("/process-text")
def process_text(data: TextInput):
    english = gt_to_english(data.text)
    reply = generate_reply(english, user_id=str(data.patient_id), lang=data.lang)  # FIX 5
    final = gt_from_english(reply, data.lang)

    out = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=final, lang=data.lang).save(out)

    return FileResponse(out, media_type="audio/mpeg")

# ------------------ TEST APIs ------------------

@app.get("/")
async def root():
    return {"status": "Running"}

@app.get("/doctors")
async def get_all_doctors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()
    conn.close()
    return {"doctors": [dict(d) for d in doctors]}

# ------------------ AUTH ------------------

@app.post("/login")
def login(phone: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patients WHERE phone=?", (phone,)).fetchone()
    conn.close()

    if not patient:
        return {"status": "not_found"}

    if not patient["password_hash"] or not verify_password(password, patient["password_hash"]):
        return {"status": "invalid_password"}

    return {
        "status": "success",
        "patient": {
            "id": patient["patient_id"],
            "preferred_language": patient["preferred_language"] or "en"
        }
    }

@app.post("/register")
def register_patient(
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    language: str = Form("en")
):
    try:
        conn = get_db_connection()
        existing = conn.execute("SELECT * FROM patients WHERE phone=?", (phone,)).fetchone()
        if existing:
            conn.close()
            return {"error": "Patient already exists"}

        conn.execute("""
            INSERT INTO patients (name, age, gender, phone, preferred_language, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, age, gender, phone, language, hash_password(password)))

        conn.commit()
        conn.close()
        return {"status": "created"}

    except Exception as e:
        print("REGISTER ERROR:", e)
        return {"error": str(e)}
    
@app.get("/admin/appointments")
def get_admin_appointments(patient_id: int = None):
    conn = get_db_connection()
    if patient_id:
        rows = conn.execute("""
            SELECT a.appointment_id, p.name AS patient,
                   d.name AS doctor, a.appointment_date AS date,
                   a.appointment_time AS time, a.status, a.reason
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC
        """, (patient_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT a.appointment_id, p.name AS patient,
                   d.name AS doctor, a.appointment_date AS date,
                   a.appointment_time AS time, a.status, a.reason
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            ORDER BY a.appointment_date DESC
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]