import os
import time
import difflib
import re
import random
import requests
import dateparser
from datetime import datetime
from googletrans import Translator
from gtts import gTTS
from database import get_db_connection

# ------------------ SETUP ------------------
translator = Translator()
MAX_STT_WAIT = 30
STT_POLL_INTERVAL = 1
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# ------------------ MEMORY (State Management) ------------------
user_state = {}
user_data = {}

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

# ------------------ HELPERS ------------------

def parse_available_hours(hours_str: str):
    if not hours_str:
        return 8, 20
    parts = [p.strip() for p in hours_str.split("-", 1)]
    if len(parts) != 2:
        return 8, 20
    try:
        start = datetime.strptime(parts[0].strip(), "%I:%M %p").hour
        end   = datetime.strptime(parts[1].strip(), "%I:%M %p").hour
        return start, end
    except Exception:
        return 8, 20

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

def fuzzy_match(text, keywords):
    words = text.lower().split()
    for word in words:
        matches = difflib.get_close_matches(word, keywords, 1, 0.7)
        if matches:
            return matches[0]
    return None

# ------------------ DB HELPERS (Voice Flow) ------------------

def get_doctors_by_department(dept, region=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if region:
        cursor.execute(
            "SELECT name, rating FROM doctors WHERE LOWER(department)=LOWER(?) AND LOWER(region)=LOWER(?)",
            (dept, region)
        )
    else:
        cursor.execute("SELECT name, rating FROM doctors WHERE LOWER(department)=LOWER(?)", (dept,))
    doctors = [{"name": row[0], "rating": row[1]} for row in cursor.fetchall()]
    conn.close()
    return doctors

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

# ------------------核心 VOICE LOGIC ------------------

def speech_to_text(audio_path):
    apiKey = os.getenv("ASSEMBLYAI_API_KEY")
    headers = {"authorization": apiKey}
    with open(audio_path, "rb") as f:
        upload_response = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=f)
    
    upload_url = upload_response.json().get("upload_url")
    if not upload_url:
        raise Exception("Upload failed")

    transcript_response = requests.post("https://api.assemblyai.com/v2/transcript", headers=headers, json={"audio_url": upload_url})
    tid = transcript_response.json().get("id")
    
    start_time = time.time()
    while True:
        res = requests.get(f"https://api.assemblyai.com/v2/transcript/{tid}", headers=headers)
        status = res.json()["status"]
        if status == "completed":
            return res.json()["text"]
        if status == "error":
            raise Exception("STT Error")
        if time.time() - start_time > MAX_STT_WAIT:
            raise TimeoutError("STT Timeout")
        time.sleep(STT_POLL_INTERVAL)

def generate_reply(text, user_id="user1", lang="en", original=""):
    text = text.lower().strip()
    combined = text + " " + original.lower()

    if "department" in text and ("which" in text or "what" in text or "belong" in text):
        for doc in ["mehta", "sharma", "rao", "shah", "desai", "gupta", "iyer", "malhotra", "bose", "chandra", "murthy", "menon", "sinha", "pandey", "hegde", "reddy"]:
            if doc in text:
                conn = get_db_connection()
                result = conn.execute("SELECT name, department FROM doctors WHERE LOWER(name) LIKE ?", (f"%{doc}%",)).fetchone()
                conn.close()
                if result:
                    return f"{result['name']} belongs to the {result['department']} department.", {}
        return "Sorry, I couldn't find that doctor.", {}

    if user_id not in user_state:
        conn = get_db_connection()
        db_uid = int(user_id) if str(user_id).isdigit() else user_id
        patient = conn.execute("SELECT * FROM patients WHERE patient_id=?", (db_uid,)).fetchone()
        conn.close()
        
        user_data[user_id] = {}
        if patient:
            user_data[user_id]["name"] = patient["name"]
            user_data[user_id]["phone"] = patient["phone"]
            user_data[user_id]["patient_id"] = patient["patient_id"]
            user_data[user_id]["region"] = patient["region"]
        user_state[user_id] = "idle"

    state = user_state[user_id]

    if state == "idle":
        if any(word in text for word in ["appointment", "book", "doctor", "consult"]):
            user_state[user_id] = "waiting_problem"
            return "What problem are you facing? You can also say regular checkup.", {}
        else:
            return "Say 'book appointment' to get started.", {}

    elif state == "waiting_problem":
        matched_dept = None
        for key, dept in problem_map.items():
            if key in text:
                matched_dept = dept
                break
        if not matched_dept:
            match = fuzzy_match(text, list(problem_map.keys()))
            if match: matched_dept = problem_map[match]

        if matched_dept:
            user_data[user_id]["dept"] = matched_dept
            region = user_data[user_id].get("region")
            
            if not region:
                conn = get_db_connection()
                db_uid = int(user_id) if str(user_id).isdigit() else user_id
                p_row = conn.execute("SELECT region FROM patients WHERE patient_id=?", (db_uid,)).fetchone()
                conn.close()
                if p_row and p_row["region"]:
                    region = p_row["region"]
                    user_data[user_id]["region"] = region

            doctors = get_doctors_by_department(matched_dept, region)
            reply_prefix = "Available doctors"
            if not doctors:
                doctors = get_doctors_by_department(matched_dept, None)
                if doctors:
                    reply_prefix = f"I couldn't find any {matched_dept} specialists in your specific area, but here are some available nearby"

            if not doctors:
                return "Sorry, no doctors available for that department right now.", {}

            user_data[user_id]["available_doctors"] = doctors
            user_state[user_id] = "waiting_doctor"
            
            if len(doctors) == 1:
                d = doctors[0]
                name = d['name'].replace('Dr.', 'Doctor')
                rating = d['rating']
                if "nearby" in reply_prefix:
                    reply = f"{name} (Rating {rating}) is available nearby. Book now?"
                else:
                    reply = f"{name} (Rating {rating}) is available. Book now, or see nearby doctors?"
            else:
                doctor_names = [f"{d['name'].replace('Dr.', 'Doctor')} (Rating {d['rating']})" for d in doctors]
                reply = f"{reply_prefix}: {', '.join(doctor_names)}. Any preference?"
            return reply, {"intent": "select_doctor", "data": {"doctors": doctors}}

        return "Sorry, I didn't catch that. Please describe your problem.", {}

    elif state == "waiting_doctor":
        available = user_data[user_id].get("available_doctors", [])
        chosen = None
        
        if any(w in text.lower() for w in ["nearby", "other area", "neighbor", "neighbour", "next area"]):
            matched_dept = user_data[user_id].get("dept")
            all_nearby = get_doctors_by_department(matched_dept, None)
            user_data[user_id]["available_doctors"] = all_nearby
            doc_names = [f"{d['name'].replace('Dr.', 'Doctor')} (Rating {d['rating']})" for d in all_nearby]
            return f"Understood. Here are {matched_dept} specialists from nearby areas: {', '.join(doc_names)}. Any preference?", {"intent": "select_doctor", "data": {"doctors": all_nearby}}

        if len(available) == 1 and any(w in text.lower() for w in ["yes", "book", "confirm", "okay", "sure", "that's fine"]):
            chosen = available[0]["name"]

        if not chosen:
            for doc_obj in available:
                doc_name = doc_obj["name"]
                parts = doc_name.lower().replace("dr.", "").replace("dr", "").strip().split()
                if any(part in text.lower() for part in parts):
                    chosen = doc_name
                    break

        if not chosen:
            for doc_obj in available:
                doc_name = doc_obj["name"]
                parts = doc_name.lower().replace("dr.", "").strip().split()
                for part in parts:
                    matches = difflib.get_close_matches(part, text.lower().split(), 1, 0.6)
                    if matches:
                        chosen = doc_name
                        break
                if chosen: break

        if not chosen:
            names_only = [d["name"] for d in available]
            return f"Sorry, I didn't catch that. Available doctors are: {', '.join(names_only)}. Please say a name or ask for nearby areas.", {}

        conn = get_db_connection()
        doctor_row = conn.execute("SELECT doctor_id, available_hours FROM doctors WHERE LOWER(name) LIKE ?", (f"%{chosen.lower().replace('dr.', '').strip()}%",)).fetchone()
        conn.close()

        user_data[user_id]["doctor"] = chosen
        user_data[user_id]["doctor_id"] = doctor_row["doctor_id"] if doctor_row else None
        avail_hours = doctor_row["available_hours"] if doctor_row and doctor_row["available_hours"] else "8:00 AM - 8:00 PM"
        user_data[user_id]["available_hours"] = avail_hours

        user_state[user_id] = "waiting_date"
        base_reply = f"Great, {chosen}. What date would you like? Note that the doctor is available {avail_hours}."
        return base_reply, {"intent": "ask_date", "data": {"doctor": chosen, "available_hours": avail_hours, "doctor_id": user_data[user_id]["doctor_id"]}}

    elif state == "waiting_date":
        date_number_words = {"first": "1", "second": "2", "third": "3", "fourth": "4", "fifth": "5", "ek": "1", "don": "2", "do": "2", "teen": "3"} # Simplified for concise code
        words = text.lower().split()
        text = " ".join([date_number_words.get(w, w) for w in words])
        parsed = dateparser.parse(text, languages=["en", "hi", "mr"], settings={"PREFER_DATES_FROM": "future", "DATE_ORDER": "DMY"})
        
        if parsed:
            if parsed.date() < datetime.now().date():
                return "That date is in the past. Please choose a future date.", {}
            user_data[user_id]["date"] = parsed.strftime("%d %B %Y")
            user_state[user_id] = "waiting_time"
            avail_hours = user_data[user_id].get("available_hours", "8:00 AM - 8:00 PM")
            reply = f"Got it, {user_data[user_id]['date']}. At what time? Note that {user_data[user_id]['doctor']} is available {avail_hours}."
            return reply, {"data": {"available_hours": avail_hours}}
        return "Sorry, I didn't catch the date. Please say it again.", {}

    elif state == "waiting_time":
        avail_hours = user_data[user_id].get("available_hours", "8:00 AM - 8:00 PM")
        allowed_start, allowed_end = parse_available_hours(avail_hours)
        
        detected_hour = None
        for word in text.split():
            if word.isdigit():
                detected_hour = int(word)
                break
        
        if detected_hour:
            # Simplified time detection logic
            h24 = detected_hour if "pm" not in text.lower() or detected_hour == 12 else detected_hour + 12
            if not (allowed_start <= h24 <= allowed_end):
                return f"Sorry, the doctor is only available {avail_hours}.", {}
            user_data[user_id]["time"] = f"{h24:02d}:00"
            user_state[user_id] = "confirming"
            d = user_data[user_id]
            return f"Confirm appointment with {d['doctor']} on {d['date']} at {d['time']}?", {}
        return "Sorry, I didn't catch the time.", {}

    elif state == "confirming":
        if any(w in text for w in ["yes", "confirm", "ok", "sure", "theek"]):
            d = user_data[user_id]
            patient = get_or_create_patient(d["name"], d["phone"], lang)
            aid = create_appointment(patient["patient_id"], d["doctor_id"], d["date"], d["time"], d["dept"], lang)
            user_state[user_id] = "idle"
            user_data[user_id] = {}
            if aid: return "Confirmed! Your appointment is booked. See you then!", {"booked": True}
            return "You already have an appointment on that date.", {}
        return "Booking cancelled. Say 'book appointment' to restart.", {}

    return "Sorry, I'm not sure how to respond to that.", {}
