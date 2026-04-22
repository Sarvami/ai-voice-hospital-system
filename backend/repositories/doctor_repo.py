def get_doctor_by_doc_id(conn, doc_id: str):
    row = conn.execute("SELECT * FROM doctors WHERE doc_id=?", (doc_id,)).fetchone()
    return dict(row) if row else None


def get_doctor_by_id(conn, doctor_id: int):
    row = conn.execute(
        "SELECT name, department, rating, qualification, available_days, contact_phone, email, region FROM doctors WHERE doctor_id=?",
        (doctor_id,)
    ).fetchone()
    return dict(row) if row else None


def get_doctor_by_name_like(conn, name_fragment: str):
    row = conn.execute(
        "SELECT doctor_id, available_hours, available_days FROM doctors WHERE LOWER(name) LIKE ?",
        (f"%{name_fragment.lower()}%",)
    ).fetchone()
    return dict(row) if row else None


def get_doctor_department_by_name(conn, name_fragment: str):
    row = conn.execute(
        "SELECT name, department FROM doctors WHERE LOWER(name) LIKE ?",
        (f"%{name_fragment.lower()}%",)
    ).fetchone()
    return dict(row) if row else None


def get_doctors_by_department(conn, dept: str, region: str = None):
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
    return [{"doctor_id": r[0], "name": r[1], "rating": r[2], "region": r[3], "available_hours": r[4]} for r in rows]


def get_doctors_by_region(conn, region: str):
    rows = conn.execute("SELECT * FROM doctors WHERE region=?", (region,)).fetchall()
    return [dict(r) for r in rows]


def get_all_doctors(conn):
    rows = conn.execute("SELECT * FROM doctors ORDER BY doctor_id DESC").fetchall()
    return [dict(r) for r in rows]


def doc_id_exists(conn, doc_id: str) -> bool:
    return conn.execute("SELECT 1 FROM doctors WHERE doc_id=?", (doc_id,)).fetchone() is not None


def create_doctor(conn, name, department, qualification, experience_years, available_days,
                  available_hours, doc_id, password_hash, email, phone, region):
    conn.execute(
        """INSERT INTO doctors (name, department, qualification, experience_years, available_days,
           available_hours, doc_id, password_hash, email, contact_phone, region)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (name, department, qualification, experience_years, available_days,
         available_hours, doc_id, password_hash, email, phone, region)
    )
    conn.commit()


def update_doctor(conn, doctor_id, name, department, qualification, experience_years,
                  doc_id, region, available_days, available_hours, contact_phone, email):
    conn.execute(
        """UPDATE doctors SET name=?, department=?, qualification=?, experience_years=?,
           doc_id=?, region=?, available_days=?, available_hours=?, contact_phone=?, email=?
           WHERE doctor_id=?""",
        (name, department, qualification, experience_years, doc_id, region,
         available_days, available_hours, contact_phone, email, doctor_id)
    )
    conn.commit()


def update_doctor_rating(conn, doctor_id: int, new_rating: float, new_count: int):
    conn.execute(
        "UPDATE doctors SET rating=?, rating_count=? WHERE doctor_id=?",
        (new_rating, new_count, doctor_id)
    )
    conn.commit()


def get_doctor_rating_stats(conn, doctor_id: int):
    row = conn.execute("SELECT rating, rating_count FROM doctors WHERE doctor_id=?", (doctor_id,)).fetchone()
    return dict(row) if row else {"rating": 4.5, "rating_count": 0}


def get_doctor_appointments_today(conn, doctor_id: int, today_str: str):
    return conn.execute(
        "SELECT COUNT(*) FROM appointments WHERE doctor_id=? AND appointment_date=?",
        (doctor_id, today_str)
    ).fetchone()[0]


def get_doctor_total_patients(conn, doctor_id: int):
    return conn.execute(
        "SELECT COUNT(DISTINCT patient_id) FROM appointments WHERE doctor_id=?",
        (doctor_id,)
    ).fetchone()[0]
