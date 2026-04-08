# AI Voice Hospital System 🎙️🏥

An AI-powered multilingual voice assistant that simplifies hospital appointment booking. Patients can speak in Hindi, Marathi, or English to book appointments, view their history, and interact with the system hands-free.

---

## 👥 Team

- Sarvami Agarwal
- Shravani Wankhade
- Tanishka Shinde

---

## ✨ Features

- 🎙️ **Voice-to-text** via AssemblyAI — speak naturally to book appointments
- 🌐 **Multilingual support** — English, Hindi, and Marathi
- 💬 **Multilingual subtitles** — UI captions display in the user's selected language
- 📅 **Calendar popup** — visual date picker for appointment selection
- 🗺️ **Region-based doctor filtering** — find doctors near you
- 👨‍⚕️ **Doctor dashboard** — doctors can view their appointments and patient stats
- 🛠️ **Admin dashboard** — manage patients, doctors, and appointments
- 🔐 **Auth system** — separate login for patients, doctors, and admin
- 🔊 **Text-to-speech replies** — bot responds with audio in the chosen language

---

## 🚀 How to Start the Project

### Prerequisites
- Python 3.10+
- Node.js (optional, for VS Code Live Server)
- VS Code with Live Server extension (optional)

### Step 1 — Clone the Repository
```bash
git clone https://github.com/Sarvami/ai-voice-hospital-system.git
cd ai-voice-hospital-system
```

### Step 2 — Set Up the Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### Step 3 — Set Up Environment Variables
Create a `.env` file inside the `backend/` folder:
```
ASSEMBLYAI_API_KEY=your_assemblyai_key_here
```
Get your free API key from https://www.assemblyai.com

### Step 4 — Set Up the Database (First Time Only)
```bash
cd backend
python seed_doctors.py
python setup_doctors.py
```

### Step 5 — Start the Backend Server
```bash
cd backend
uvicorn main:app --reload
```
Backend runs at `http://127.0.0.1:8000`

### Step 6 — Start the Frontend
```bash
cd frontend
python -m http.server 5500
```
Then open `http://localhost:5500/login.html` in your browser.

---

## 🗄️ Project Structure

```
ai-voice-hospital-system/
├── backend/
│   ├── main.py              # FastAPI app — all routes and voice logic
│   ├── database.py          # SQLAlchemy models
│   ├── seed_doctors.py      # Seeds doctor data into DB
│   ├── setup_doctors.py     # Additional DB setup
│   └── .env                 # API keys (not committed)
├── database/
│   └── hospital.db          # SQLite database
└── frontend/
    ├── login.html
    ├── index.html           # Main patient voice interface
    ├── admin.html           # Admin dashboard
    ├── doctor.html          # Doctor dashboard
    └── app.js               # Core frontend logic + subtitle system
```

---

## 🔑 Default Login Credentials

### Admin
- Email: `admin@gmail.com`
- Password: `admin123`

### Patient (Sample)
- Phone: `9921523959`
- Password: `hello123`

### Doctor
- Doctor ID: `DOC20` through `DOC69`
- Password: `doctor123`

---

## 🌐 Supported Languages

| Code | Language |
|------|----------|
| `en` | English  |
| `hi` | Hindi    |
| `mr` | Marathi  |

Voice input, bot replies, audio output, and UI subtitles all adapt to the selected language.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/process-audio` | Upload audio, get voice reply |
| POST | `/process-text` | Send text, get voice reply |
| POST | `/register` | Register a new patient |
| POST | `/login` | Login (patient / doctor / admin) |
| GET | `/doctors` | List all doctors |
| GET | `/admin/overview` | Patient, doctor, appointment counts |
| GET | `/admin/appointments` | All appointments (admin view) |
| GET | `/admin/patients` | All patients |
| GET | `/admin/doctors` | All doctors |
| POST | `/admin/add-doctor` | Add a new doctor |
| GET | `/doctor/dashboard` | Doctor stats |
| GET | `/doctor/appointments` | Doctor's appointments |
| GET | `/patient/appointments` | Patient's appointments |
| POST | `/set-appointment-date` | Set date from calendar picker |
| POST | `/set-region` | Set region for doctor filtering |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python) |
| Database | SQLite |
| Speech-to-Text | AssemblyAI |
| Text-to-Speech | gTTS |
| Translation | googletrans |
| Date Parsing | dateparser |
| Frontend | HTML, CSS, Vanilla JS |
| Auth | bcrypt (passlib) |