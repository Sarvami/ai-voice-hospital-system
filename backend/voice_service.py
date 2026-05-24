import os
import time
import difflib
import re
import random
import requests
import dateparser
from datetime import datetime
from deep_translator import GoogleTranslator
from gtts import gTTS
from database import get_db_connection
from repositories import doctor_repo, patient_repo, appointment_repo
from repositories.session_repo import get_session, set_session, delete_session

# ------------------ SETUP ------------------
# translator = Translator() is replaced by usage-time instantiation in deep-translator
MAX_STT_WAIT = 30
STT_POLL_INTERVAL = 1
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# Stateless session management — DB is the source of truth
# Removed global user_state/user_data dicts to ensure statelessness

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


def gt_from_english(text: str, target_lang: str) -> str:
    if target_lang == "en":
        return text
    try:
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    except Exception:
        return text

def gt_to_english(text: str) -> str:
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
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
    result = doctor_repo.get_doctors_by_department(conn, dept, region)
    conn.close()
    return result


def get_or_create_patient(name, phone, language="en"):
    conn = get_db_connection()
    result = patient_repo.get_or_create_patient_voice(conn, name, phone, language)
    conn.close()
    return result


def create_appointment(pid, did, date, time_str, reason, language):
    conn = get_db_connection()
    if appointment_repo.appointment_exists(conn, pid, did, date):
        conn.close()
        return None
    if appointment_repo.appointment_slot_taken(conn, did, date, time_str):
        conn.close()
        return "slot_taken"
    aid = appointment_repo.create_appointment(conn, pid, did, date, time_str, "Booked", reason, "voice", language)
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
                result = doctor_repo.get_doctor_department_by_name(conn, doc)
                conn.close()
                if result:
                    return f"{result['name']} belongs to the {result['department']} department.", {}
        return "Sorry, I couldn't find that doctor.", {}

    # Load session from DB
    state, data = get_session(user_id)

    # Initialize data if it's a new session or patient_id is missing
    if ("patient_id" not in data) and str(user_id).isdigit():
        conn = get_db_connection()
        patient = patient_repo.get_patient_by_id(conn, int(user_id))
        conn.close()
        if patient:
            data = {
                "name": patient["name"],
                "phone": patient["phone"],
                "patient_id": patient["patient_id"],
                "region": patient["region"]
            }

    def save(new_state):
        nonlocal state
        state = new_state
        set_session(user_id, new_state, data)

    if state == "idle":
        if any(word in text for word in ["appointment", "book", "doctor", "consult"]):
            save("waiting_problem")
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
            data["dept"] = matched_dept
            region = data.get("region")
            
            if not region:
                conn = get_db_connection()
                patient = patient_repo.get_patient_by_id(conn, int(user_id)) if str(user_id).isdigit() else None
                conn.close()
                if patient and patient.get("region"):
                    region = patient["region"]
                    data["region"] = region

            doctors = get_doctors_by_department(matched_dept, region)
            reply_prefix = "Available doctors"
            if not doctors:
                doctors = get_doctors_by_department(matched_dept, None)
                if doctors:
                    reply_prefix = f"I couldn't find any {matched_dept} specialists in your specific area, but here are some available nearby"

            if not doctors:
                return "Sorry, no doctors available for that department right now.", {}

            data["available_doctors"] = doctors
            save("waiting_doctor")

            if len(doctors) == 1:
                d = doctors[0]
                name = d['name'].replace('Dr.', 'Doctor')
                region_label = data.get("region", "your area")
                if "nearby" in reply_prefix:
                    english_reply = f"We found {name} available nearby. Would you like to book with them? Say yes or no."
                else:
                    english_reply = f"We found {name} in {region_label}. Would you like to book with them? Say yes or no."
                reply = gt_from_english(english_reply, lang)
                return reply, {"intent": "show_doctors_popup", "data": {"doctors": doctors}}
            else:
                doctor_names = [f"{d['name'].replace('Dr.', 'Doctor')} (Rating {d['rating']})" for d in doctors]
                if "nearby" in reply_prefix:
                    reply = f"{reply_prefix}: {', '.join(doctor_names)}. Any preference?"
                else:
                    reply = f"In {region}, available doctors: {', '.join(doctor_names)}. Any preference?"
                return reply, {"intent": "select_doctor", "data": {"doctors": doctors}}

        return "Sorry, I didn't catch that. Please describe your problem.", {}

    elif state == "waiting_doctor":
        available = data.get("available_doctors", [])
        chosen = None

        # Detect "show me nearby / other area / aas paas" requests
        nearby_keywords = ["nearby", "other area", "neighbor", "neighbour", "next area",
                           "aas paas", "aaspaas", "kareeb", "doosre", "doosra",
                           "other doctor", "more doctor", "different doctor",
                           "jagah", "jagha", "different area", "another area", "meet"]
        original_lower = original.lower() if original else ""
        nearby_original_keywords = ["shetron", "shetra", "aas paas", "aaspaas", "paas ke",
                                    "kareeb", "milein", "miley", "mile", "doosre", "doosra"]
        if any(w in text.lower() for w in nearby_keywords) or any(w in original_lower for w in nearby_original_keywords):
            matched_dept = data.get("dept")
            current_region = data.get("region")
            all_doctors = get_doctors_by_department(matched_dept, None)
            # exclude current region doctors so we show truly nearby ones first, but include all
            nearby = [d for d in all_doctors if d.get("region", "").lower() != (current_region or "").lower()]
            if not nearby:
                nearby = all_doctors
            data["available_doctors"] = nearby
            data["popup_doctors"] = nearby
            data["popup_index"] = 0
            save("waiting_doctor")
            return (f"Here are {matched_dept} specialists from other areas. I'll show them one by one.",
                    {"intent": "show_doctors_popup", "data": {"doctors": nearby}})

        if len(available) == 1 and any(w in text.lower() for w in [
            # English
            "yes", "book", "confirm", "okay", "sure", "that's fine",
            # Hindi
            "haan", "haa", "ha", "bilkul", "theek", "zaroor",
            # Marathi
            "ho", "hoy",
            # Tamil
            "aamam", "aama",
            # Telugu
            "avunu", "avun",
            # Gujarati
            "haa", "ha",
        ]):
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
        doctor_row = doctor_repo.get_doctor_by_name_like(conn, chosen.replace('dr.', '').strip())
        conn.close()

        data["doctor"] = chosen
        data["doctor_id"] = doctor_row["doctor_id"] if doctor_row else None
        avail_hours = doctor_row["available_hours"] if doctor_row and doctor_row["available_hours"] else "8:00 AM - 8:00 PM"
        avail_days  = doctor_row["available_days"]  if doctor_row and doctor_row["available_days"]  else ""
        data["available_hours"] = avail_hours
        data["available_days"]  = avail_days

        state = "waiting_date"
        set_session(user_id, "waiting_date", data)
        base_reply = f"Great, {chosen}. What date would you like? The doctor is available {avail_days} {avail_hours}."
        return base_reply, {"intent": "ask_date", "data": {"doctor": chosen, "available_hours": avail_hours, "available_days": avail_days, "doctor_id": data["doctor_id"]}}

    elif state == "waiting_date":
        date_number_words = {"first": "1", "second": "2", "third": "3", "fourth": "4", "fifth": "5", "ek": "1", "don": "2", "do": "2", "teen": "3"}
        words = text.lower().split()
        text = " ".join([date_number_words.get(w, w) for w in words])
        parsed = dateparser.parse(text, languages=["en", "hi", "mr"], settings={"PREFER_DATES_FROM": "future", "DATE_ORDER": "DMY"})

        if parsed:
            if parsed.date() < datetime.now().date():
                return "That date is in the past. Please choose a future date.", {}

            # Check doctor's available days
            available_days_str = data.get("available_days", "")
            if available_days_str:
                day_name = parsed.strftime("%A")  # e.g. "Monday"
                day_abbr = parsed.strftime("%a")  # e.g. "Mon"
                days_lower = available_days_str.lower()

                # Parse ranges like "Mon-Thu", "Mon-Fri"
                day_order = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                allowed = set()
                import re as _re
                range_match = _re.search(r'(\w+)\s*[-–]\s*(\w+)', days_lower)
                if range_match:
                    start_d = range_match.group(1)[:3]
                    end_d   = range_match.group(2)[:3]
                    if start_d in day_order and end_d in day_order:
                        si, ei = day_order.index(start_d), day_order.index(end_d)
                        for i in range(si, ei + 1):
                            allowed.add(day_order[i])
                else:
                    for d in day_order:
                        if d in days_lower:
                            allowed.add(d)

                if allowed and day_abbr.lower()[:3] not in allowed:
                    return (f"Sorry, {data['doctor']} is not available on {day_name}. "
                            f"They are available {available_days_str}. Please choose another date."), {}

            data["date"] = parsed.strftime("%d %B %Y")
            state = "waiting_time"
            set_session(user_id, "waiting_time", data)
            avail_hours = data.get("available_hours", "8:00 AM - 8:00 PM")
            reply = f"Got it, {data['date']}. At what time? The doctor is available {avail_hours}."
            return reply, {"data": {"available_hours": avail_hours}}
        return "Sorry, I didn't catch the date. Please say it again.", {}

    elif state == "waiting_time":
        avail_hours = data.get("available_hours", "8:00 AM - 8:00 PM")
        allowed_start, allowed_end = parse_available_hours(avail_hours)

        # Map word numbers (English + Hindi + Marathi) to digits
        word_to_num = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12,
            "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
            "chhe": 6, "che": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
            "gyarah": 11, "barah": 12,
        }

        detected_hour = None
        is_pm = any(w in text.lower() for w in ["pm", "evening", "sham", "shaam", "raat", "night", "afternoon", "dopahar", "duphar"])
        is_am = any(w in text.lower() for w in ["am", "morning", "subah", "savere"])

        # Try digit first
        for word in text.split():
            if word.isdigit():
                detected_hour = int(word)
                break

        # Try HH:MM format (e.g. "12:00", "6:30", "7:00pm")
        if detected_hour is None:
            import re
            m = re.search(r'(\d{1,2}):\d{2}', text)
            if m:
                detected_hour = int(m.group(1))

        # Try word-form numbers
        if detected_hour is None:
            for word in text.lower().split():
                if word in word_to_num:
                    detected_hour = word_to_num[word]
                    break

        if detected_hour:
            if is_pm and detected_hour != 12:
                h24 = detected_hour + 12
            elif is_am and detected_hour == 12:
                h24 = 0
            elif not is_am and not is_pm and 1 <= detected_hour <= 7:
                # Ambiguous low hour with no AM/PM — assume PM (afternoon/evening)
                h24 = detected_hour + 12
            else:
                h24 = detected_hour
            if not (allowed_start <= h24 <= allowed_end):
                return f"Sorry, the doctor is only available {avail_hours}.", {}
            data["time"] = f"{h24:02d}:00"
            state = "confirming"
            set_session(user_id, "confirming", data)
            return f"Confirm appointment with {data['doctor']} on {data['date']} at {data['time']}?", {}
        return "Sorry, I didn't catch the time.", {}

    elif state == "confirming":
        confirm_words = ["yes", "confirm", "ok", "sure", "theek", "ha", "haa", "han",
                         "haan", "ho", "bilkul", "zaroor", "correct", "right", "book",
                         "please", "karo", "kar", "done", "proceed", "aage"]
        cancel_words  = ["no", "nahi", "naa", "cancel", "band", "mat", "don't", "dont", "stop",
                         # Marathi
                         "nako", "nahi",
                         # Tamil
                         "illai", "venda",
                         # Telugu
                         "kadu", "vaddu",
                         # Gujarati
                         "na", "nahi"]

        if any(w in text for w in confirm_words):
            # Using data instead of global user_data
            pid = data.get("patient_id")
            if pid is None and str(user_id).isdigit():
                pid = int(user_id)
            name = data.get("name", "Patient")
            phone = data.get("phone", "")
            patient = get_or_create_patient(name, phone, lang) if phone else {"patient_id": pid}
            final_pid = patient.get("patient_id") or pid
            aid = create_appointment(final_pid, data["doctor_id"], data["date"], data["time"], data["dept"], lang)
            if aid == "slot_taken":
                return f"Sorry, {data['doctor']} is already booked at {data['time']} on {data['date']}. Please choose another time.", {}
            if aid:
                delete_session(user_id)
                return "Confirmed! Your appointment is booked.", {"booked": True}
            delete_session(user_id)
            return "You already have an appointment with this doctor on that date.", {}
        elif any(w in text for w in cancel_words):
            delete_session(user_id)
            return "Booking cancelled. Say 'book appointment' to restart.", {}
        else:
            return f"Please confirm — shall I book with {data['doctor']} on {data['date']} at {data['time']}? Say yes or no.", {}

    return "Sorry, I'm not sure how to respond to that.", {}
