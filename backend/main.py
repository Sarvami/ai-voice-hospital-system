from database import SessionLocal, Patient
from googletrans import Translator
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from gtts import gTTS
from fastapi import Request
import requests
import uuid
import os
import time
import difflib
import re
import sqlite3
import dateparser
import random

from passlib.context import CryptContext
from pydantic import BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password[:72], hashed)

# ------------------ SETUP ------------------

translator = Translator()

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

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
STT_POLL_INTERVAL = 1

# ------------------ DB CONNECTION ------------------

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
        return text

def gt_from_english(text: str, target_lang: str) -> str:
    if target_lang == "en":
        return text
    try:
        return translator.translate(text, dest=target_lang).text
    except Exception:
        return text


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
    cursor.execute(
        "SELECT * FROM doctors WHERE LOWER(doc_id) = LOWER(?)",
        (name.strip(),)
    )
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
    existing = cursor.execute("""
        SELECT appointment_id FROM appointments 
        WHERE patient_id=? AND doctor_id=? AND appointment_date=?
    """, (pid, did, date)).fetchone()
    if existing:
        conn.close()
        return None
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
        upload_response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=f
        )

    upload_json = upload_response.json()
    if "upload_url" not in upload_json:
        raise Exception(f"Upload failed: {upload_json}")

    audio_url = upload_json["upload_url"]

    transcript_response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json={"audio_url": audio_url}
    )

    transcript_json = transcript_response.json()
    if "id" not in transcript_json:
        raise Exception(f"Transcript request failed: {transcript_json}")

    tid = transcript_json["id"]
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
            raise Exception(f"STT failed: {res.json()}")
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

def generate_reply(text, user_id="user1", lang="en", original=""):
    text = text.lower().strip()
    combined = text + " " + original.lower()

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
        user_state[user_id] = "idle"

    state = user_state[user_id]

    if state == "idle":
        if any(word in text for word in ["appointment", "book", "doctor", "consult"]):
            user_state[user_id] = "waiting_problem"
            return "What problem are you facing? You can also say regular checkup.", {}
        else:
            return "Say 'book appointment' to get started."

    elif state == "waiting_problem":
        matched_dept = None
        for key, dept in problem_map.items():
            if key in text:
                matched_dept = dept
                break
        if not matched_dept:
            match = fuzzy_match(text, list(problem_map.keys()))
            if match:
                matched_dept = problem_map[match]

        if matched_dept:
         user_data[user_id]["dept"] = matched_dept
         doctors = get_doctors_by_department(matched_dept)
         if not doctors:
            return "Sorry, no doctors available for that department right now.", {}
         user_data[user_id]["available_doctors"] = doctors
         user_state[user_id] = "waiting_doctor"
         doctor_names = [d.replace("Dr.", "Doctor") for d in doctors]
         reply = f"Available doctors: {', '.join(doctor_names)}. Any preference?"
         return reply, {
            "intent": "select_doctor",
            "data": {"doctors": doctors}
        }

        return "Sorry, I didn't catch that. Please describe your problem." , {}

    elif state == "waiting_doctor":
        available = user_data[user_id].get("available_doctors", [])
        chosen = None
        print(f"TEXT: {text}")
        print(f"AVAILABLE: {available}")

        for doc in available:
            parts = doc.lower().replace("dr.", "").replace("dr", "").strip().split()
            for part in parts:
                if part in text.lower():
                    chosen = doc
                    break
            if chosen:
                break

        if not chosen:
            for doc in available:
                parts = doc.lower().replace("dr.", "").strip().split()
                for part in parts:
                    matches = difflib.get_close_matches(part, text.lower().split(), 1, 0.6)
                    if matches:
                        chosen = doc
                        break
                if chosen:
                    break

        if not chosen:
            return f"Sorry, I didn't catch that. Available doctors are: {', '.join(available)}. Please say a name."

        conn = get_db_connection()
        doctor_row = conn.execute(
            "SELECT doctor_id FROM doctors WHERE LOWER(name) LIKE ?",
            (f"%{chosen.lower().replace('dr.', '').strip()}%",)
        ).fetchone()
        conn.close()

        user_data[user_id]["doctor"]    = chosen
        user_data[user_id]["doctor_id"] = doctor_row["doctor_id"] if doctor_row else None
        user_state[user_id] = "waiting_date"
        return f"Great, {chosen}. What date would you like?", {
          "intent": "select_date",
          "data": {"doctor": chosen}
         }
        
    elif state == "waiting_date":
        date_number_words = {
            "first": "1", "second": "2", "third": "3", "fourth": "4",
            "fifth": "5", "sixth": "6", "seventh": "7", "eighth": "8",
            "ninth": "9", "tenth": "10", "eleventh": "11", "twelfth": "12",
            "thirteenth": "13", "fourteenth": "14", "fifteenth": "15",
            "sixteenth": "16", "seventeenth": "17", "eighteenth": "18",
            "nineteenth": "19", "twentieth": "20", "thirtieth": "30",
            "thirty-first": "31",
            "ek": "1", "don": "2", "do": "2", "teen": "3",
            "paach": "5", "paanch": "5", "saha": "6", "chhe": "6",
            "saat": "7", "aat": "8", "aath": "8", "nau": "9",
            "daha": "10", "das": "10", "gara": "10", "dhara": "10",
            "akra": "11", "gyarah": "11", "bara": "12", "barah": "12",
            "tera": "13", "thera": "13", "chaudha": "14",
            "pandhra": "15", "solha": "16", "satra": "17", "athra": "18",
            "ekonis": "19", "vis": "20", "ekkis": "21", "bais": "22",
            "teis": "23", "chaubis": "24", "panchvis": "25",
            "sattavis": "27", "athhavis": "28", "ekonatis": "29",
            "tis": "30", "ekatis": "31",
        }
        words = text.lower().split()
        text = " ".join([date_number_words.get(w, w) for w in words])

        cleaned = re.sub(
            r"\b(i would like|an appointment on|appointment|please|book|schedule|"
            r"chahungi|chahta|chahiye|chahir|mujhe|ko|co|la|che|ahe|mala|tya|on|"
            r"the|a|an|for|kara|karaycha|dyaycha|hava|because|of)\b",
            "", text
        ).strip()
        cleaned = re.sub(r'[.]+', ' ', cleaned)
        cleaned = ' '.join(dict.fromkeys(cleaned.split()))

        raw_deduped = re.sub(r'[.]+', ' ', text)
        raw_deduped = ' '.join(dict.fromkeys(raw_deduped.split()))

        original_cleaned = re.sub(
            r"\b(appointment|book|kara|karaycha|co|la|che|ahe|mala)\b",
            "", original.lower()
        ).strip()

        parsed = None
        for attempt in [cleaned, raw_deduped, text, original_cleaned, original]:
            parsed = dateparser.parse(
                attempt,
                languages=["en", "hi", "mr"],
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": __import__("datetime").datetime.now(),
                    "DATE_ORDER": "DMY",
                }
            )
            if parsed:
                break

        if parsed:
            from datetime import datetime
            if parsed.date() < datetime.now().date():
                return "That date is in the past. Please choose a future date."
            user_data[user_id]["date"] = parsed.strftime("%d %B %Y")
            user_state[user_id] = "waiting_time"
            return f"Got it, {user_data[user_id]['date']}. At what time?"
        else:
            return "Sorry, I didn't catch the date. Please say just the date, like 'April 10' or 'tomorrow'."
       

    elif state == "waiting_time":
        number_words = {
         "Bara": 12, "barah": 12, "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
         "chhe": 6, "saat": 7,"Saat": 7,"sat": 7, "aath": 8, "nau": 9, "das": 10,
         "gyarah": 11, "barah": 12, "bara": 12,
         "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
         "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12,
          }

        detected_hour = None
        detected_period = "PM"
        words = text.lower().split()

        if any(w in combined for w in ["dopaher", "do peher", "dophar", "afternoon", "sham", "sandhya"]):
            detected_period = "PM"
        if any(w in words for w in ["sakal", "subah", "morning"]):
            detected_period = "AM"
        if any(w in words for w in ["raat", "night"]):
            detected_period = "PM"

        for word in words:
            if word.isdigit():
                detected_hour = int(word)
                break
            if word in number_words:
                detected_hour = number_words[word]
                break

        if detected_hour:
            if detected_period == "PM" and detected_hour < 12:
                hour_24 = detected_hour + 12
            elif detected_period == "AM" and detected_hour == 12:
                hour_24 = 0
            else:
                hour_24 = detected_hour

            if not (8 <= hour_24 <= 20):
                return "Sorry, appointments are only available between 8 AM and 8 PM. Please choose a valid time."

            time_str = f"{hour_24:02d}:00"
            from datetime import datetime
            parsed_time = datetime.strptime(time_str, "%H:%M")
            user_data[user_id]["time"] = parsed_time.strftime("%I:%M %p")
            user_state[user_id] = "confirming"
            d = user_data[user_id]
            return f"Confirm appointment with {d['doctor']} on {d['date']} at {d['time']}?"

        # Fallback: try dateparser if number_words didn't match
        parsed = dateparser.parse(text, settings={"PREFER_DATES_FROM": "future"})
        if parsed:
            if not (8 <= parsed.hour <= 20):
                return "Sorry, appointments are only available between 8 AM and 8 PM. Please choose a valid time."
            user_data[user_id]["time"] = parsed.strftime("%I:%M %p")
            user_state[user_id] = "confirming"
            d = user_data[user_id]
            return f"Confirm appointment with {d['doctor']} on {d['date']} at {d['time']}?"

        return "Sorry, I didn't catch the time. Please say it again, like '11 AM' or '3 in the afternoon'."

    elif state == "confirming":
        confirm_words = ["yes", "confirm", "ok", "okay", "ha", "haa", "haan", "ho", "hou", "theek", "bilkul", "sure"]
        cancel_words  = ["no", "cancel", "nahi", "nako", "band", "nahii", "mat", "don't"]
        if any(w in text for w in confirm_words):
            d = user_data[user_id]
            patient = get_or_create_patient(d["name"], d["phone"], lang)
            aid = create_appointment(
                patient["patient_id"],
                d["doctor_id"],
                d["date"],
                d["time"],
                d["dept"],
                lang
            )
            if aid is None:
                user_state[user_id] = "idle"
                user_data[user_id] = {}
                return "You already have an appointment with this doctor on that date. Please choose a different date."
            user_state[user_id] = "idle"
            user_data[user_id] = {}
            return f"Appointment confirmed! Your booking ID is {aid}."

        elif any(w in text for w in cancel_words):
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
        english = gt_to_english(original) if lang != "en" else original
        print(f"ORIGINAL: {original}")
        print(f"TRANSLATED: {english}")
        print(f"USER STATE: {user_state.get(str(patient_id), 'NOT FOUND')}")
        reply, meta = generate_reply(english, user_id=str(patient_id), lang=lang, original=original)
        print(f"REPLY: {reply}")
        final = gt_from_english(reply, lang)

    except TimeoutError:
        final = "Sorry, the system is taking too long. Please try again."
        meta = {}

    except Exception as e:
        print("ERROR in process_audio:", e)
        final = "Sorry, something went wrong. Please try again."
        meta = {}

    finally:
        if os.path.exists(path):
            os.remove(path)

    # If meta has a special intent, return JSON so frontend can show popup
    if meta.get("intent"):
        out = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
        gTTS(text=final, lang=lang).save(out)
        audio_url = f"/temp-audio/{os.path.basename(out)}"
        return JSONResponse({"intent": meta["intent"], "data": meta.get("data", {}), "message": final, "audio_path": audio_url})

    out = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=final, lang=lang).save(out)
    return FileResponse(out, media_type="audio/mpeg")

# ------------------ TEXT API ------------------

class TextInput(BaseModel):
    text: str
    lang: str = "en"
    patient_id: int = 0

class AddDoctorRequest(BaseModel):
    name: str
    department: str
    qualification: str = ""
    experience_years: int = 0
    doc_id: str
    password: str
    available_days: str = ""


@app.post("/process-text")
def process_text(data: TextInput):
    english = gt_to_english(data.text)
    reply = generate_reply(english, user_id=str(data.patient_id), lang=data.lang, original=data.text)
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

    if role == "doctor":
        phone = data.get("doctor_id", "").strip()
    else:
        phone = data.get("phone", "").strip()

    if not phone or not password:
        return {"success": False, "message": "Missing fields"}

    conn = get_db_connection()

    if role == "patient":
        user = conn.execute("SELECT * FROM patients WHERE phone=?", (phone,)).fetchone()
        conn.close()
        if not user:
            return {"success": False, "message": "User not found"}
        if not user["password_hash"] or not verify_password(password, user["password_hash"]):
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

    elif role == "doctor":
        doctor_id_val = data.get("doctor_id", "").strip()
        print(f"TRYING TO FIND: '{doctor_id_val}'")
        all_doctors = conn.execute("SELECT doc_id FROM doctors LIMIT 5").fetchall()
        print(f"SAMPLE DOCTOR IDs IN DB: {[d[0] for d in all_doctors]}")
        user = conn.execute("SELECT * FROM doctors WHERE doc_id=?", (doctor_id_val,)).fetchone()
        conn.close()
        if not user:
            return {"success": False, "message": "Doctor ID not found"}
        if not user["password_hash"] or not verify_password(password, user["password_hash"]):
            return {"success": False, "message": "Incorrect password"}
        return {
            "success": True,
            "user": {
                "id": user["doctor_id"],
                "name": user["name"],
                "doc_id": user["doc_id"],
                "preferred_language": "en"
            }
        }

    conn.close()
    return {"success": False, "message": "Invalid role"}

@app.post("/register")
async def register_patient(request: Request):
    try:
        data = await request.json()
        name     = data.get("name", "").strip()
        age      = data.get("age", 0)
        phone    = data.get("phone", "").strip()
        password = data.get("password", "")
        language = data.get("preferred_language", "en")
        gender   = data.get("gender", "Unknown")

        if not name or not phone or not password:
            return {"success": False, "message": "Missing required fields"}

        conn = get_db_connection()
        existing = conn.execute("SELECT * FROM patients WHERE phone=?", (phone,)).fetchone()
        if existing:
            conn.close()
            return {"success": False, "message": "Patient already exists"}

        conn.execute("""
            INSERT INTO patients (name, age, gender, phone, preferred_language, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, age, gender, phone, language, hash_password(password)))

        conn.commit()
        conn.close()
        return {"success": True, "message": "Account created"}

    except Exception as e:
        print("REGISTER ERROR:", e)
        return {"success": False, "message": str(e)}


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

# ------------------ DOCTOR AUTH + DASHBOARD ------------------

@app.post("/doctor/login")
def doctor_login(doc_id: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    doctor = conn.execute("SELECT * FROM doctors WHERE doc_id=?", (doc_id,)).fetchone()    
    conn.close()
    if not doctor:
        return {"status": "not_found"}
    if not doctor["password_hash"] or not verify_password(password, doctor["password_hash"]):
        return {"status": "invalid_password"}
    return {
        "status": "success",
        "doctor": {
            "id": doctor["doctor_id"],
            "name": doctor["name"],
            "department": doctor["department"]
        }
    }

@app.get("/doctor/dashboard")
def doctor_dashboard(doctor_id: int):
    conn = get_db_connection()
    doctor = conn.execute("SELECT * FROM doctors WHERE doctor_id=?", (doctor_id,)).fetchone()
    if not doctor:
        conn.close()
        return {"error": "Doctor not found"}

    from datetime import date
    today = date.today().strftime("%Y-%m-%d")

    appointments_today = conn.execute("""
        SELECT COUNT(*) FROM appointments 
        WHERE doctor_id=? AND appointment_date=?
    """, (doctor_id, today)).fetchone()[0]

    total_patients = conn.execute("""
        SELECT COUNT(DISTINCT patient_id) FROM appointments WHERE doctor_id=?
    """, (doctor_id,)).fetchone()[0]

    conn.close()
    return {
        "name": doctor["name"],
        "specialization": doctor["department"],
        "appointments_today": appointments_today,
        "total_patients": total_patients,
        "rating": 4
    }

@app.get("/doctor/appointments")
def doctor_appointments(doctor_id: int):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT 
            a.appointment_id AS id,
            p.name AS patient_name,
            a.appointment_date AS date,
            a.appointment_time AS time,
            a.status,
            a.reason
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.doctor_id=?
        ORDER BY a.appointment_date DESC
    """, (doctor_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/patient/appointments")
def patient_appointments(patient_id: int):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT a.appointment_id, d.name AS doctor,
               a.appointment_date AS date, a.appointment_time AS time,
               a.status, a.reason
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC
    """, (patient_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/patient/records")
def patient_records(patient_id: int):
    return []

# ── OVERVIEW ──────────────────────────────────────────────────────────────────

@app.get("/admin/overview")
def get_admin_overview():
    conn = get_db_connection()
    patients     = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    doctors      = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    appointments = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    conn.close()
    return {"patients": patients, "doctors": doctors, "appointments": appointments}

@app.get("/admin/patients")
def get_admin_patients():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT name, age, phone, preferred_language, created_at FROM patients ORDER BY patient_id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/admin/doctors")
def get_admin_doctors():
    conn = get_db_connection()
    rows = conn.execute(
        """SELECT doctor_id, name, department, qualification,
                  experience_years, available_days
           FROM doctors ORDER BY doctor_id DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/add-doctor")
def add_doctor(req: AddDoctorRequest):
    conn = get_db_connection()
    existing = conn.execute(
        "SELECT doctor_id FROM doctors WHERE doc_id = ?", (req.doc_id,)
    ).fetchone()
    if existing:
        conn.close()
        return {"success": False, "message": f"A doctor with ID '{req.doc_id}' already exists."}
    
    clean = req.name.lower().replace("dr.", "").replace("dr ", "").strip()
    parts = clean.split()
    email = ".".join(parts) + "@hospital.com" 
    contact_phone = "9" + str(random.randint(100000000, 999999999))
    
    conn.execute(
        """INSERT INTO doctors
   (name, department, qualification, experience_years, available_days, doc_id, password_hash, email, contact_phone)""",
        (req.name, req.department, req.qualification, req.experience_years,
         req.available_days, req.doc_id, hash_password(req.password), email, contact_phone)
    )
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/doctors/by-region/{region}")
def doctors_by_region(region: str):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM doctors WHERE LOWER(region)=LOWER(?)", (region,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/temp-audio/{filename}")
async def serve_temp_audio(filename: str):
    path = f"{TEMP_DIR}/{filename}"
    if os.path.exists(path):
        return FileResponse(path, media_type="audio/mpeg")
    return JSONResponse({"error": "File not found"}, status_code=404)