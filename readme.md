# AI Voice Hospital System 🎙️🏥

An AI-powered multilingual voice assistant that simplifies hospital appointment booking. Patients can speak in Hindi, Marathi, or English to book appointments, view their history, and interact with the system hands-free.

---

## 👥 Team

- Sarvami Agarwal
- Shravani Wankhade
- Tanishka Shinde

---

## 🚀 How to Start the Project

### Prerequisites
Make sure you have the following installed:
- Python 3.10+
- Node.js (for Live Server in VS Code)
- VS Code with Live Server extension

### Step 1 — Clone the Repository
\\\ash
git clone https://github.com/Sarvami/ai-voice-hospital-system.git
cd ai-voice-hospital-system
\\\

### Step 2 — Set Up the Backend
\\\ash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
\\\

### Step 3 — Set Up Environment Variables
Create a \.env\ file inside the \ackend/\ folder:
\\\
ASSEMBLYAI_API_KEY=your_assemblyai_key_here
\\\
Get your free API key from https://www.assemblyai.com

### Step 4 — Start the Backend Server
\\\ash
cd backend
uvicorn main:app --reload
\\\
Backend will run at \http://127.0.0.1:8000\

### Step 5 — Start the Frontend
\\\ash
cd frontend
python -m http.server 5500
\\\
Then open \http://localhost:5500/login.html\ in your browser.

---

## 🗄️ Database Setup (First Time Only)

\\\ash
cd backend
python seed_doctors.py
python setup_doctors.py
\\\

---

## 🔑 Default Login Credentials

### Admin
- Email: \dmin@gmail.com\
- Password: \dmin123\

### Patient (Sample)
- Phone: \9921523959\
- Password: \hello123\

### Doctor
- Doctor ID: \DOC20\ through \DOC69\
- Password: \doctor123\"

cd C:\Users\sarva\ai-voice-hospital-system
Set-Content README.md -Encoding UTF8 

### Environment Setup
Create a file called `.env` inside the `backend/` folder:
ASSEMBLYAI_API_KEY=your_assemblyai_key_here

Get your free API key from https://www.assemblyai.com
