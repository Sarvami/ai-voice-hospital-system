# SwasthSeva 🎙️🏥

An AI-powered multilingual voice assistant that simplifies hospital appointment booking. Patients can speak in their native language to book appointments, manage their health records, and interact with the system hands-free.

---

## 👥 Team

- Sarvami Agarwal
- Shravani Wankhade
- Tanishka Shinde

---

## ✨ Features

- 🎙️ **Voice-to-text** via AssemblyAI — speak naturally to book appointments
- 🌐 **Multilingual support** — Hindi, Marathi, English, Tamil, Telugu, Gujarati
- 🗺️ **Region-based doctor filtering** — finds doctors in your area (Bibewadi, Wanowrie, PCMC, etc.)
- 👨‍⚕️ **Doctor popup** — when only one doctor is available in your area, a card popup shows their name, rating, region, and hours with Yes/No booking buttons
- 📅 **Smart calendar** — greys out past dates and days the doctor doesn't work; shows error message on invalid selection
- � **Specialist scheduling** — respects each doctor's available days and hours; rejects bookings outside their schedule
- ⭐ **Doctor rating system** — patients rate after completed appointments; ratings ≤3 stars show a comment box for feedback; low ratings flagged in red on doctor and admin dashboards
- 📁 **Medical report uploads** — patients can upload blood tests, scans, prescriptions etc. (PDF/JPG/PNG); admins can view them per patient
- 👨‍⚕️ **Doctor dashboard** — appointments calendar, patient list, ratings & reviews
- 🛠️ **Admin dashboard** — manage patients & doctors, view all appointments, ratings, and patient-uploaded reports
- 🔐 **Secure auth** — separate portals for patients, doctors, and admins with bcrypt password hashing
- 🔊 **Text-to-speech replies** — natural audio responses in the user's language via gTTS
- 🌙 **Dark/Light theme** — across all dashboards

---

## 🔄 Project Workflow

### Patient Booking Flow
```
Patient opens index.html
        │
        ▼
Selects language (Hindi/English/Marathi etc.)
        │
        ▼
Taps mic → speaks problem (e.g. "chest pain")
        │
        ▼
AssemblyAI transcribes → Google Translate → English
        │
        ▼
Backend (generate_reply) matches problem to department
        │
        ▼
Finds doctors in patient's region
        │
   ┌────┴────┐
1 doctor   Multiple doctors
   │            │
   ▼            ▼
Doctor      Voice lists all
popup       doctors, patient
(Yes/No)    says a name
   │            │
   └────┬───────┘
        ▼
Calendar popup opens
(unavailable days greyed out)
        │
        ▼
Patient picks date → speaks time
        │
        ▼
Backend validates day + time against doctor's schedule
        │
        ▼
Confirmation prompt → patient says "haan/yes/bilkul"
        │
        ▼
Appointment saved to DB → Success popup shown
```

### Voice State Machine (Backend)
```
idle → waiting_problem → waiting_doctor → waiting_date → waiting_time → confirming → idle
```

### Role-Based Access
```
Login page
    ├── Patient  → patient/patient_dashboard.html
    ├── Doctor   → doctor/doctor_dashboard.html
    └── Admin    → admin/admin_dashboard.html
```

---

## 🚀 How to Start

### Prerequisites
- Python 3.10+
- `.env` file in `backend/` with your `ASSEMBLYAI_API_KEY`

### First-time setup
```bash
python fix_all_data.py
```
Seeds 50 doctors with full profiles, regions, and specialist hours.

### Run (single FastAPI server for frontend + backend)
```bash
venv\Scripts\activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://127.0.0.1:8000/pages/login.html` (or just `/` for the voice assistant home).

---

## 🗄️ Project Structure

```
swasthseva/
├── backend/
│   ├── main.py              # FastAPI app, /process-audio, /process-text
│   ├── voice_service.py     # STT, TTS, state machine, booking logic
│   ├── routes_patient.py    # Login, register, appointments, reports, ratings
│   ├── routes_doctor.py     # Doctor dashboard, patients, ratings
│   ├── routes_admin.py      # Admin CRUD, overview, ratings
│   ├── database.py          # SQLite connection
│   ├── models.py            # Pydantic request models
│   └── seeders/             # DB seeding scripts
├── frontend/
│   ├── index.html           # Main voice assistant interface
│   ├── pages/               # login.html, register.html, profile.html
│   ├── shared/              # style.css, script.js (shared across pages)
│   ├── admin/               # Admin dashboard
│   ├── doctor/              # Doctor dashboard
│   └── patient/             # Patient dashboard
└── fix_all_data.py          # Master setup/repair script
```

---

## 🔑 Login Credentials

| Role | Field | Value |
|------|-------|-------|
| Admin | Email | `admin@gmail.com` |
| Admin | Password | `admin123` |
| Doctor | Doctor ID | `DOC1` – `DOC50` |
| Doctor | Password | `doctor123` |
| Patient | — | Register at `/pages/register.html` |

---

## 🌐 Supported Regions
Bibewadi, Kalyani Nagar, Ravet, PCMC, Sangamvadi, Wanowrie, Hadapsar

---

## 🔌 Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/process-audio` | Core voice pipeline — STT → NLP → TTS |
| POST | `/process-text` | Text-based voice pipeline (used by doctor popup) |
| POST | `/login` | Unified login for patient / doctor / admin |
| POST | `/register` | Patient registration |
| GET | `/patient/appointments` | Patient's appointment history |
| POST | `/patient/rate-appointment` | Submit rating + optional review |
| POST | `/patient/upload-report` | Upload medical report (PDF/JPG/PNG) |
| GET | `/patient/reports` | Fetch patient's uploaded reports |
| DELETE | `/patient/report/{id}` | Delete an uploaded report |
| GET | `/doctor/dashboard` | Doctor profile + stats |
| GET | `/doctor/ratings` | Doctor's ratings and reviews |
| GET | `/admin/ratings` | All ratings across all doctors |
| GET | `/admin/patients` | All patients (with report access) |
| PUT | `/admin/update-doctor` | Edit doctor profile |
| POST | `/set-region` | Save patient's selected region |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Database | SQLite |
| Speech-to-Text | AssemblyAI |
| Text-to-Speech | gTTS |
| Translation | Google Translate (googletrans) |
| Frontend | Vanilla JS, HTML, CSS |
| Auth | bcrypt (passlib) |
| Hosting | Local (single FastAPI server via uvicorn) |
