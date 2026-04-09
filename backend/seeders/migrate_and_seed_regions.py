import sqlite3
import random

DB_PATH = "../data/hospital.db"

def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add region column if not exists
    try:
        cursor.execute("ALTER TABLE doctors ADD COLUMN region TEXT;")
        print("Added region column.")
    except sqlite3.OperationalError:
        print("Region column already exists.")

    regions = [
        "Bibewadi", "Kalyani Nagar", "Ravet", 
        "PCMC", "Sangamwadi", "Wanowrie", "Hadapsar"
    ]

    cursor.execute("SELECT doctor_id FROM doctors")
    doctors = cursor.fetchall()

    if not doctors:
        print("No doctors found to update.")
    else:
        for (doc_id,) in doctors:
            assigned_region = random.choice(regions)
            cursor.execute("UPDATE doctors SET region = ? WHERE doctor_id = ?", (assigned_region, doc_id))
        
        print(f"Randomly assigned regions to {len(doctors)} doctors.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_migration()
