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
        "PCMC", "Sangamvadi", "Wanowrie", "Hadapsar"
    ]

    cursor.execute("SELECT doctor_id, department FROM doctors ORDER BY department, doctor_id")
    doctors = cursor.fetchall()

    if not doctors:
        print("No doctors found to update.")
    else:
        dept_counts = {}
        for (doc_id, dept) in doctors:
            idx = dept_counts.get(dept, 0)
            assigned_region = regions[idx % len(regions)]
            cursor.execute("UPDATE doctors SET region = ? WHERE doctor_id = ?", (assigned_region, doc_id))
            dept_counts[dept] = idx + 1
        
        print(f"Deterministically assigned regions to {len(doctors)} doctors across all departments.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_migration()
