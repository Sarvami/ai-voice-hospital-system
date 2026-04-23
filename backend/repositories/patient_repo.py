def get_patient_by_phone(conn, phone: str):
    row = conn.execute("SELECT * FROM patients WHERE phone=?", (phone,)).fetchone()
    return dict(row) if row else None


def get_patient_by_id(conn, patient_id: int):
    row = conn.execute("SELECT * FROM patients WHERE patient_id=?", (patient_id,)).fetchone()
    return dict(row) if row else None


def create_patient(conn, name, age, gender, phone, language, region, password_hash):
    conn.execute(
        "INSERT INTO patients (name, age, gender, phone, preferred_language, region, password_hash) VALUES (?,?,?,?,?,?,?)",
        (name, age, gender, phone, language, region, password_hash)
    )
    conn.commit()


def get_or_create_patient_voice(conn, name: str, phone: str, language: str = "en"):
    row = conn.execute("SELECT * FROM patients WHERE phone=?", (phone,)).fetchone()
    if row:
        return dict(row)
    conn.execute(
        "INSERT INTO patients (name, age, gender, phone, preferred_language) VALUES (?,?,?,?,?)",
        (name, 30, "Unknown", phone, language)
    )
    conn.commit()
    pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    new_row = conn.execute("SELECT * FROM patients WHERE patient_id=?", (pid,)).fetchone()
    return dict(new_row)


def patient_phone_exists(conn, phone: str) -> bool:
    return conn.execute("SELECT 1 FROM patients WHERE phone=?", (phone,)).fetchone() is not None


def update_patient(conn, patient_id, name, age, gender, phone, preferred_language):
    conn.execute(
        "UPDATE patients SET name=?, age=?, gender=?, phone=?, preferred_language=? WHERE patient_id=?",
        (name, age, gender, phone, preferred_language, patient_id)
    )
    conn.commit()


def update_patient_region(conn, patient_id, region: str):
    conn.execute("UPDATE patients SET region=? WHERE patient_id=?", (region, patient_id))
    conn.commit()


def get_all_patients(conn):
    rows = conn.execute("SELECT * FROM patients ORDER BY patient_id DESC").fetchall()
    return [dict(r) for r in rows]
