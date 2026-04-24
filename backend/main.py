import os
import uuid
import time
import sqlite3
import sys
import warnings
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
from fastapi import FastAPI, UploadFile, File, Form, Request, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from gtts import gTTS
from pathlib import Path

# Ensure local backend modules resolve for both:
# - `uvicorn main:app` (from backend/)
# - `uvicorn backend.main:app` (from repo root)
BACKEND_DIR = Path(__file__).parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Local imports
from database import get_db
from models import TextInput, TranslateRequest
from voice_service import (
    speech_to_text, gt_to_english, gt_from_english, 
    generate_reply
)
from deep_translator import GoogleTranslator
import routes_patient
import routes_doctor
import routes_admin

# ------------------ SETUP ------------------
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

app = FastAPI(title="SwasthSeva API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

# Include Routers
app.include_router(routes_patient.router)
app.include_router(routes_doctor.router)
app.include_router(routes_admin.router, prefix="/api/admin")

# ------------------ CORE VOICE API ------------------

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
        reply, meta = generate_reply(english, user_id=str(patient_id), lang=lang, original=original)
        final = gt_from_english(reply, lang)

        print(f"\n{'─'*50}")
        print(f"  original  : {original}")
        print(f"  english   : {english}")
        print(f"  reply     : {reply}")
        print(f"  translated: {final}")
        print(f"  intent    : {meta.get('intent', '—')}  |  state: {meta.get('data', {})}")
        print(f"{'─'*50}\n")

    except Exception as e:
        print("ERROR in process_audio:", e)
        final = "Sorry, something went wrong. Please try again."
        reply = final
        original = ""
        meta = {}
    finally:
        if os.path.exists(path):
            os.remove(path)

    out_filename = f"{uuid.uuid4()}.mp3"
    out_path = os.path.join(TEMP_DIR, out_filename)
    gTTS(text=final, lang=lang).save(out_path)
    audio_url = f"/temp-audio/{out_filename}"

    return JSONResponse({
        "text": reply,
        "original_text": original,
        "reply_in_lang": final,
        "audio_url": audio_url,
        "booked": meta.get("booked", False),
        "intent": meta.get("intent", ""),
        "doctor_id": meta.get("data", {}).get("doctor_id"),
        "available_days": meta.get("data", {}).get("available_days", ""),
        "doctors": meta.get("data", {}).get("doctors", [])
    })

@app.post("/process-text")
def process_text(data: TextInput):
    try:
        english = gt_to_english(data.text)
        reply, meta = generate_reply(english, user_id=str(data.patient_id), lang=data.lang, original=data.text)
        final = gt_from_english(reply, data.lang)
    except Exception as e:
        print("ERROR in process_text:", e)
        final = "Sorry, something went wrong. Please try again."
        reply = final
        meta = {}

    try:
        out_filename = f"{uuid.uuid4()}.mp3"
        out_path = os.path.join(TEMP_DIR, out_filename)
        gTTS(text=final, lang=data.lang).save(out_path)
        audio_url = f"/temp-audio/{out_filename}"
    except Exception as e:
        print("ERROR generating TTS in process_text:", e)
        audio_url = ""

    return JSONResponse({
        "text": reply,
        "original_text": data.text,
        "reply_in_lang": final,
        "audio_url": audio_url,
        "booked": meta.get("booked", False),
        "intent": meta.get("intent", ""),
        "doctor_id": meta.get("data", {}).get("doctor_id"),
        "available_days": meta.get("data", {}).get("available_days", ""),
        "doctors": meta.get("data", {}).get("doctors", [])
    })

# ------------------ UTILITY APIs ------------------

@app.get("/")
async def root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "SwasthSeva API Running"}

# Mount other static folders explicitly to avoid root conflicts
if (FRONTEND_DIR / "doctor").exists():
    app.mount("/doctor", StaticFiles(directory=str(FRONTEND_DIR / "doctor")), name="doctor_ui")
if (FRONTEND_DIR / "patient").exists():
    app.mount("/patient", StaticFiles(directory=str(FRONTEND_DIR / "patient")), name="patient_ui")
if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

@app.get("/temp-audio/{filename}")
async def serve_temp_audio(filename: str):
    path = f"{TEMP_DIR}/{filename}"
    if os.path.exists(path):
        return FileResponse(path, media_type="audio/mpeg")
    return JSONResponse({"error": "File not found"}, status_code=404)

@app.post("/translate-text")
def translate_text_api(req: TranslateRequest):
    try:
        translated = GoogleTranslator(source='auto', target=req.target_lang).translate(req.text)
        return {"success": True, "translation": translated}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/doctors")
async def get_all_doctors(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM doctors").fetchall()
    return {"doctors": [dict(d) for d in rows]}

# Start server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)