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
import sqlite3
import re

# ------------------ SETUP ------------------

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

MAX_STT_WAIT = 30   # seconds
STT_POLL_INTERVAL = 2

# ------------------ TRANSLATION (PYTHON 3.13 SAFE) ------------------

def translate_text(text: str, target_lang: str) -> str:
    if target_lang == "en":
        return text
    try:
        res = requests.post(
            "https://libretranslate.de/translate",
            data={
                "q": text,
                "source": "auto",
                "target": target_lang,
                "format": "text",
            },
            timeout=10,
        )
        return res.json().get("translatedText", text)
    except Exception:
        return text

# ------------------ DATABASE SETUP ------------------

def get_db_connection():
    conn = sqlite3.connect("hospital.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        department TEXT,
        qualification TEXT,
        experience_years INTEGER,
        available_days TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        phone TEXT,
        preferred_language TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date TEXT,
        appointment_time TEXT,
        status TEXT,
        reason TEXT,
        booking_source TEXT,
        language_used TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_database()

# ------------------ MEMORY ------------------

user_state = {}
user_data = {}

# ------------------ DATA ------------------

problem_map = {
    "chest pain": "cardiology",
    "heart pain": "cardiology",
    "chest": "cardiology",
    "headache": "general",
    "fever": "general",
    "cold": "general",
    "cough": "general",
    "pain": "general",
    "ache": "general",
    "ear pain": "ent",
    "tooth pain": "dentist"
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
    cursor.execute("SELECT * FROM patients WHERE id=?", (pid,))
    new_patient = cursor.fetchone()

    conn.commit()
    conn.close()
    return dict(new_patient)

def create_appointment(pid, did, date, time, reason, language):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO appointments
        (patient_id, doctor_id, appointment_date, appointment_time,
         status, reason, booking_source, language_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (pid, did, date, time, "Booked", reason, "voice", language))

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

        # ⏱️ TIMEOUT CHECK
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

def generate_reply(text, user_id="user1"):
    text = text.lower().strip()

    if user_id not in user_state:
        user_state[user_id] = "idle"
        user_data[user_id] = {}

    state = user_state[user_id]

    if state == "idle" and "appointment" in text:
        user_state[user_id] = "waiting_name"
        return "May I have your name?"

    if state == "waiting_name":
        user_data[user_id]["name"] = text.title()
        user_state[user_id] = "waiting_phone"
        return "Your phone number?"

    if state == "waiting_phone":
        phone = re.sub(r"\D", "", text)
        if len(phone) < 10:
            return "Please say valid phone number."

        user_data[user_id]["phone"] = phone[:10]
        user_state[user_id] = "waiting_problem"
        return "What problem are you facing?"

    if state == "waiting_problem":
        for key, dept in problem_map.items():
            if key in text:
                user_data[user_id]["dept"] = dept
                doctors = get_doctors_by_department(dept)
                user_state[user_id] = "waiting_doctor"
                return f"Doctors: {', '.join(doctors)}. Any preference?"
        return "Please describe problem."

    if state == "waiting_doctor":
        dept = user_data[user_id]["dept"]
        doctors = get_doctors_by_department(dept)

        if doctors:
            info = find_doctor_by_name(doctors[0])
            user_data[user_id]["doctor"] = doctors[0]
            user_data[user_id]["doctor_id"] = info["id"]
            user_state[user_id] = "waiting_date"
            return "On which date?"
        return "No doctor available."

    if state == "waiting_date":
        user_data[user_id]["date"] = text
        user_state[user_id] = "waiting_time"
        return "At what time?"

    if state == "waiting_time":
        user_data[user_id]["time"] = text
        user_state[user_id] = "confirming"
        d = user_data[user_id]
        return f"Confirm appointment with {d['doctor']}?"

    if state == "confirming":
        if "yes" in text:
            d = user_data[user_id]
            patient = get_or_create_patient(d["name"], d["phone"], "en")

            aid = create_appointment(
                patient["id"],
                d["doctor_id"],
                d["date"],
                d["time"],
                d["dept"],
                "en"
            )

            user_state[user_id] = "idle"
            user_data[user_id] = {}
            return f"Appointment confirmed. ID: {aid}"

        user_state[user_id] = "idle"
        return "Cancelled."

    return "Sorry, repeat please."

# ------------------ MAIN API ------------------

@app.post("/process-audio")
async def process_audio(audio: UploadFile = File(...), lang: str = Form(...)):

    path = f"{TEMP_DIR}/{uuid.uuid4()}.wav"

    with open(path, "wb") as f:
        f.write(await audio.read())

    try:
        original = speech_to_text(path)
        english = translate_text(original, "en")
        reply = generate_reply(english)
        final = translate_text(reply, lang)

    except TimeoutError:
        final = "Sorry, the system is taking too long. Please try again."

    except Exception:
        final = "Sorry, something went wrong. Please try again."

    out = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=final, lang=lang).save(out)

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

    return {"doctors": [dict(doctor) for doctor in doctors]}
# ------------------ TEXT API ------------------

from pydantic import BaseModel

class TextInput(BaseModel):
    text: str
    lang: str = "en"


@app.post("/process-text")
def process_text(data: TextInput):

    # Translate to English for logic
    english = translate_text(data.text, "en")

    # Generate reply
    reply = generate_reply(english)

    # Translate back to user language
    final = translate_text(reply, data.lang)

    # Convert to speech
    out = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=final, lang=data.lang).save(out)

    return FileResponse(out, media_type="audio/mpeg")
