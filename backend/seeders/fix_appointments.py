import sqlite3

conn = sqlite3.connect('../database/hospital.db')

conn.execute("DELETE FROM appointments WHERE appointment_id = 3")
conn.execute("UPDATE appointments SET appointment_date='10 January 2026' WHERE appointment_id=1")
conn.execute("UPDATE appointments SET appointment_date='11 January 2026' WHERE appointment_id=2")
conn.execute("UPDATE appointments SET appointment_date='16 April 2026' WHERE appointment_id=5")

conn.commit()
print('Done! Verifying...')

rows = conn.execute("SELECT appointment_id, appointment_date FROM appointments").fetchall()
for r in rows:
    print(r)

conn.close()