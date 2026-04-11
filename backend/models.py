from pydantic import BaseModel

class TextInput(BaseModel):
    text: str
    lang: str = "en"
    patient_id: int = 0

class AddDoctorRequest(BaseModel):
    name: str
    department: str
    qualification: str
    experience_years: int
    doc_id: str
    password: str
    region: str
    available_days: str = ""
    available_hours: str = "8:00 AM - 8:00 PM"

class UpdateDoctorRequest(BaseModel):
    doctor_id: int
    name: str
    department: str
    qualification: str
    experience_years: int
    doc_id: str
    region: str
    available_days: str
    available_hours: str
    contact_phone: str
    email: str

class DateRequest(BaseModel):
    patient_id: str
    date: str
    doctor_id: int = None
    lang: str = "en"

class RegionRequest(BaseModel):
    patient_id: str
    region: str
    doctor_id: int = None
    lang: str = "en"

class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "en"

class RateRequest(BaseModel):
    appointment_id: int
    rating: int
    review: str = ""

class UpdatePatientRequest(BaseModel):
    patient_id: int
    name: str
    age: int
    gender: str
    phone: str
    preferred_language: str
