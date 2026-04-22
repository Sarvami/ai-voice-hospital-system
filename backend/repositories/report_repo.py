def create_report(conn, patient_id, report_type: str, filename: str, filepath: str):
    conn.execute(
        "INSERT INTO patient_reports (patient_id, report_type, filename, filepath, uploaded_at) VALUES (?,?,?,?,datetime('now'))",
        (patient_id, report_type, filename, filepath)
    )
    conn.commit()


def get_reports_by_patient(conn, patient_id: int):
    rows = conn.execute(
        "SELECT * FROM patient_reports WHERE patient_id=? ORDER BY uploaded_at DESC",
        (patient_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_report_by_id(conn, report_id: int):
    row = conn.execute("SELECT * FROM patient_reports WHERE id=?", (report_id,)).fetchone()
    return dict(row) if row else None


def delete_report(conn, report_id: int):
    conn.execute("DELETE FROM patient_reports WHERE id=?", (report_id,))
    conn.commit()
