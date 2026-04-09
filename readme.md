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
- 👨‍⚕️ **Doctor dashboard** — view appointments and patient stats.
- 🛠️ **Admin dashboard** — fully manage patients (view details, edit profiles) and doctors.
- 🔐 **Secure Auth** — separate portals for patients, doctors, and hospital administrators.
- 🔊 **Text-to-speech replies** — natural audio responses in the user's language.

---

## 🚀 How to Start the Project

### Prerequisites
- Python 3.10+
- `.env` file in `backend/` with `ASSEMBLYAI_API_KEY`.

### One-Click Setup & Fix
If you are setting up for the first time or need to sync your database with the latest features, simply run:
```bash
python fix_all_data.py
```
This script automatically initializes the database, seeds 50 doctors with full profiles, and ensures all columns are perfectly aligned.

### Standard Execution
1. **Start the Backend:**
   ```bash
   cd backend
   venv\Scripts\activate
   uvicorn main:app --reload
   ```
2. **Start the Frontend:**
   Open `login.html` (in `frontend/`) using VS Code Live Server or any local server.

---

## 🗄️ Project Structure

```
ai-voice-hospital-system/
├── backend/
│   ├── main.py              # FastAPI app & Core Voice Logic
│   ├── database.py          # SQLAlchemy Models & Schema
│   └── seeders/             # Data seeding scripts
├── frontend/
│   ├── indexx.html          # Main Patient Voice Interface
│   ├── admin/               # Admin Dashboard (admin_dashboard.html)
│   ├── doctor/              # Doctor Dashboard (doctor_dashboard.html)
│   └── script.js            # Core Voice Logic & Region Management
└── fix_all_data.py          # Master Setup/Repair Script
```

---

## 🔑 Login Credentials

### Admin
- Email: `admin@gmail.com`
- Password: `admin123`

### Doctor
- Doctor ID: `DOC1` to `DOC50`
- Password: `doctor123`

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
| GET | `/admin/patients` | Fetch all patient details (Admin only) |
| PUT | `/admin/update-patient` | Administratively edit patient data |
| GET | `/doctors/by-region` | Get doctors filtered by location |

---

## 🛠️ Tech Stack
FastAPI, SQLite (SQLAlchemy), AssemblyAI (STT), gTTS (TTS), GoogleTrans, Vanilla JS/CSS.