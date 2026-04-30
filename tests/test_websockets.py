import pytest
import sqlite3
import os
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import DB_PATH, get_db_connection

client = TestClient(app)

def test_websocket_auth():
    # Attempt to connect without token
    with pytest.raises(Exception) as excinfo:
        with client.websocket_connect("/ws/patient/1"):
            pass
    assert "403" in str(excinfo.value) or "1008" in str(excinfo.value)

    # Generate token
    response = client.get("/generate-ws-token?user_type=patient&user_id=1")
    assert response.status_code == 200
    token = response.json()["token"]

    # Connect with valid token
    with client.websocket_connect(f"/ws/patient/1?token={token}") as websocket:
        # Should connect successfully
        pass

def test_send_message_broadcast():
    # Generate tokens for doctor and patient
    doc_res = client.get("/generate-ws-token?user_type=doctor&user_id=1")
    pat_res = client.get("/generate-ws-token?user_type=patient&user_id=1")
    doc_token = doc_res.json()["token"]
    pat_token = pat_res.json()["token"]

    with client.websocket_connect(f"/ws/patient/1?token={pat_token}") as pat_ws:
        # Doctor sends a message to patient 1
        payload = {
            "doctor_id": 1,
            "patient_id": 1,
            "appointment_id": None,
            "message": "Hello from tests"
        }
        res = client.post("/doctor/send-message", json=payload)
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Patient WebSocket should receive "new_message"
        data = pat_ws.receive_json()
        assert data["type"] == "new_message"
        assert "message_id" in data

def test_trigger_sos_broadcast():
    pat_res = client.get("/generate-ws-token?user_type=patient&user_id=2")
    pat_token = pat_res.json()["token"]

    with client.websocket_connect(f"/ws/patient/2?token={pat_token}") as pat_ws:
        # Doctor triggers SOS for patient 2
        payload = {
            "doctor_id": 1,
            "patient_id": 2
        }
        res = client.post("/doctor/trigger-sos", json=payload)
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Patient WebSocket should receive "new_alert"
        data = pat_ws.receive_json()
        assert data["type"] == "new_alert"
