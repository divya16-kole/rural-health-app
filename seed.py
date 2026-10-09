import sqlite3
from datetime import datetime

conn = sqlite3.connect("ruralcare.db")
now = datetime.now().isoformat(timespec="seconds")

pharmacies = [
    ("Sri Venkateshwara Pharmacy", "Ramesh", "9876543210", "Hassan", 13.0072, 76.1004),
    ("Janatha Medicals", "Suresh", "9876543211", "Hassan", 13.0100, 76.0950),
    ("Life Care Pharmacy", "Anita", "9876543212", "Hassan", 13.0030, 76.1100),
]
for p in pharmacies:
    conn.execute(
        "INSERT INTO pharmacies (name, owner_name, phone, address, latitude, longitude, created_at) "
        "VALUES (?,?,?,?,?,?,?)", (*p, now))

stock = [(1, "Paracetamol 500mg", 1, 50), (1, "Amoxicillin 500mg", 1, 30),
         (2, "Paracetamol 500mg", 1, 20), (2, "ORS Packet", 1, 100),
         (3, "Cetirizine 10mg", 1, 20), (3, "Ibuprofen 400mg", 0, 0)]
for s in stock:
    conn.execute(
        "INSERT INTO medicine_inventory (pharmacy_id, medicine_name, available, quantity, updated_at) "
        "VALUES (?,?,?,?,?)", (*s, now))

conn.commit(); conn.close()
print("Sample data added")