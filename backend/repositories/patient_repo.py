from database import get_db_connection


def get_patient_by_phone(phone: str):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM patients WHERE phone=?", (phone,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_patient_by_id(patient_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM patients WHERE patient_id=?", (patient_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_patient(name: str, age: int, gender: str, phone: str, language: str, region: str, password_hash: str):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO patients (name, age, gender, phone, preferred_language, region, password_hash) VALUES (?,?,?,?,?,?,?)",
        (name, age, gender, phone, language, region, password_hash)
    )
    conn.commit()
    conn.close()


def get_or_create_patient_voice(name: str, phone: str, language: str = "en"):
    """Used by the voice booking flow — creates a minimal patient if not found."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM patients WHERE phone=?", (phone,)).fetchone()
    if row:
        conn.close()
        return dict(row)
    conn.execute(
        "INSERT INTO patients (name, age, gender, phone, preferred_language) VALUES (?,?,?,?,?)",
        (name, 30, "Unknown", phone, language)
    )
    pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    new_row = conn.execute("SELECT * FROM patients WHERE patient_id=?", (pid,)).fetchone()
    conn.commit()
    conn.close()
    return dict(new_row)


def patient_phone_exists(phone: str) -> bool:
    conn = get_db_connection()
    exists = conn.execute("SELECT 1 FROM patients WHERE phone=?", (phone,)).fetchone()
    conn.close()
    return exists is not None


def update_patient(patient_id: int, name: str, age: int, gender: str, phone: str, preferred_language: str):
    conn = get_db_connection()
    conn.execute(
        "UPDATE patients SET name=?, age=?, gender=?, phone=?, preferred_language=? WHERE patient_id=?",
        (name, age, gender, phone, preferred_language, patient_id)
    )
    conn.commit()
    conn.close()


def update_patient_region(patient_id, region: str):
    conn = get_db_connection()
    conn.execute("UPDATE patients SET region=? WHERE patient_id=?", (region, patient_id))
    conn.commit()
    conn.close()


def get_all_patients():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM patients ORDER BY patient_id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
