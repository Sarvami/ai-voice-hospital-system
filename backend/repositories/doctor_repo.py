from database import get_db_connection


def get_doctor_by_doc_id(doc_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM doctors WHERE doc_id=?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_doctor_by_id(doctor_id: int):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT name, department, rating, qualification, available_days, contact_phone, email, region FROM doctors WHERE doctor_id=?",
        (doctor_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_doctor_by_name_like(name_fragment: str):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT doctor_id, available_hours, available_days FROM doctors WHERE LOWER(name) LIKE ?",
        (f"%{name_fragment.lower()}%",)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_doctor_department_by_name(name_fragment: str):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT name, department FROM doctors WHERE LOWER(name) LIKE ?",
        (f"%{name_fragment.lower()}%",)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_doctors_by_department(dept: str, region: str = None):
    conn = get_db_connection()
    if region:
        rows = conn.execute(
            "SELECT doctor_id, name, rating, region, available_hours FROM doctors WHERE LOWER(department)=LOWER(?) AND LOWER(region)=LOWER(?)",
            (dept, region)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT doctor_id, name, rating, region, available_hours FROM doctors WHERE LOWER(department)=LOWER(?)",
            (dept,)
        ).fetchall()
    conn.close()
    return [{"doctor_id": r[0], "name": r[1], "rating": r[2], "region": r[3], "available_hours": r[4]} for r in rows]


def get_doctors_by_region(region: str):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM doctors WHERE region=?", (region,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_doctors():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM doctors ORDER BY doctor_id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def doc_id_exists(doc_id: str) -> bool:
    conn = get_db_connection()
    exists = conn.execute("SELECT 1 FROM doctors WHERE doc_id=?", (doc_id,)).fetchone()
    conn.close()
    return exists is not None


def create_doctor(name, department, qualification, experience_years, available_days,
                  available_hours, doc_id, password_hash, email, phone, region):
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO doctors (name, department, qualification, experience_years, available_days,
           available_hours, doc_id, password_hash, email, contact_phone, region)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (name, department, qualification, experience_years, available_days,
         available_hours, doc_id, password_hash, email, phone, region)
    )
    conn.commit()
    conn.close()


def update_doctor(doctor_id, name, department, qualification, experience_years,
                  doc_id, region, available_days, available_hours, contact_phone, email):
    conn = get_db_connection()
    conn.execute(
        """UPDATE doctors SET name=?, department=?, qualification=?, experience_years=?,
           doc_id=?, region=?, available_days=?, available_hours=?, contact_phone=?, email=?
           WHERE doctor_id=?""",
        (name, department, qualification, experience_years, doc_id, region,
         available_days, available_hours, contact_phone, email, doctor_id)
    )
    conn.commit()
    conn.close()


def update_doctor_rating(doctor_id: int, new_rating: float, new_count: int):
    conn = get_db_connection()
    conn.execute(
        "UPDATE doctors SET rating=?, rating_count=? WHERE doctor_id=?",
        (new_rating, new_count, doctor_id)
    )
    conn.commit()
    conn.close()


def get_doctor_rating_stats(doctor_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT rating, rating_count FROM doctors WHERE doctor_id=?", (doctor_id,)).fetchone()
    conn.close()
    return dict(row) if row else {"rating": 4.5, "rating_count": 0}


def get_doctor_appointments_today(doctor_id: int, today_str: str):
    conn = get_db_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM appointments WHERE doctor_id=? AND appointment_date=?",
        (doctor_id, today_str)
    ).fetchone()[0]
    conn.close()
    return count


def get_doctor_total_patients(doctor_id: int):
    conn = get_db_connection()
    count = conn.execute(
        "SELECT COUNT(DISTINCT patient_id) FROM appointments WHERE doctor_id=?",
        (doctor_id,)
    ).fetchone()[0]
    conn.close()
    return count
