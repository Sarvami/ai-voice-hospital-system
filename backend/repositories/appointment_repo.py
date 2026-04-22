def get_appointments_by_patient(conn, patient_id: int):
    rows = conn.execute("""
        SELECT a.appointment_id, d.name AS doctor, d.email, d.contact_phone, d.region,
               a.appointment_date AS date, a.appointment_time AS time,
               a.status, a.reason, a.rating
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id=?
        ORDER BY a.appointment_date DESC
    """, (patient_id,)).fetchall()
    return [dict(r) for r in rows]


def get_appointments_by_doctor(conn, doctor_id: int):
    rows = conn.execute("""
        SELECT a.appointment_id AS id, p.name AS patient_name,
               a.appointment_date AS date, a.appointment_time AS time,
               a.status, a.reason
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.doctor_id=?
        ORDER BY a.appointment_date DESC
    """, (doctor_id,)).fetchall()
    return [dict(r) for r in rows]


def get_all_appointments(conn, patient_id: int = None):
    sql = """SELECT a.appointment_id AS id, p.name AS patient, d.name AS doctor,
                    d.department, d.region, a.appointment_date AS date,
                    a.appointment_time AS time, a.status, a.reason
             FROM appointments a
             JOIN patients p ON a.patient_id = p.patient_id
             JOIN doctors  d ON a.doctor_id  = d.doctor_id"""
    if patient_id:
        rows = conn.execute(sql + " WHERE a.patient_id=? ORDER BY a.appointment_date DESC", (patient_id,)).fetchall()
    else:
        rows = conn.execute(sql + " ORDER BY a.appointment_date DESC").fetchall()
    return [dict(r) for r in rows]


def get_appointment_by_id(conn, appointment_id: int):
    row = conn.execute("SELECT * FROM appointments WHERE appointment_id=?", (appointment_id,)).fetchone()
    return dict(row) if row else None


def appointment_exists(conn, patient_id: int, doctor_id: int, date: str) -> bool:
    return conn.execute(
        "SELECT appointment_id FROM appointments WHERE patient_id=? AND doctor_id=? AND appointment_date=?",
        (patient_id, doctor_id, date)
    ).fetchone() is not None


def create_appointment(conn, patient_id, doctor_id, date, time_str, status, reason, source, language):
    conn.execute("""
        INSERT INTO appointments
        (patient_id, doctor_id, appointment_date, appointment_time,
         status, reason, booking_source, language_used)
        VALUES (?,?,?,?,?,?,?,?)
    """, (patient_id, doctor_id, date, time_str, status, reason, source, language))
    aid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    return aid


def set_appointment_rating(conn, appointment_id: int, rating: int):
    conn.execute("UPDATE appointments SET rating=? WHERE appointment_id=?", (rating, appointment_id))
    conn.commit()


def set_appointment_review(conn, appointment_id: int, review: str):
    conn.execute("UPDATE appointments SET review=? WHERE appointment_id=?", (review, appointment_id))
    conn.commit()


def get_ratings_by_doctor(conn, doctor_id: int):
    rows = conn.execute("""
        SELECT p.name AS patient_name, a.rating, a.review, a.appointment_date AS date
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.doctor_id=? AND a.rating IS NOT NULL
        ORDER BY a.appointment_date DESC
    """, (doctor_id,)).fetchall()
    return [dict(r) for r in rows]


def get_all_ratings(conn):
    rows = conn.execute("""
        SELECT p.name AS patient, d.name AS doctor, d.department,
               a.rating, a.review, a.appointment_date AS date
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors  d ON a.doctor_id  = d.doctor_id
        WHERE a.rating IS NOT NULL
        ORDER BY a.rating ASC, a.appointment_date DESC
    """).fetchall()
    return [dict(r) for r in rows]


def get_patients_by_doctor(conn, doctor_id: int):
    rows = conn.execute("""
        SELECT DISTINCT p.patient_id, p.name, p.age, p.gender, p.phone
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.doctor_id=?
    """, (doctor_id,)).fetchall()
    return [dict(r) for r in rows]


def get_overview_counts(conn):
    p = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    d = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    a = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    return {"patients": p, "doctors": d, "appointments": a}
