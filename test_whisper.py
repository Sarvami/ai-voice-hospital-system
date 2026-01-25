from faster_whisper import WhisperModel

print("STEP 0: Starting script")

audio_path = r"C:\Users\sarva\OneDrive\ドキュメント\Sound Recordings\Recording (2).m4a"

print("STEP 1: Creating WhisperModel (this may take time)...")

model = WhisperModel("./whisper_model", device="cpu", compute_type="int8")


print("STEP 2: Model created successfully")

print("STEP 3: Starting transcription...")
segments, info = model.transcribe(audio_path, beam_size=1)
segments = list(segments)

print("STEP 4: Transcription finished")
print("Detected language:", info.language)

for s in segments:
    print("SEGMENT:", s.text)

print("DONE")
