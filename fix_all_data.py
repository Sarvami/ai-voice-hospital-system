import os
import subprocess
import sys

# Move to backend directory
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

print("--- AI Voice Hospital System: One-Click Fix ---")

# 1. Run database initialization
print("\n[1/3] Initializing Database Schema...")
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
