import sqlite3

conn = sqlite3.connect("practice.db")
rows = conn.execute(
    "SELECT at, prid, step, detail FROM events WHERE status = 'fail' ORDER BY id DESC LIMIT 8"
).fetchall()
conn.close()

if not rows:
    print("Koi fail event nahi mila.")
for at, prid, step, detail in rows:
    print(f"{at} | {prid} | {step} | {detail}")
