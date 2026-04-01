# AI Voice Hospital System 🎙️🏥

An AI-powered multilingual voice assistant that simplifies hospital appointment booking. Patients can speak in Hindi, Marathi, or English to book appointments, view their history, and interact with the system hands-free.

---

## 👥 Team

- Sarvami
- Shravani
- Tanishka

---

## 🚀 How to Start the Project

### Prerequisites
Make sure you have the following installed:
- Python 3.10+
- Node.js (for Live Server in VS Code)
- VS Code with Live Server extension

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

### Step 4 — Start the Backend Server
```bash
cd backend
uvicorn main:app --reload
```
Backend will run at `http://127.0.0.1:8000`

### Step 5 — Start the Frontend
Open a new terminal and run:
```bash
cd frontend
python -m http.server 5500
```
Then open `http://localhost:5500/login.html` in your browser.

---

## 🗄️ Database Setup (First Time Only)

If the database is empty or you need to seed doctor data:

```bash
cd backend
python seed_doctors.py
python setup_doctors.py
```

This adds 50 doctors across 10 departments and sets up default login credentials.

---

## 🔑 Default Login Credentials

### Admin
- Phone/ID: `admin`
- Password: `admin123`

### Patient (Sample)
- Phone: `9921523959`
- Password: `hello123`

### Doctor
- Doctor ID: `DOC1` through `DOC50` (stored in the `phone` column)
- Password: `doctor123`
- New doctors added via the admin dashboard follow the same pattern (e.g. `DOC51`, `DOC52`, ...)

---

## 🏗️ Project Structure

```
ai-voice-hospital-system/
├── backend/
│   ├── main.py              # FastAPI backend, all endpoints
│   ├── database.py          # SQLAlchemy models
│   ├── seed_doctors.py      # Seeds 50 doctors into DB
│   ├── setup_doctors.py     # Sets doctor login credentials
│   ├── .env                 # API keys (not committed)
│   └── requirements.txt
├── database/
│   ├── hospital.db          # SQLite database
│   └── schema.sql
├── frontend/
│   ├── login.html           # Login page (Patient/Doctor/Admin)
│   ├── register.html        # Patient registration
│   ├── indexx.html          # Voice assistant (main page)
│   ├── script.js            # Shared JS logic
│   ├── style.css
│   ├── patient/
│   │   ├── patient_dashboard.html
│   │   ├── patient.js
│   │   └── patient.css
│   ├── doctor/
│   │   ├── doctor_dashboard.html
│   │   ├── doctor.js
│   │   └── doctor.css
│   └── admin/
│       ├── admin_dashboard.html
│       ├── admin.js
│       └── admin.css
```

---

## ✅ Features Built

- Patient registration and login
- Doctor login with hospital-issued ID (DOC1–DOC50)
- Admin dashboard with overview, patients, doctors, appointments
- Add new doctors via admin panel
- Multilingual voice interaction (Hindi, Marathi, English)
- Speech-to-text via AssemblyAI
- Auto-translation via Google Translate
- Text-to-speech response via gTTS
- Conversational appointment booking flow
- Symptom → Department mapping
- Doctor selection from available doctors
- Natural language date and time parsing
- Appointment confirmation with booking ID
- Double booking prevention
- Patient dashboard with appointment history
- Doctor dashboard with appointments and stats
- Department query answering ("What department is Dr. X in?")

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| Database | SQLite, SQLAlchemy |
| Speech-to-Text | AssemblyAI |
| Translation | Google Translate (googletrans) |
| Text-to-Speech | gTTS |
| Auth | bcrypt, passlib |
| Frontend | HTML, CSS, JavaScript |
| Date Parsing | dateparser |

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | Login for patient / doctor / admin |
| POST | `/register` | Register new patient |
| POST | `/process-audio` | Send voice recording, get audio response |
| POST | `/process-text` | Send text input, get audio response |
| GET | `/doctors` | Get all doctors |
| GET | `/doctor/dashboard` | Doctor's stats (requires `doctor_id`) |
| GET | `/doctor/appointments` | Doctor's appointments (requires `doctor_id`) |
| GET | `/patient/appointments` | Patient's appointments (requires `patient_id`) |
| GET | `/patient/records` | Patient records — placeholder |
| GET | `/admin/overview` | Total counts: patients, doctors, appointments |
| GET | `/admin/patients` | All patients (name, age, phone, language, registered) |
| GET | `/admin/doctors` | All doctors (name, dept, qualification, experience, days) |
| POST | `/admin/add-doctor` | Add a new doctor with hashed password |
| GET | `/admin/appointments` | All appointments with patient & doctor names |

---

## 📝 Notes

- The voice pipeline supports Hindi (`hi`), Marathi (`mr`), and English (`en`)
- Tamil, Telugu, Gujarati are shown in UI but not yet supported in backend
- State machine resets if the backend server is restarted
- Doctor credentials use the `phone` column to store the DOC-style ID (e.g. `DOC1`)
- Always run the backend before opening the frontend
- Database file lives at `database/hospital.db` relative to the project root; backend connects via `../database/hospital.db`