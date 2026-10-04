import sqlite3

conn = sqlite3.connect("ruralcare.db")

print("Pharmacies:", conn.execute("SELECT COUNT(*) FROM pharmacies").fetchone()[0])
print("Medicines:", conn.execute("SELECT COUNT(*) FROM medicine_inventory").fetchone()[0])

for row in conn.execute("SELECT id, name FROM pharmacies"):
    print(row)