import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "hospital.db")

def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add rating columns to doctors
    try:
        cursor.execute("ALTER TABLE doctors ADD COLUMN rating REAL DEFAULT 4.5;")
        cursor.execute("ALTER TABLE doctors ADD COLUMN rating_count INTEGER DEFAULT 10;")
        print("Added rating columns to doctors.")
    except sqlite3.OperationalError:
        print("Rating columns already exist in doctors table.")

    # Add rating column to appointments
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN rating INTEGER;")
        print("Added rating column to appointments.")
    except sqlite3.OperationalError:
        print("Rating column already exists in appointments table.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_migration()
