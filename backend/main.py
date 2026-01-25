from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from googletrans import Translator
from dotenv import load_dotenv
from gtts import gTTS
import requests
import uuid
import os
import time

load_dotenv()

API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

app = FastAPI()

translator = Translator()

TEMP_DIR = "temp"
supported = ["en", "hi", "mr"]

os.makedirs(TEMP_DIR, exist_ok=True)


# ------------------ STT ------------------

def speech_to_text(audio_path):

    headers = {"authorization": API_KEY}

    # Upload audio
    with open(audio_path, "rb") as f:
        upload_res = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=f
        )

    audio_url = upload_res.json()["upload_url"]

    # Request transcription
    transcript_res = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json={"audio_url": audio_url}
    )

    transcript_id = transcript_res.json()["id"]

    # Poll until done
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

    # returns english text + detected language
    return result.text, result.src


def translate_back(text, lang):

    if lang == "en":
        return text

    result = translator.translate(text, dest=lang)
    return result.text


# ------------------ LOGIC ------------------

def generate_reply(text):

    text = text.lower()

    if "book" in text or "appointment" in text:
        return "Sure. Which department would you like to book?"

    if "hello" in text or "hi" in text:
        return "Hello! How can I help you?"

    if "doctor" in text:
        return "Which doctor are you looking for?"

    return "Sorry, I did not understand. Please repeat."


# ------------------ MAIN AUDIO API ------------------

@app.post("/process-audio")
async def process_audio(audio: UploadFile = File(...)):

    input_path = f"{TEMP_DIR}/{uuid.uuid4()}.wav"

    with open(input_path, "wb") as f:
        f.write(await audio.read())

    # STT
    original_text = speech_to_text(input_path)

    # Translate to English + detect language
    english_text, lang = translate_to_english(original_text)

    # Logic
    reply_english = generate_reply(english_text)

    # Translate back to user language
    final_reply = translate_back(reply_english, lang)

        # Select TTS language
    supported = ["en", "hi", "mr"]

    if lang in supported:
        tts_lang = lang
    else:
        tts_lang = "en"   # fallback for gu, etc.

    # TTS
    output_path = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=final_reply, lang=tts_lang).save(output_path)

    return FileResponse(output_path, media_type="audio/mpeg")



# ------------------ DEBUG STT API ------------------

@app.post("/speech-to-text")
async def speech_to_text_only(audio: UploadFile = File(...)):

    input_path = f"{TEMP_DIR}/{uuid.uuid4()}.wav"

    with open(input_path, "wb") as f:
        f.write(await audio.read())

    text = speech_to_text(input_path)

    return JSONResponse({
        "transcript": text
    })
