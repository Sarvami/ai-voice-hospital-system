# database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import os

# Create database directory if it doesn't exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DB_DIR, exist_ok=True)

# SQLite database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_DIR}/hospital.db"
DB_PATH = os.path.join(DB_DIR, "hospital.db")

import sqlite3
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    """FastAPI dependency — yields a connection and closes it after the request."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# ------------------ MODELS ------------------

class Doctor(Base):
    __tablename__ = "doctors"
    
    doctor_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    qualification = Column(String)
    experience_years = Column(Integer)
    available_days = Column(String)
    available_hours = Column(String)
    doc_id = Column(String, unique=True)
    password_hash = Column(String)
    contact_phone = Column(String)
    email = Column(String)
    region = Column(String)
    rating = Column(Float, default=4.5)
    rating_count = Column(Integer, default=10)
    appointments = relationship("Appointment", back_populates="doctor")
    
    def __repr__(self):
        return f"<Doctor(doctor_id={self.doctor_id}, name={self.name}, department={self.department})>"

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    phone = Column(String, unique=True, index=True)
    email = Column(String, nullable=True)
    otp = Column(String, nullable=True)
    otp_expiry = Column(String, nullable=True)
    preferred_language = Column(String, default="en")
    password_hash = Column(String, nullable=False)
    region = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    appointments = relationship("Appointment", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(id={self.id}, name={self.name})>"

class Appointment(Base):
    __tablename__ = "appointments"
    
    appointment_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"))
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id"))
    appointment_date = Column(String, nullable=False)
    appointment_time = Column(String, nullable=False)
    status = Column(String, default="Booked")
    reason = Column(Text)
    booking_source = Column(String, default="voice")
    language_used = Column(String, default="en")
    rating = Column(Integer) # Patient rating for this appointment
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    
    def __repr__(self):
        return f"<Appointment(appointment_id={self.appointment_id}, patient_id={self.patient_id}, doctor_id={self.doctor_id})>"

class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    patient_id = Column(String, primary_key=True)
    state = Column(String, default="idle")
    data = Column(Text) # JSON string
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Create messages table via raw SQL (not in SQLAlchemy models to keep it simple)
def _create_messages_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id     INTEGER NOT NULL,
            sender_role   TEXT NOT NULL,
            receiver_id   INTEGER NOT NULL,
            receiver_role TEXT NOT NULL,
            appointment_id INTEGER,
            message_text  TEXT NOT NULL,
            is_read       INTEGER DEFAULT 0,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

_create_messages_table()

def _create_meet_links_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meet_links (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id      INTEGER NOT NULL,
            patient_id     INTEGER NOT NULL,
            appointment_id INTEGER,
            meet_link      TEXT NOT NULL,
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            scheduled_time TEXT,
            status         TEXT DEFAULT 'active'
        )
    """)
    conn.commit()
    conn.close()

_create_meet_links_table()

# SQLAlchemy Database dependency (unused by current repositories)
def get_sqlalchemy_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()