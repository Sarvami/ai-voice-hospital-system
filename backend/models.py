from pydantic import BaseModel, field_validator, Field
from typing import Optional
import re

VALID_LANGS   = {"en", "hi", "mr", "ta", "te", "gu", "bn", "kn", "pa"}
VALID_REGIONS = {"Bibewadi", "Kalyani Nagar", "Ravet", "PCMC", "Sangamvadi", "Wanowrie", "Hadapsar"}
VALID_GENDERS = {"Male", "Female", "Other", "Unknown"}

class TextInput(BaseModel):
    text: str
    lang: str = "en"
    patient_id: int = 0

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v):
        if v not in VALID_LANGS:
            return "en"  # fallback gracefully
        return v

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("text cannot be empty")
        return v.strip()


class AddDoctorRequest(BaseModel):
    name: str
    department: str
    qualification: str
    experience_years: int = Field(..., ge=0, le=60)
    doc_id: str
    password: str = Field(..., min_length=4)
    region: str
    available_days: str = ""
    available_hours: str = "8:00 AM - 8:00 PM"

    @field_validator("name", "department", "qualification", "doc_id")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("field cannot be empty")
        return v.strip()

    @field_validator("available_hours")
    @classmethod
    def validate_hours(cls, v):
        pattern = r'^\d{1,2}:\d{2} (AM|PM) - \d{1,2}:\d{2} (AM|PM)$'
        if v and not re.match(pattern, v):
            raise ValueError("available_hours must be in format: H:MM AM/PM - H:MM AM/PM")
        return v


class UpdateDoctorRequest(BaseModel):
    doctor_id: int
    name: str
    department: str
    qualification: str
    experience_years: int = Field(..., ge=0, le=60)
    doc_id: str
    region: str
    available_days: str
    available_hours: str
    contact_phone: str
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("invalid email address")
        return v


class DateRequest(BaseModel):
    patient_id: str
    date: str
    doctor_id: Optional[int] = None
    lang: str = "en"

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v):
        return v if v in VALID_LANGS else "en"


class RegionRequest(BaseModel):
    patient_id: str
    region: str
    doctor_id: Optional[int] = None
    lang: str = "en"

    @field_validator("region")
    @classmethod
    def validate_region(cls, v):
        if v not in VALID_REGIONS:
            raise ValueError(f"region must be one of: {', '.join(VALID_REGIONS)}")
        return v

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v):
        return v if v in VALID_LANGS else "en"


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "en"

    @field_validator("target_lang")
    @classmethod
    def validate_lang(cls, v):
        return v if v in VALID_LANGS else "en"


class RateRequest(BaseModel):
    appointment_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    review: str = ""

    @field_validator("review")
    @classmethod
    def trim_review(cls, v):
        return v.strip()[:1000] if v else ""  # cap at 1000 chars


class CancelAppointmentRequest(BaseModel):
    doctor_id: int = Field(..., gt=0)
    cancellation_reason: str = Field(..., min_length=5, max_length=500)

    @field_validator("cancellation_reason")
    @classmethod
    def trim_reason(cls, v):
        cleaned = v.strip()
        if len(cleaned) < 5:
            raise ValueError("cancellation_reason must be at least 5 characters")
        return cleaned


class UpdatePatientRequest(BaseModel):
    patient_id: int = Field(..., gt=0)
    name: str
    age: int = Field(..., ge=0, le=150)
    gender: str
    phone: str
    email: Optional[str] = None
    preferred_language: str = "en"

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v not in VALID_GENDERS:
            raise ValueError(f"gender must be one of: {', '.join(VALID_GENDERS)}")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^\d{10}$', v):
            raise ValueError("phone must be a 10-digit number")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v and ("@" not in v or "." not in v):
            raise ValueError("invalid email address")
        return v

    @field_validator("preferred_language")
    @classmethod
    def validate_lang(cls, v):
        return v if v in VALID_LANGS else "en"


class OtpRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^\d{10}$', v.strip()):
            raise ValueError("phone must be a 10-digit number")
        return v.strip()


class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str
