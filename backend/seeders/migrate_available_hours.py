import sqlite3
 
DB_PATH = "../database/hospital.db"
 
def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
 
    existing_cols = [row[1] for row in cursor.execute("PRAGMA table_info(doctors)").fetchall()]
    if "available_hours" not in existing_cols:
        cursor.execute("ALTER TABLE doctors ADD COLUMN available_hours TEXT DEFAULT '8:00 AM - 8:00 PM'")
        print("✅ Column 'available_hours' added.")
    else:
        print("ℹ️  Column 'available_hours' already exists — skipping.")
 
    cursor.execute("""
        UPDATE doctors
        SET available_hours = '8:00 AM - 8:00 PM'
        WHERE available_hours IS NULL OR available_hours = ''
    """)
    print(f"✅ Default hours applied to {cursor.rowcount} rows.")
 
    # Special timings for a handful of doctors
    special_timings = [
        ("DOC20", "6:00 PM - 8:00 PM"),
        ("DOC25", "8:00 AM - 1:00 PM"),
        ("DOC30", "2:00 PM - 8:00 PM"),
        ("DOC35", "6:00 PM - 8:00 PM"),
        ("DOC40", "9:00 AM - 3:00 PM"),
    ]
 
    for doc_id, hours in special_timings:
        cursor.execute("UPDATE doctors SET available_hours = ? WHERE doc_id = ?", (hours, doc_id))
        if cursor.rowcount:
            print(f"  🕐 {doc_id} → {hours}")
        else:
            print(f"  ⚠️  {doc_id} not found (skipped)")
 
    conn.commit()
    conn.close()
    print("\n✅ Migration complete.")
 
if __name__ == "__main__":
    migrate()