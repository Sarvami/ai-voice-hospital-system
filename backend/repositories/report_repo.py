from database import get_db_connection


def create_report(patient_id, report_type: str, filename: str, filepath: str):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO patient_reports (patient_id, report_type, filename, filepath, uploaded_at) VALUES (?,?,?,?,datetime('now'))",
        (patient_id, report_type, filename, filepath)
    )
    conn.commit()
    conn.close()


def get_reports_by_patient(patient_id: int):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM patient_reports WHERE patient_id=? ORDER BY uploaded_at DESC",
        (patient_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report_by_id(report_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM patient_reports WHERE id=?", (report_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_report(report_id: int):
    conn = get_db_connection()
    conn.execute("DELETE FROM patient_reports WHERE id=?", (report_id,))
    conn.commit()
    conn.close()
