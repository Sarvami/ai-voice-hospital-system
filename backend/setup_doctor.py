import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DB_PATH = "../database/hospital.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

doctors = conn.execute("SELECT doctor_id, name FROM doctors").fetchall()

for doc in doctors:
    # phone: DOC + doctor_id e.g. DOC1, DOC2
    phone = f"DOC{doc['doctor_id']}"
    # default password: doctor123
    password_hash = pwd_context.hash("doctor123")
    conn.execute("""
        UPDATE doctors SET phone=?, password_hash=? WHERE doctor_id=?
    """, (phone, password_hash, doc['doctor_id']))
    print(f"{doc['name']} → ID: {phone} | Password: doctor123")

conn.commit()
conn.close()
print("\nDone! All doctors set up.")