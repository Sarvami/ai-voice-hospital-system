from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from gtts import gTTS
import requests
import uuid
import os
import time

load_dotenv()

API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

app = FastAPI()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


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


@app.post("/process-audio")
async def process_audio(audio: UploadFile = File(...)):
    input_path = f"{TEMP_DIR}/{uuid.uuid4()}.wav"
    with open(input_path, "wb") as f:
        f.write(await audio.read())

    # STT
    text = speech_to_text(input_path)

    # TTS
    output_path = f"{TEMP_DIR}/{uuid.uuid4()}.mp3"
    gTTS(text=text, lang="en").save(output_path)

    return FileResponse(output_path, media_type="audio/mpeg")

from fastapi.responses import JSONResponse

@app.post("/speech-to-text")
async def speech_to_text_only(audio: UploadFile = File(...)):
    input_path = f"{TEMP_DIR}/{uuid.uuid4()}.wav"
    with open(input_path, "wb") as f:
        f.write(await audio.read())

    text = speech_to_text(input_path)

    return JSONResponse({
        "transcript": text
    })