import sqlite3
import random

conn = sqlite3.connect('../database/hospital.db')
doctors = conn.execute('SELECT doctor_id, name FROM doctors').fetchall()

for doc in doctors:
    did, name = doc[0], doc[1]
    clean = name.lower().replace("dr.", "").replace("dr ", "").strip()
    parts = clean.split()
    email = ".".join(parts) + "@hospital.com"
    phone = "9" + str(random.randint(100000000, 999999999))
    conn.execute(
        "UPDATE doctors SET email=?, contact_phone=? WHERE doctor_id=?",
        (email, phone, did)
    )

conn.commit()
conn.close()
print("Done")