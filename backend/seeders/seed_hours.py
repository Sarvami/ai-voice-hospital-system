import sqlite3
import random

hours_options = [
    "8:00 AM - 12:00 PM",
    "10:00 AM - 2:00 PM",
    "12:00 PM - 4:00 PM",
    "2:00 PM - 6:00 PM",
    "4:00 PM - 8:00 PM",
    "6:00 AM - 10:00 AM",
    "9:00 AM - 1:00 PM",
    "8:00 AM - 8:00 PM",
]

conn = sqlite3.connect('../database/hospital.db')
doctors = conn.execute("SELECT doctor_id, name FROM doctors").fetchall()

for doc in doctors:
    hours = random.choice(hours_options)
    conn.execute("UPDATE doctors SET available_hours=? WHERE doctor_id=?", (hours, doc[0]))
    print(f"{doc[1]} → {hours}")

conn.commit()
conn.close()
print("Done!")