def ensure_cancellation_columns(conn):
    cols = conn.execute("PRAGMA table_info(appointments)").fetchall()
    col_names = {c[1] for c in cols}
    changed = False
    if "cancellation_reason" not in col_names:
        conn.execute("ALTER TABLE appointments ADD COLUMN cancellation_reason TEXT")
        changed = True
    if "cancelled_by" not in col_names:
        conn.execute("ALTER TABLE appointments ADD COLUMN cancelled_by TEXT")
        changed = True
    if "review" not in col_names:
        conn.execute("ALTER TABLE appointments ADD COLUMN review TEXT")
        changed = True
    if changed:
        conn.commit()


def get_appointments_by_patient(conn, patient_id: int):
    ensure_cancellation_columns(conn)
    rows = conn.execute("""
        SELECT a.appointment_id, a.doctor_id, d.name AS doctor, d.email, d.contact_phone, d.region,
               a.appointment_date AS date, a.appointment_time AS time,
               a.status, a.reason, a.rating, a.cancellation_reason, a.cancelled_by
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id=?
        ORDER BY a.appointment_date DESC
    """, (patient_id,)).fetchall()
    return [dict(r) for r in rows]


def get_appointments_by_doctor(conn, doctor_id: int):
    ensure_cancellation_columns(conn)
    rows = conn.execute("""
        SELECT a.appointment_id AS id, a.patient_id, p.name AS patient_name,
               a.appointment_date AS date, a.appointment_time AS time,
               a.status, a.reason, a.cancellation_reason, a.cancelled_by
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.doctor_id=?
        ORDER BY a.appointment_date DESC
    """, (doctor_id,)).fetchall()
    return [dict(r) for r in rows]


def get_all_appointments(conn, patient_id: int = None):
    ensure_cancellation_columns(conn)
    sql = """SELECT a.appointment_id AS id, a.patient_id, p.name AS patient, d.name AS doctor,
                    d.department, d.region, a.appointment_date AS date,
                    a.appointment_time AS time, a.status, a.reason, a.cancellation_reason, a.cancelled_by
             FROM appointments a
             JOIN patients p ON a.patient_id = p.patient_id
             JOIN doctors  d ON a.doctor_id  = d.doctor_id"""
    if patient_id:
        rows = conn.execute(sql + " WHERE a.patient_id=? ORDER BY a.appointment_date DESC", (patient_id,)).fetchall()
    else:
        rows = conn.execute(sql + " ORDER BY a.appointment_date DESC").fetchall()
    return [dict(r) for r in rows]


def get_appointment_by_id(conn, appointment_id: int):
    ensure_cancellation_columns(conn)
    row = conn.execute("SELECT * FROM appointments WHERE appointment_id=?", (appointment_id,)).fetchone()
    return dict(row) if row else None


def appointment_exists(conn, patient_id: int, doctor_id: int, date: str) -> bool:
    return conn.execute(
        "SELECT appointment_id FROM appointments WHERE patient_id=? AND doctor_id=? AND appointment_date=?",
        (patient_id, doctor_id, date)
    ).fetchone() is not None


def appointment_slot_taken(conn, doctor_id: int, date: str, time_str: str) -> bool:
    """Check if a doctor already has a non-cancelled appointment at this exact date+time."""
    return conn.execute(
        """SELECT appointment_id FROM appointments
           WHERE doctor_id=? AND appointment_date=? AND appointment_time=?
           AND LOWER(status) NOT IN ('cancelled')""",
        (doctor_id, date, time_str)
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
    ensure_cancellation_columns(conn)
    rows = conn.execute("""
        SELECT p.name AS patient_name, a.rating, a.review, a.appointment_date AS date
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.doctor_id=? AND a.rating IS NOT NULL
        ORDER BY a.appointment_date DESC
    """, (doctor_id,)).fetchall()
    return [dict(r) for r in rows]


def get_all_ratings(conn):
    ensure_cancellation_columns(conn)
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


def cancel_appointment_by_doctor(conn, appointment_id: int, doctor_id: int, cancellation_reason: str):
    ensure_cancellation_columns(conn)
    row = conn.execute(
        "SELECT appointment_id, status FROM appointments WHERE appointment_id=? AND doctor_id=?",
        (appointment_id, doctor_id),
    ).fetchone()
    if not row:
        return {"success": False, "message": "Appointment not found for this doctor."}

    current_status = (row["status"] or "").lower()
    if current_status in {"cancelled", "completed"}:
        return {"success": False, "message": f"Cannot cancel an appointment with status '{row['status']}'."}

    conn.execute(
        """
        UPDATE appointments
        SET status='Cancelled',
            cancellation_reason=?,
            cancelled_by='doctor'
        WHERE appointment_id=? AND doctor_id=?
        """,
        (cancellation_reason, appointment_id, doctor_id),
    )
    conn.commit()
    return {"success": True}
