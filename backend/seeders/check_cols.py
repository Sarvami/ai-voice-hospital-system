import sqlite3
conn = sqlite3.connect('../database/hospital.db')
cols = conn.execute('PRAGMA table_info(doctors)').fetchall()
for col in cols:
    print(col[1])
conn.close()