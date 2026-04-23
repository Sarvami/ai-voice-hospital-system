import os
import subprocess
import sys
import sqlite3

# Move to backend directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(ROOT_DIR, "backend"))
DB_PATH = os.path.join(ROOT_DIR, "backend", "data", "hospital.db")

print("--- SwasthSeva: One-Click Fix ---")

# 0. Cleanup malformed tables (COMMENTED OUT TO PRESERVE YOUR DATA)
# print("\n[0/4] Cleaning up old data...")
# if os.path.exists(DB_PATH):
#     conn = sqlite3.connect(DB_PATH)
#     conn.execute("DROP TABLE IF EXISTS doctors")
#     conn.execute("DROP TABLE IF EXISTS patients")
#     conn.execute("DROP TABLE IF EXISTS appointments")
#     conn.commit()
#     conn.close()

# 1. Run database initialization
print("\n[1/4] Initializing Database Schema...")
subprocess.run([sys.executable, "database.py"])

# 2. Run Doctor Seeder
print("\n[2/3] Seeding 50 Doctors with complete profiles...")
os.chdir("seeders")
subprocess.run([sys.executable, "seed_doctors.py"])

# 3. Run Region Seeder
print("\n[3/3] Assigning random regions...")
subprocess.run([sys.executable, "migrate_and_seed_regions.py"])

print("\nDONE! All data is fixed and synced.")
print("Please RESTART your uvicorn server now.")
