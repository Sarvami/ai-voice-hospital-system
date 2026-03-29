import sqlite3
conn = sqlite3.connect('data/hospital.db')
conn.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_id INTEGER,
        rating INTEGER,
        review TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()
print('Done!')