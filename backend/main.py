from fastapi import FastAPI, UploadFile, File
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

    # Force safe language
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
        user_data[user_id] = {}

    state = user_state[user_id]

    # ---------------- CANCEL ----------------
    if any(w in text for w in ["cancel", "stop", "exit"]):
        user_state[user_id] = "idle"
        user_data[user_id] = {}
        return "Okay, I have cancelled your request. How can I help you now?"

    # ---------------- GREETING (RESET) ----------------
    if any(w in text for w in ["hello", "hi", "namaste", "hey"]):
        user_state[user_id] = "idle"
        user_data[user_id] = {}
        return "Hello! How can I help you?"

    # ---------------- DIRECT DOCTOR BOOKING ----------------
    for dept in doctors_by_dept:
        for doc in doctors_by_dept[dept]:
            if doc.lower() in text:
                user_state[user_id] = "waiting_date"
                user_data[user_id] = {"doctor": doc, "dept": dept}
                return f"Okay. Appointment with {doc}. On which date?"

    # ---------------- START BOOKING ----------------
    if any(w in text for w in ["appointment", "book", "schedule"]):
        user_state[user_id] = "waiting_problem"
        user_data[user_id] = {}
        return "What problem are you facing?"
    
    
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
                doctors = doctors_by_dept.get(dept, [])

                user_state[user_id] = "waiting_doctor"

                return (
                    f"You should visit {dept}. "
                    f"Available doctors are: {', '.join(doctors)}. "
                    f"Do you have any preference?"
                )
    return "Please describe your health problem."




    # ---------------- DOCTOR ----------------
    if state == "waiting_doctor":

        if any(w in text for w in ["no", "anyone", "any", "whatever"]):

            dept = user_data[user_id]["dept"]
            doctor = doctors_by_dept[dept][0]

            user_data[user_id]["doctor"] = doctor
            user_state[user_id] = "waiting_date"

            return f"Okay. I will assign {doctor}. On which date?"

        for dept in doctors_by_dept:
            for doc in doctors_by_dept[dept]:
                if doc.lower() in text:

                    user_data[user_id]["doctor"] = doc
                    user_state[user_id] = "waiting_date"

                    return f"Okay. Appointment with {doc}. On which date?"

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
            f"Please confirm. Appointment with {d['doctor']} "
            f"on {d['date']} at {d['time']}. Say yes or no."
        )

    # ---------------- CONFIRM ----------------
    if state == "confirming":

        if "yes" in text:

            d = user_data[user_id]

            user_state[user_id] = "idle"
            user_data[user_id] = {}

            return (
                f"Your appointment with {d['doctor']} "
                f"on {d['date']} at {d['time']} is confirmed. Thank you."
            )

        else:
            user_state[user_id] = "idle"
            user_data[user_id] = {}

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

    # Logic
    reply_english = generate_reply(english_text, "user1")

    # Translate back
    final_reply = translate_back(reply_english, lang)
    print("RAW:", original_text)
    print("EN:", english_text)
    print("LANG:", lang)

    # TTS language
    if lang in supported:
        tts_lang = lang
    else:
        tts_lang = "en"

    # TTS
    output_path = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=final_reply, lang=tts_lang).save(output_path)

    return FileResponse(output_path, media_type="audio/mpeg")

# ------------------ DEBUG API ------------------

@app.post("/speech-to-text")
async def speech_to_text_only(audio: UploadFile = File(...)):

    input_path = f"{TEMP_DIR}/{uuid.uuid4()}.wav"

    with open(input_path, "wb") as f:
        f.write(await audio.read())

    text = speech_to_text(input_path)

    return JSONResponse({
        "transcript": text
    })
