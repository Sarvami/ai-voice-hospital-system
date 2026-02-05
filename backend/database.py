# database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import os

# Create database directory if it doesn't exist
DB_DIR = "data"
os.makedirs(DB_DIR, exist_ok=True)

# SQLite database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_DIR}/hospital.db"

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
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    qualification = Column(String)
    experience_years = Column(Integer)
    available_days = Column(String)
    appointments = relationship("Appointment", back_populates="doctor")
    
    def __repr__(self):
        return f"<Doctor(id={self.id}, name={self.name}, department={self.department})>"

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    phone = Column(String)
    preferred_language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    appointments = relationship("Appointment", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(id={self.id}, name={self.name})>"

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    appointment_date = Column(String, nullable=False)
    appointment_time = Column(String, nullable=False)
    status = Column(String, default="Booked")
    reason = Column(Text)
    booking_source = Column(String, default="voice")
    language_used = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id})>"

# Create tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()