"""HTTP workflow smoke tests for SwasthSeva API endpoints."""
import io
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from backend.main import app  # noqa: E402

client = TestClient(app)


def _first_patient_id():
    r = client.get("/api/admin/patients")
    assert r.status_code == 200
    patients = r.json()
    if not patients:
        pytest.skip("No patients in database")
    return patients[0]["patient_id"]


def _first_doctor_id():
    r = client.get("/api/admin/doctors")
    assert r.status_code == 200
    doctors = r.json()
    if not doctors:
        pytest.skip("No doctors in database")
    return doctors[0]["doctor_id"]


class TestPublicAndAdmin:
    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200

    def test_doctors_list(self):
        r = client.get("/doctors")
        assert r.status_code == 200
        assert "doctors" in r.json()

    def test_vapid_key(self):
        r = client.get("/push/vapid-public-key")
        assert r.status_code == 200
        assert "publicKey" in r.json()

    def test_admin_overview(self):
        r = client.get("/api/admin/overview")
        assert r.status_code == 200
        data = r.json()
        assert "patients" in data

    def test_admin_analytics(self):
        r = client.get("/api/admin/analytics")
        assert r.status_code == 200
        data = r.json()
        assert "appointments_per_day" in data
        assert "by_department" in data

    def test_admin_audit_log(self):
        r = client.get("/api/admin/audit-log")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_announcements_list(self):
        r = client.get("/api/admin/announcements")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestPatientWorkflow:
    def test_appointments(self):
        pid = _first_patient_id()
        r = client.get(f"/patient/appointments?patient_id={pid}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_records(self):
        pid = _first_patient_id()
        r = client.get(f"/patient/records?patient_id={pid}")
        assert r.status_code == 200
        data = r.json()
        assert "records" in data
        assert isinstance(data["records"], list)

    def test_reports(self):
        pid = _first_patient_id()
        r = client.get(f"/patient/reports?patient_id={pid}")
        assert r.status_code == 200
        assert "reports" in r.json()

    def test_announcements(self):
        pid = _first_patient_id()
        r = client.get(f"/patient/announcements?patient_id={pid}")
        assert r.status_code == 200
        assert "announcements" in r.json()

    def test_meet_links(self):
        pid = _first_patient_id()
        r = client.get(f"/patient/meet-links?patient_id={pid}")
        assert r.status_code == 200

    def test_conversations(self):
        pid = _first_patient_id()
        r = client.get(f"/patient/conversations?patient_id={pid}")
        assert r.status_code == 200

    def test_active_alerts(self):
        pid = _first_patient_id()
        r = client.get(f"/patient/active-alerts?patient_id={pid}")
        assert r.status_code == 200

    def test_update_profile(self):
        pid = _first_patient_id()
        r = client.post(
            "/update-profile",
            json={
                "patient_id": pid,
                "name": "Test Patient",
                "age": 30,
                "gender": "Male",
                "language": "en",
            },
        )
        assert r.status_code == 200
        assert r.json().get("success") is True

    def test_push_subscribe(self):
        pid = _first_patient_id()
        r = client.post(
            "/patient/push-subscribe",
            json={
                "patient_id": pid,
                "subscription": {
                    "endpoint": "https://example.com/push/test",
                    "keys": {"p256dh": "x", "auth": "y"},
                },
            },
        )
        assert r.status_code == 200
        assert r.json().get("success") is True


class TestDoctorWorkflow:
    def test_dashboard(self):
        did = _first_doctor_id()
        r = client.get(f"/doctor/dashboard?doctor_id={did}")
        assert r.status_code == 200

    def test_appointments(self):
        did = _first_doctor_id()
        r = client.get(f"/doctor/appointments?doctor_id={did}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_patients(self):
        did = _first_doctor_id()
        r = client.get(f"/doctor/patients?doctor_id={did}")
        assert r.status_code == 200

    def test_ratings(self):
        did = _first_doctor_id()
        r = client.get(f"/doctor/ratings?doctor_id={did}")
        assert r.status_code == 200

    def test_conversations(self):
        did = _first_doctor_id()
        r = client.get(f"/doctor/conversations?doctor_id={did}")
        assert r.status_code == 200


class TestVoiceAndSession:
    def test_process_text(self):
        pid = _first_patient_id()
        r = client.post(
            "/process-text",
            json={"text": "hello", "lang": "en", "patient_id": pid},
        )
        assert r.status_code == 200
        assert "text" in r.json()

    def test_translate_text(self):
        r = client.post(
            "/translate-text",
            json={"text": "hello", "target_lang": "hi"},
        )
        assert r.status_code == 200
        assert r.json().get("success") is True

    def test_set_region(self):
        pid = _first_patient_id()
        r = client.post(
            "/set-region",
            json={
                "patient_id": str(pid),
                "region": "Bibewadi",
                "lang": "en",
            },
        )
        assert r.status_code == 200
        assert r.json().get("success") is True


class TestBulkImport:
    def test_bulk_import_csv(self):
        csv_content = (
            "name,department,qualification,experience_years,available_days,"
            "available_hours,doc_id,password,region\n"
            "Dr. Test Import,General,MBBS,3,Mon-Fri,9:00 AM - 5:00 PM,"
            f"DOC_{uuid.uuid4().hex[:10]},pass123,Bibewadi\n"
        )
        r = client.post(
            "/api/admin/doctors/bulk-import",
            files={"file": ("doctors.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        assert data.get("created", 0) >= 0
