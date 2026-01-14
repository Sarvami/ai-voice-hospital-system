from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "AI Voice Hospital System Backend"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "backend",
        "version": "0.1.0"
    }
