import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DB_PATH = "../database/hospital.db"

conn = sqlite3.connect(DB_PATH)
doctors = conn.execute("SELECT doctor_id, name FROM doctors ORDER BY doctor_id").fetchall()

for i, doc in enumerate(doctors):
    doc_id = f"DOC{i+1}"
    password_hash = pwd_context.hash("doctor123")
    conn.execute(
        "UPDATE doctors SET doc_id=?, password_hash=? WHERE doctor_id=?",
        (doc_id, password_hash, doc[0])
    )
    print(f"{doc[1]} → ID: {doc_id}")

conn.commit()
conn.close()
print("Done!")