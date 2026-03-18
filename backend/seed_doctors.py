import sqlite3

DB_PATH = "../database/hospital.db"

doctors = [
    # Cardiology (5)
    ("Dr. Arjun Mehta", "Cardiology", "MD Cardiology, DM", 15, "Mon-Fri"),
    ("Dr. Priya Sharma", "Cardiology", "MD Cardiology", 10, "Mon-Sat"),
    ("Dr. Rajan Shah", "Cardiology", "DM Cardiology", 12, "Tue-Sun"),
    ("Dr. Neha Kulkarni", "Cardiology", "MD, FACC", 8, "Mon-Fri"),
    ("Dr. Sunil Bapat", "Cardiology", "DM Cardiology, FRCP", 17, "Mon-Thu"),

    # General (5)
    ("Dr. Suresh Patil", "General", "MBBS, MD", 9, "Mon-Sat"),
    ("Dr. Kavita Verma", "General", "MBBS", 6, "Mon-Fri"),
    ("Dr. Amit Joshi", "General", "MBBS, MD", 11, "Mon-Sun"),
    ("Dr. Sneha Rao", "General", "MBBS", 5, "Tue-Sat"),
    ("Dr. Harish Nair", "General", "MBBS, MD", 8, "Mon-Fri"),

    # ENT (5)
    ("Dr. Vikram Nair", "ENT", "MS ENT", 13, "Mon-Fri"),
    ("Dr. Anita Desai", "ENT", "MS ENT, DNB", 8, "Mon-Sat"),
    ("Dr. Rohit Gupta", "ENT", "MS ENT", 7, "Tue-Sun"),
    ("Dr. Meena Pillai", "ENT", "MS ENT, FRCS", 11, "Mon-Fri"),
    ("Dr. Sanjay Iyer", "ENT", "MS ENT", 6, "Mon-Thu"),

    # Dentist (5)
    ("Dr. Pooja Iyer", "Dentist", "BDS, MDS", 9, "Mon-Sat"),
    ("Dr. Karan Malhotra", "Dentist", "BDS", 5, "Mon-Fri"),
    ("Dr. Swati Bhatt", "Dentist", "MDS Orthodontics", 10, "Tue-Sun"),
    ("Dr. Rajiv Doshi", "Dentist", "BDS, MDS Prostho", 12, "Mon-Fri"),
    ("Dr. Alka Shetty", "Dentist", "MDS Periodontics", 7, "Mon-Sat"),

    # Orthopedics (5)
    ("Dr. Rajesh Kapoor", "Orthopedics", "MS Ortho, DNB", 14, "Mon-Fri"),
    ("Dr. Meera Pillai", "Orthopedics", "MS Ortho", 9, "Mon-Sat"),
    ("Dr. Sameer Tiwari", "Orthopedics", "MS Ortho, FRCS", 16, "Tue-Fri"),
    ("Dr. Asha Kadam", "Orthopedics", "MS Ortho, DNB", 10, "Mon-Thu"),
    ("Dr. Nitin Bhosale", "Orthopedics", "MS Ortho", 7, "Mon-Fri"),

    # Neurology (5)
    ("Dr. Aditya Bose", "Neurology", "DM Neurology", 12, "Mon-Fri"),
    ("Dr. Sunita Chandra", "Neurology", "MD, DM Neurology", 10, "Mon-Sat"),
    ("Dr. Praveen Murthy", "Neurology", "DM Neurology, FRCP", 18, "Tue-Sun"),
    ("Dr. Rekha Joshi", "Neurology", "DM Neurology", 8, "Mon-Fri"),
    ("Dr. Vivek Sathe", "Neurology", "MD, DM Neurology", 11, "Mon-Thu"),

    # Gynecology (5)
    ("Dr. Rekha Menon", "Gynecology", "MS OBG, DNB", 13, "Mon-Sat"),
    ("Dr. Deepa Saxena", "Gynecology", "MD Gynecology", 9, "Mon-Fri"),
    ("Dr. Lata Krishnan", "Gynecology", "MS OBG", 11, "Tue-Sun"),
    ("Dr. Smita Gokhale", "Gynecology", "MS OBG, DNB", 14, "Mon-Fri"),
    ("Dr. Anjali Pawar", "Gynecology", "MD Gynecology", 7, "Mon-Sat"),

    # Dermatology (5)
    ("Dr. Nisha Agarwal", "Dermatology", "MD Dermatology", 8, "Mon-Fri"),
    ("Dr. Vivek Sinha", "Dermatology", "MD, DVD", 6, "Mon-Sat"),
    ("Dr. Ritu Pandey", "Dermatology", "MD Dermatology", 9, "Tue-Sun"),
    ("Dr. Kiran Wagh", "Dermatology", "MD Dermatology, DNB", 12, "Mon-Fri"),
    ("Dr. Priti Kulkarni", "Dermatology", "MD Dermatology", 5, "Mon-Thu"),

    # Pediatrics (5)
    ("Dr. Ashok Hegde", "Pediatrics", "MD Pediatrics, DCH", 14, "Mon-Sat"),
    ("Dr. Usha Reddy", "Pediatrics", "MD Pediatrics", 10, "Mon-Fri"),
    ("Dr. Ganesh Naik", "Pediatrics", "DCH, DNB", 7, "Tue-Sun"),
    ("Dr. Seema Jain", "Pediatrics", "MD Pediatrics, DCH", 9, "Mon-Fri"),
    ("Dr. Rahul Deshpande", "Pediatrics", "DCH, MD Pediatrics", 11, "Mon-Sat"),

    # Ophthalmology (5)
    ("Dr. Shilpa Doshi", "Ophthalmology", "MS Ophthalmology", 11, "Mon-Fri"),
    ("Dr. Manoj Patel", "Ophthalmology", "MS Ophthalmology, FRCS", 15, "Mon-Sat"),
    ("Dr. Archana Jain", "Ophthalmology", "MS Ophthalmology", 8, "Tue-Sun"),
    ("Dr. Dilip Thakur", "Ophthalmology", "MS Ophthalmology, DNB", 13, "Mon-Fri"),
    ("Dr. Varsha Mane", "Ophthalmology", "MS Ophthalmology", 6, "Mon-Thu"),
]

conn = sqlite3.connect(DB_PATH)

# Clear existing duplicate doctors
conn.execute("DELETE FROM doctors")
conn.commit()

# Insert fresh doctors
for doc in doctors:
    conn.execute("""
        INSERT INTO doctors (name, department, qualification, experience_years, available_days, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, doc)

conn.commit()

# Verify
count = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
print(f"Done! {count} doctors added.")

# Show summary by department
rows = conn.execute("""
    SELECT department, COUNT(*) as count 
    FROM doctors 
    GROUP BY department 
    ORDER BY department
""").fetchall()

print("\nDoctors per department:")
for row in rows:
    print(f"  {row[0]}: {row[1]} doctors")

conn.close()