# AI Voice Hospital System 🎙️🏥

An AI-powered multilingual voice assistant that simplifies hospital appointment booking. Patients can speak in Hindi, Marathi, or English to book appointments, manage their health, and interact with the system hands-free.

---

## 👥 Team

- Sarvami Agarwal
- Shravani Wankhade
- Tanishka Shinde

---

## ✨ Features

- 🎙️ **Voice-to-text** via AssemblyAI — speak naturally to book appointments.
- 🌐 **Multilingual support** — English, Hindi, and Marathi.
- 🗺️ **Region-based doctor filtering** — find doctors specifically in your city/area (Bibewadi, PCMC, etc.).
- 👨‍⚕️ **Doctor dashboard** — view appointments, patient list, and ratings received.
- 🛠️ **Admin dashboard** — fully manage patients & doctors (edit profiles, adjust timings, manage regions) and monitor all ratings & reviews.
- 🔐 **Secure Auth** — separate portals for patients, doctors, and hospital administrators.
- 🔊 **Text-to-speech replies** — natural audio responses in the user's language.
- 🕒 **Specialist Scheduling** — supports varied doctor timings (e.g., 2-4 hour "Specialist Hours").
- ⭐ **Doctor Rating System** — patients can rate their doctor after a completed appointment. Ratings of 3 stars or below prompt a mandatory comment box so patients can describe their experience. Low-rated reviews are flagged in red on both the doctor and admin dashboards.

---

## 🚀 How to Start the Project

### Prerequisites
- Python 3.10+
- `.env` file in `backend/` with `ASSEMBLYAI_API_KEY`.

### One-Click Setup & Fix
If you are setting up for the first time or need to sync your database with the latest features (including the new specialist timings), simply run:
```bash
python fix_all_data.py
```
This script automatically initializes the database, seeds 50 doctors with complete profiles (including random specialist hours for variety), and ensures all columns are perfectly aligned.

### Standard Execution
1. **Start the Backend:**
   ```bash
   cd backend
   venv\Scripts\activate
   uvicorn main:app --reload
   ```
2. **Start the Frontend:**
   Open `frontend/index.html` using VS Code Live Server or serve from inside the `frontend/` folder:
   ```bash
   cd frontend
   python -m http.server 5500
   ```
   Then open `http://localhost:5500/pages/login.html`.

---

## 🗄️ Project Structure

```
ai-voice-hospital-system/
├── backend/
│   ├── main.py              # FastAPI app & Core Voice Logic
│   ├── database.py          # SQLAlchemy Models & Schema
│   └── seeders/             # Data seeding scripts (Doctors, Regions, etc.)
├── frontend/
│   ├── index.html           # Main Patient Voice Interface
│   ├── pages/               # login.html, register.html, profile.html
│   ├── shared/              # Shared style.css & script.js
│   ├── admin/               # Admin Dashboard & Assets
│   ├── doctor/              # Doctor Dashboard & Assets
│   └── patient/             # Patient Dashboard & Assets
└── fix_all_data.py          # Master Setup/Repair Script (Team Sync)
```

---

## 🔑 Login Credentials

### Admin
- Email: `admin@gmail.com`
- Password: `admin123`

### Doctor
- Doctor ID: `DOC1` to `DOC50`
- Password: `doctor123`
- *Note: Some doctors now have "Specialist Hours" which will be visible on the Admin and Appointment views.*

### Patient
- Register a new account on the `register.html` page to test the region-filtering features.

---

## 🌐 Supported Regions
Bibewadi, Kalyani Nagar, Ravet, PCMC, Sangamvadi, Wanowrie, Hadapsar.

---

## 🔌 Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/set-region` | Persist user location for filtering |
| POST | `/patient/rate-appointment` | Submit a star rating (+ optional review for ≤3 stars) |
| GET | `/doctor/ratings` | Fetch ratings & reviews for a specific doctor |
| GET | `/admin/ratings` | Fetch all ratings & reviews across all doctors (Admin only) |
| GET | `/admin/patients` | Fetch all patient details (Admin only) |
| PUT | `/admin/update-patient` | Administratively edit patient data |
| PUT | `/admin/update-doctor` | Administratively edit doctor data |
| GET | `/doctors/by-region` | Get doctors filtered by location |

---

## 🛠️ Tech Stack
FastAPI, SQLite (SQLAlchemy), AssemblyAI (STT), gTTS (TTS), GoogleTrans, Vanilla JS/CSS (Dark/Light mode support).