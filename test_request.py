import requests

url = "http://127.0.0.1:8000/process-audio"

audio_path = r"C:\Users\sarva\OneDrive\ドキュメント\Sound Recordings\Recording (2).m4a"

with open(audio_path, "rb") as f:
    files = {"audio": f}
    print("Sending request...")
    r = requests.post(url, files=files)
    print("Status:", r.status_code)
    print("Response:", r.text)
