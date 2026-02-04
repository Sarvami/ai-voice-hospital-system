from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from googletrans import Translator
from dotenv import load_dotenv
from gtts import gTTS
import requests
import uuid
import os
import time
import difflib
import sqlite3
import json
from typing import Optional

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

translator = Translator()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

supported = ["en", "hi", "mr"]

# ------------------ DATABASE SETUP ------------------

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect('hospital.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row  # This allows column access by name
    return conn

def init_database():
    """Initialize database with tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        qualification TEXT,
        experience_years INTEGER,
        available_days TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        phone TEXT,
        preferred_language TEXT DEFAULT 'en',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        status TEXT DEFAULT 'Booked',
        reason TEXT,
        booking_source TEXT DEFAULT 'voice',
        language_used TEXT DEFAULT 'en',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients (id),
        FOREIGN KEY (doctor_id) REFERENCES doctors (id)
    )
    ''')
    
    # Insert sample data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        # Insert sample doctors
        doctors = [
            ('Dr. Mehta', 'Cardiology', 'MD Cardiology', 12, 'Mon-Fri'),
            ('Dr. Sharma', 'General', 'MBBS', 8, 'Mon-Sat'),
            ('Dr. Rao', 'ENT', 'MS ENT', 10, 'Tue-Sun')
        ]
        cursor.executemany('''
            INSERT INTO doctors (name, department, qualification, experience_years, available_days)
            VALUES (?, ?, ?, ?, ?)
        ''', doctors)
        
        # Insert sample patients
        patients = [
            ('Amit Patil', 45, 'Male', '9999999999', 'mr'),
            ('Sneha Kulkarni', 30, 'Female', '8888888888', 'en'),
            ('Rahul Verma', 52, 'Male', '7777777777', 'hi')
        ]
        cursor.executemany('''
            INSERT INTO patients (name, age, gender, phone, preferred_language)
            VALUES (?, ?, ?, ?, ?)
        ''', patients)
        
        # Get inserted IDs
        cursor.execute("SELECT id FROM doctors ORDER BY id")
        doctor_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM patients ORDER BY id")
        patient_ids = [row[0] for row in cursor.fetchall()]
        
        # Insert sample appointments
        if doctor_ids and patient_ids:
            appointments = [
                (patient_ids[0], doctor_ids[1], '2026-01-10', '10:30', 'Booked', 'General consultation', 'voice', 'mr'),
                (patient_ids[1], doctor_ids[0], '2026-01-11', '11:00', 'Booked', 'Chest pain', 'voice', 'en'),
                (patient_ids[2], doctor_ids[2], '2026-01-12', '12:15', 'Booked', 'Ear discomfort', 'voice', 'hi')
            ]
            cursor.executemany('''
                INSERT INTO appointments 
                (patient_id, doctor_id, appointment_date, appointment_time, status, reason, booking_source, language_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', appointments)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# ------------------ MEMORY ------------------

user_state = {}
user_data = {}

# ------------------ DATA ------------------

doctors_by_dept = {
    "cardiology": ["Dr Sharma", "Dr Mehta"],
    "ent": ["Dr Patil", "Dr Joshi"],
    "dentist": ["Dr Shah"],
    "general": ["Dr Rao"]
}

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

def get_doctors_by_department(department: str):
    """Get doctors from database by department"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get doctors from database
    cursor.execute('''
        SELECT name FROM doctors 
        WHERE LOWER(department) LIKE ? 
        OR LOWER(department) LIKE ?
    ''', (f'%{department}%', department))
    
    db_doctors = [row[0] for row in cursor.fetchall()]
    
    # Get hardcoded doctors for this department
    hardcoded_doctors = doctors_by_dept.get(department, [])
    
    # Combine and remove duplicates
    all_doctors = list(set(hardcoded_doctors + db_doctors))
    
    conn.close()
    return all_doctors

def find_doctor_by_name(doctor_name: str):
    """Find doctor by name"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM doctors 
        WHERE LOWER(name) LIKE ? 
        OR name LIKE ?
    ''', (f'%{doctor_name.lower()}%', f'%{doctor_name}%'))
    
    doctor = cursor.fetchone()
    conn.close()
    
    return dict(doctor) if doctor else None

def get_or_create_patient(name: str, phone: str, language: str = "en"):
    """Get existing patient or create new one"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient exists by phone
    cursor.execute("SELECT * FROM patients WHERE phone = ?", (phone,))
    patient = cursor.fetchone()
    
    if patient:
        conn.close()
        return dict(patient)
    else:
        # Create new patient
        cursor.execute('''
            INSERT INTO patients (name, age, gender, phone, preferred_language)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, 30, 'Unknown', phone, language))
        
        patient_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        new_patient = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        return dict(new_patient) if new_patient else None

def create_appointment(patient_id: int, doctor_id: int, date: str, time: str, reason: str = "General consultation", language: str = "en"):
    """Create appointment in database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO appointments 
        (patient_id, doctor_id, appointment_date, appointment_time, status, reason, booking_source, language_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (patient_id, doctor_id, date, time, 'Booked', reason, 'voice', language))
    
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return appointment_id

# ------------------ STT ------------------

def speech_to_text(audio_path):
    headers = {"authorization": API_KEY}
    
    with open(audio_path, "rb") as f:
        upload_res = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=f
        )
    
    audio_url = upload_res.json()["upload_url"]
    
    transcript_res = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json={"audio_url": audio_url}
    )
    
    transcript_id = transcript_res.json()["id"]
    
    while True:
        status_res = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers=headers
        )
        
        status = status_res.json()["status"]
        
        if status == "completed":
            return status_res.json()["text"]
        elif status == "error":
            raise Exception("Transcription failed")
        
        time.sleep(2)

# ------------------ TRANSLATION ------------------

def translate_to_english(text):
    result = translator.translate(text, dest="en")
    
    # Detect language
    lang = "hi" if any(w in text.lower() for w in ["muje", "mujhe", "dard", "bukhar", "sardi"]) else "en"
    
    return result.text, lang

def translate_back(text, lang):
    if lang == "en":
        return text
    
    result = translator.translate(text, dest=lang)
    return result.text

# ------------------ LOGIC ------------------

def fuzzy_match(text, keywords):
    words = text.lower().split()
    
    for word in words:
        matches = difflib.get_close_matches(word, keywords, n=1, cutoff=0.7)
        if matches:
            return matches[0]
    
    return None

def generate_reply(text, user_id="user1"):
    global user_state, user_data
    
    text = text.lower().strip()
    
    # Init user
    if user_id not in user_state:
        user_state[user_id] = "idle"
        user_data[user_id] = {"phone": None, "name": None}
    
    state = user_state[user_id]
    
    # ---------------- CANCEL ----------------
    if any(w in text for w in ["cancel", "stop", "exit"]):
        user_state[user_id] = "idle"
        user_data[user_id] = {"phone": None, "name": None}
        return "Okay, I have cancelled your request. How can I help you now?"
    
    # ---------------- GREETING (RESET) ----------------
    if any(w in text for w in ["hello", "hi", "namaste", "hey"]):
        user_state[user_id] = "idle"
        user_data[user_id] = {"phone": None, "name": None}
        return "Hello! How can I help you?"
    
    # ---------------- GET PATIENT INFO ----------------
    if state == "idle" and any(w in text for w in ["appointment", "book", "schedule"]):
        user_state[user_id] = "waiting_name"
        return "May I have your name, please?"
    
    # ---------------- GET NAME ----------------
    if state == "waiting_name":
        user_data[user_id]["name"] = text.title()
        user_state[user_id] = "waiting_phone"
        return f"Thank you {user_data[user_id]['name']}. What is your phone number?"
    
    # ---------------- GET PHONE ----------------
    if state == "waiting_phone":
        # Extract numbers from text
        import re
        phone = re.sub(r'\D', '', text)  # Remove non-digits
        if len(phone) >= 10:
            phone = phone[:10]  # Take first 10 digits
        else:
            return "Please provide a valid 10-digit phone number."
        
        user_data[user_id]["phone"] = phone
        user_state[user_id] = "waiting_problem"
        return "What problem are you facing?"
    
    # ---------------- DIRECT DOCTOR BOOKING ----------------
    if state == "waiting_problem":
        # Check for direct doctor mention from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM doctors")
        all_doctors = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        for doctor_name in all_doctors:
            if doctor_name.lower() in text:
                # Get doctor details
                doctor_info = find_doctor_by_name(doctor_name)
                if doctor_info:
                    user_data[user_id]["doctor"] = doctor_info['name']
                    user_data[user_id]["doctor_id"] = doctor_info['id']
                    user_data[user_id]["dept"] = doctor_info['department'].lower()
                    user_state[user_id] = "waiting_date"
                    return f"Okay. Appointment with {doctor_info['name']}. On which date?"
    
    # ---------------- PROBLEM → DEPT ----------------
    if state == "waiting_problem":
        # Collect all keywords
        keywords = []
        for k in problem_map:
            keywords.extend(k.split())
        
        # Try fuzzy matching
        match = fuzzy_match(text, keywords)
        
        if match:
            for key in problem_map:
                if match in key:
                    dept = problem_map[key]
                    user_data[user_id]["dept"] = dept
                    
                    # Get doctors from database
                    doctors = get_doctors_by_department(dept)
                    
                    user_state[user_id] = "waiting_doctor"
                    
                    if doctors:
                        doctor_list = ", ".join(doctors)
                        return f"You should visit {dept}. Available doctors are: {doctor_list}. Do you have any preference?"
                    else:
                        return f"No doctors available in {dept} department at the moment."
        
        return "Please describe your health problem."
    
    # ---------------- DOCTOR ----------------
    if state == "waiting_doctor":
        if any(w in text for w in ["no", "anyone", "any", "whatever"]):
            dept = user_data[user_id]["dept"]
            
            # Get first available doctor for this department
            doctors = get_doctors_by_department(dept)
            
            if doctors:
                doctor_name = doctors[0]
                # Get doctor ID from database
                doctor_info = find_doctor_by_name(doctor_name)
                if doctor_info:
                    user_data[user_id]["doctor"] = doctor_info['name']
                    user_data[user_id]["doctor_id"] = doctor_info['id']
                else:
                    user_data[user_id]["doctor"] = doctor_name
                    user_data[user_id]["doctor_id"] = None
                
                user_state[user_id] = "waiting_date"
                return f"Okay. I will assign {doctor_name}. On which date?"
            else:
                return "No doctors available. Please try another department."
        
        # Check for specific doctor
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM doctors")
        all_doctors = cursor.fetchall()
        conn.close()
        
        for doctor_row in all_doctors:
            doctor_id, doctor_name = doctor_row
            if doctor_name.lower() in text:
                user_data[user_id]["doctor"] = doctor_name
                user_data[user_id]["doctor_id"] = doctor_id
                user_state[user_id] = "waiting_date"
                return f"Okay. Appointment with {doctor_name}. On which date?"
        
        return "Please tell the doctor name or say anyone."
    
    # ---------------- DATE ----------------
    if state == "waiting_date":
        user_data[user_id]["date"] = text.replace(".", "").strip()
        user_state[user_id] = "waiting_time"
        return "At what time?"
    
    # ---------------- TIME ----------------
    if state == "waiting_time":
        user_data[user_id]["time"] = text.replace(".", "").strip()
        user_state[user_id] = "confirming"
        
        d = user_data[user_id]
        return (
            f"Please confirm. Appointment with {d.get('doctor', 'doctor')} "
            f"on {d['date']} at {d['time']}. Say yes or no."
        )
    
    # ---------------- CONFIRM ----------------
    if state == "confirming":
        if "yes" in text:
            d = user_data[user_id]
            
            # Create or get patient
            patient = get_or_create_patient(
                name=d.get("name", "Unknown"),
                phone=d.get("phone", "0000000000"),
                language="en"
            )
            
            if not patient:
                return "Error creating patient record. Please try again."
            
            # Get doctor ID if not already set
            if "doctor_id" not in d or not d["doctor_id"]:
                doctor_info = find_doctor_by_name(d.get("doctor", ""))
                if doctor_info:
                    d["doctor_id"] = doctor_info['id']
                else:
                    # Use first available doctor as fallback
                    doctors = get_doctors_by_department(d.get("dept", "general"))
                    if doctors:
                        doctor_info = find_doctor_by_name(doctors[0])
                        if doctor_info:
                            d["doctor_id"] = doctor_info['id']
            
            # Create appointment
            if "doctor_id" in d and d["doctor_id"]:
                appointment_id = create_appointment(
                    patient_id=patient['id'],
                    doctor_id=d['doctor_id'],
                    date=d['date'],
                    time=d['time'],
                    reason=d.get('dept', 'General consultation'),
                    language="en"
                )
                
                # Reset state
                user_state[user_id] = "idle"
                user_data[user_id] = {"phone": None, "name": None}
                
                # Get doctor name for confirmation
                doctor_info = find_doctor_by_name(d.get("doctor", ""))
                doctor_name = doctor_info['name'] if doctor_info else d.get('doctor', 'the doctor')
                
                return (
                    f"Your appointment with {doctor_name} "
                    f"on {d['date']} at {d['time']} is confirmed. "
                    f"Your appointment ID is {appointment_id}. Thank you."
                )
            else:
                return "Sorry, doctor information is missing. Please try again."
        else:
            user_state[user_id] = "idle"
            user_data[user_id] = {"phone": None, "name": None}
            return "Okay. Appointment cancelled."
    
    # ---------------- DEFAULT ----------------
    return "Sorry, I did not understand. Please repeat."

# ------------------ MAIN API ------------------

@app.post("/process-audio")
async def process_audio(audio: UploadFile = File(...)):
    input_path = f"{TEMP_DIR}/{uuid.uuid4()}.wav"
    
    with open(input_path, "wb") as f:
        f.write(await audio.read())
    
    # STT
    original_text = speech_to_text(input_path)
    
    # Translate
    english_text, lang = translate_to_english(original_text)
    
    # Logic with database
    reply_english = generate_reply(english_text, "user1")
    
    # Translate back
    final_reply = translate_back(reply_english, lang)
    
    print("RAW:", original_text)
    print("EN:", english_text)
    print("LANG:", lang)
    print("REPLY:", reply_english)
    
    # TTS language
    tts_lang = lang if lang in supported else "en"
    
    # TTS
    output_path = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=final_reply, lang=tts_lang).save(output_path)
    
    return FileResponse(output_path, media_type="audio/mpeg")

# ------------------ DEBUG & DATABASE APIS ------------------

@app.post("/speech-to-text")
async def speech_to_text_only(audio: UploadFile = File(...)):
    input_path = f"{TEMP_DIR}/{uuid.uuid4()}.wav"
    
    with open(input_path, "wb") as f:
        f.write(await audio.read())
    
    text = speech_to_text(input_path)
    
    return JSONResponse({
        "transcript": text
    })

@app.get("/doctors")
async def get_all_doctors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()
    conn.close()
    
    return {
        "doctors": [dict(doctor) for doctor in doctors]
    }

@app.get("/appointments")
async def get_all_appointments():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.*, p.name as patient_name, d.name as doctor_name
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.id
        LEFT JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.created_at DESC
    ''')
    
    appointments = cursor.fetchall()
    conn.close()
    
    return {
        "appointments": [dict(appt) for appt in appointments]
    }

@app.get("/patients")
async def get_all_patients():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    conn.close()
    
    return {
        "patients": [dict(patient) for patient in patients]
    }

@app.get("/init-db")
async def initialize_database():
    """Initialize database with sample data"""
    try:
        init_database()
        return {"message": "Database initialized successfully"}
    except Exception as e:
        return {"message": f"Error initializing database: {str(e)}"}

# Health check
@app.get("/")
async def root():
    return {"message": "AI Voice Hospital System API is running"}

@app.get("/test-db")
async def test_database():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        return {
            "status": "connected",
            "tables": [table[0] for table in tables]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    