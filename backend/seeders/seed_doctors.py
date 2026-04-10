import sqlite3
import random

DB_PATH = "../data/hospital.db"

doctors = [
    # Cardiology (7)
    ("Dr. Arjun Mehta", "Cardiology", "MD Cardiology, DM", 15, "Mon-Fri"),
    ("Dr. Priya Sharma", "Cardiology", "MD Cardiology", 10, "Mon-Sat"),
    ("Dr. Rajan Shah", "Cardiology", "DM Cardiology", 12, "Tue-Sun"),
    ("Dr. Neha Kulkarni", "Cardiology", "MD, FACC", 8, "Mon-Fri"),
    ("Dr. Sunil Bapat", "Cardiology", "DM Cardiology, FRCP", 17, "Mon-Thu"),
    ("Dr. Sameer Khan", "Cardiology", "MD, DM", 14, "Mon-Sat"),
    ("Dr. Ananya Ray", "Cardiology", "MD Cardiology", 9, "Tue-Fri"),

    # General (7)
    ("Dr. Suresh Patil", "General", "MBBS, MD", 9, "Mon-Sat"),
    ("Dr. Kavita Verma", "General", "MBBS", 6, "Mon-Fri"),
    ("Dr. Amit Joshi", "General", "MBBS, MD", 11, "Mon-Sun"),
    ("Dr. Sneha Rao", "General", "MBBS", 5, "Tue-Sat"),
    ("Dr. Harish Nair", "General", "MBBS, MD", 8, "Mon-Fri"),
    ("Dr. Rajesh Khanna", "General", "MBBS, MD", 12, "Mon-Sat"),
    ("Dr. Suman Gill", "General", "MBBS", 7, "Wed-Sun"),

    # ENT (7)
    ("Dr. Vikram Nair", "ENT", "MS ENT", 13, "Mon-Fri"),
    ("Dr. Anita Desai", "ENT", "MS ENT, DNB", 8, "Mon-Sat"),
    ("Dr. Rohit Gupta", "ENT", "MS ENT", 7, "Tue-Sun"),
    ("Dr. Meena Pillai", "ENT", "MS ENT, FRCS", 11, "Mon-Fri"),
    ("Dr. Sanjay Iyer", "ENT", "MS ENT", 6, "Mon-Thu"),
    ("Dr. Pavan Joshi", "ENT", "MS ENT", 10, "Mon-Sat"),
    ("Dr. Shilpa Rao", "ENT", "MS ENT", 9, "Tue-Fri"),

    # Dentist (7)
    ("Dr. Pooja Iyer", "Dentist", "BDS, MDS", 9, "Mon-Sat"),
    ("Dr. Karan Malhotra", "Dentist", "BDS", 5, "Mon-Fri"),
    ("Dr. Swati Bhatt", "Dentist", "MDS Orthodontics", 10, "Tue-Sun"),
    ("Dr. Rajiv Doshi", "Dentist", "BDS, MDS Prostho", 12, "Mon-Fri"),
    ("Dr. Alka Shetty", "Dentist", "MDS Periodontics", 7, "Mon-Sat"),
    ("Dr. Rahul Varma", "Dentist", "BDS, MDS", 8, "Mon-Fri"),
    ("Dr. Snehal Patil", "Dentist", "MDS", 11, "Tue-Sat"),

    # Orthopedics (7)
    ("Dr. Rajesh Kapoor", "Orthopedics", "MS Ortho, DNB", 14, "Mon-Fri"),
    ("Dr. Meera Pillai", "Orthopedics", "MS Ortho", 9, "Mon-Sat"),
    ("Dr. Sameer Tiwari", "Orthopedics", "MS Ortho, FRCS", 16, "Tue-Fri"),
    ("Dr. Asha Kadam", "Orthopedics", "MS Ortho, DNB", 10, "Mon-Thu"),
    ("Dr. Nitin Bhosale", "Orthopedics", "MS Ortho", 7, "Mon-Fri"),
    ("Dr. Deepak Garg", "Orthopedics", "MS Ortho", 13, "Mon-Sat"),
    ("Dr. Rashmi Desai", "Orthopedics", "MS Ortho", 8, "Tue-Sun"),

    # Neurology (7)
    ("Dr. Aditya Bose", "Neurology", "DM Neurology", 12, "Mon-Fri"),
    ("Dr. Sunita Chandra", "Neurology", "MD, DM Neurology", 10, "Mon-Sat"),
    ("Dr. Praveen Murthy", "Neurology", "DM Neurology, FRCP", 18, "Tue-Sun"),
    ("Dr. Rekha Joshi", "Neurology", "DM Neurology", 8, "Mon-Fri"),
    ("Dr. Vivek Sathe", "Neurology", "MD, DM Neurology", 11, "Mon-Thu"),
    ("Dr. Ishwar Puri", "Neurology", "DM Neurology", 15, "Mon-Sat"),
    ("Dr. Neha Ghalot", "Neurology", "DM Neurology", 9, "Tue-Fri"),

    # Gynecology (7)
    ("Dr. Rekha Menon", "Gynecology", "MS OBG, DNB", 13, "Mon-Sat"),
    ("Dr. Deepa Saxena", "Gynecology", "MD Gynecology", 9, "Mon-Fri"),
    ("Dr. Lata Krishnan", "Gynecology", "MS OBG", 11, "Tue-Sun"),
    ("Dr. Smita Gokhale", "Gynecology", "MS OBG, DNB", 14, "Mon-Fri"),
    ("Dr. Anjali Pawar", "Gynecology", "MD Gynecology", 7, "Mon-Sat"),
    ("Dr. Preeti Singh", "Gynecology", "MS OBG", 12, "Mon-Thu"),
    ("Dr. Maya Hegde", "Gynecology", "MS OBG", 10, "Tue-Fri"),

    # Dermatology (7)
    ("Dr. Nisha Agarwal", "Dermatology", "MD Dermatology", 8, "Mon-Fri"),
    ("Dr. Vivek Sinha", "Dermatology", "MD, DVD", 6, "Mon-Sat"),
    ("Dr. Ritu Pandey", "Dermatology", "MD Dermatology", 9, "Tue-Sun"),
    ("Dr. Kiran Wagh", "Dermatology", "MD Dermatology, DNB", 12, "Mon-Fri"),
    ("Dr. Priti Kulkarni", "Dermatology", "MD Dermatology", 5, "Mon-Thu"),
    ("Dr. Sanjay Dutta", "Dermatology", "MD", 11, "Mon-Sat"),
    ("Dr. Aarti Saxena", "Dermatology", "MD", 10, "Tue-Fri"),

    # Pediatrics (7)
    ("Dr. Ashok Hegde", "Pediatrics", "MD Pediatrics, DCH", 14, "Mon-Sat"),
    ("Dr. Usha Reddy", "Pediatrics", "MD Pediatrics", 10, "Mon-Fri"),
    ("Dr. Ganesh Naik", "Pediatrics", "DCH, DNB", 7, "Tue-Sun"),
    ("Dr. Seema Jain", "Pediatrics", "MD Pediatrics, DCH", 9, "Mon-Fri"),
    ("Dr. Rahul Deshpande", "Pediatrics", "DCH, MD Pediatrics", 11, "Mon-Sat"),
    ("Dr. Vinod Kambli", "Pediatrics", "MD", 12, "Mon-Thu"),
    ("Dr. Kavita Murthy", "Pediatrics", "MD", 8, "Tue-Fri"),

    # Ophthalmology (7)
    ("Dr. Shilpa Doshi", "Ophthalmology", "MS Ophthalmology", 11, "Mon-Fri"),
    ("Dr. Manoj Patel", "Ophthalmology", "MS Ophthalmology, FRCS", 15, "Mon-Sat"),
    ("Dr. Archana Jain", "Ophthalmology", "MS Ophthalmology", 8, "Tue-Sun"),
    ("Dr. Dilip Thakur", "Ophthalmology", "MS Ophthalmology, DNB", 13, "Mon-Fri"),
    ("Dr. Varsha Mane", "Ophthalmology", "MS Ophthalmology", 6, "Mon-Thu"),
    ("Dr. Amit Trivedi", "Ophthalmology", "MS", 10, "Mon-Sat"),
    ("Dr. Pooja Hegde", "Ophthalmology", "MS", 9, "Tue-Fri"),

]

conn = sqlite3.connect(DB_PATH)

# Clear existing duplicate doctors
conn.execute("DELETE FROM doctors")
conn.commit()

# Insert fresh doctors with full details
for i, doc in enumerate(doctors, 1):
    doc_id = f"DOC{i:02d}"
    # Generate simple email/phone
    clean_name = doc[0].lower().replace("dr.", "").strip().replace(" ", ".")
    email = f"{clean_name}@hospital.com"
    phone = f"9823{random.randint(100000, 999999)}"
    
    # Assign specialist hours to ~15% of doctors
    available_hours = "8:00 AM - 8:00 PM"
    if random.random() < 0.15:
        special_slots = [
            "10:00 AM - 1:00 PM",
            "2:00 PM - 5:00 PM",
            "9:00 AM - 12:00 PM",
            "4:00 PM - 7:00 PM",
            "11:00 AM - 3:00 PM"
        ]
        available_hours = random.choice(special_slots)

    conn.execute("""
        INSERT INTO doctors (name, department, qualification, experience_years, available_days, 
                            doc_id, email, contact_phone, password_hash, available_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, '$2b$12$8rOxmDR4.fKircYEbdDSYem.1NC9rORJpXt.MAuLfHxRENu/eWq8C', ?)
    """, (*doc, doc_id, email, phone, available_hours))

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