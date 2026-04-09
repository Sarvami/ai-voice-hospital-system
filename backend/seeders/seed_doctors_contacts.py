import sqlite3
import random

conn = sqlite3.connect("../database/hospital.db")
doctors = conn.execute("SELECT doctor_id, name FROM doctors").fetchall()

for doc in doctors:
    doc_id, name = doc
    clean = name.lower().replace("dr.", "").replace("dr ", "").strip()
    parts = clean.split()
    email = ".".join(parts) + "@hospital.com"
    phone = "9" + str(random.randint(100000000, 999999999))
    
    conn.execute(
        "UPDATE doctors SET email=?, contact_phone=? WHERE doctor_id=?",
        (email, phone, doc_id)
    )

conn.commit()
conn.close()
print("Done!")