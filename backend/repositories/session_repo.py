import json
from database import get_db_connection


def get_session(patient_id: str) -> tuple:
    """Returns (state, data) for a patient. Defaults to ('idle', {})."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT state, data FROM conversation_sessions WHERE patient_id=?",
        (patient_id,)
    ).fetchone()
    conn.close()
    if row:
        return row["state"], json.loads(row["data"])
    return "idle", {}


def set_session(patient_id: str, state: str, data: dict):
    """Upsert the session state for a patient."""
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO conversation_sessions (patient_id, state, data, updated_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(patient_id) DO UPDATE SET
            state      = excluded.state,
            data       = excluded.data,
            updated_at = excluded.updated_at
    """, (patient_id, state, json.dumps(data)))
    conn.commit()
    conn.close()


def delete_session(patient_id: str):
    """Remove session after booking completes or is cancelled."""
    conn = get_db_connection()
    conn.execute("DELETE FROM conversation_sessions WHERE patient_id=?", (patient_id,))
    conn.commit()
    conn.close()
