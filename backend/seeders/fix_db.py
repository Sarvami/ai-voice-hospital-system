import sqlite3
conn = sqlite3.connect('../database/hospital.db')
conn.execute("ALTER TABLE doctors ADD COLUMN available_hours TEXT DEFAULT '8:00 AM - 8:00 PM'")
conn.commit()
conn.close()
print('Done')