import os
import uuid
import time
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from gtts import gTTS
from pathlib import Path

# Local imports
from database import get_db_connection
from models import TextInput, TranslateRequest
from voice_service import (
    speech_to_text, gt_to_english, gt_from_english, 
    generate_reply, user_state, translator
)
import routes_patient
import routes_doctor
import routes_admin

# ------------------ SETUP ------------------
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

app = FastAPI(title="AI Voice Hospital API")

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

# Include Routers
app.include_router(routes_patient.router)
app.include_router(routes_doctor.router)
app.include_router(routes_admin.router)

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
        
        # Inject availability if present
        if meta.get("data", {}).get("available_hours"):
            hours = meta["data"]["available_hours"]
            if hours != "8:00 AM - 8:00 PM":
                final += f" ({hours})"

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
        "doctor_id": meta.get("data", {}).get("doctor_id")
    })

@app.post("/process-text")
def process_text(data: TextInput):
    english = gt_to_english(data.text)
    reply, meta = generate_reply(english, user_id=str(data.patient_id), lang=data.lang, original=data.text)
    final = gt_from_english(reply, data.lang)

    out_filename = f"{uuid.uuid4()}.mp3"
    out_path = os.path.join(TEMP_DIR, out_filename)
    gTTS(text=final, lang=data.lang).save(out_path)

    return JSONResponse({
        "text": reply,
        "original_text": data.text,
        "reply_in_lang": final,
        "audio_url": f"/temp-audio/{out_filename}",
        "booked": meta.get("booked", False),
        "doctor_id": meta.get("data", {}).get("doctor_id")
    })

# ------------------ UTILITY APIs ------------------

@app.get("/")
async def root():
    return {"status": "AI Voice Hospital System API Running"}

@app.get("/temp-audio/{filename}")
async def serve_temp_audio(filename: str):
    path = f"{TEMP_DIR}/{filename}"
    if os.path.exists(path):
        return FileResponse(path, media_type="audio/mpeg")
    return JSONResponse({"error": "File not found"}, status_code=404)

@app.post("/translate-text")
def translate_text_api(req: TranslateRequest):
    try:
        translated = translator.translate(req.text, dest=req.target_lang).text
        return {"success": True, "translation": translated}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/doctors")
async def get_all_doctors():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM doctors").fetchall()
    conn.close()
    return {"doctors": [dict(d) for d in rows]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)