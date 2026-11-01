# Status: updater chal raha hai? DB mein nayi khabrein aa rahi hain? PIB pe kya naya hai?

import sqlite3
from datetime import datetime

from collector import fetch_feed, get_prid

conn = sqlite3.connect("practice.db")

print("== Aakhri 5 update koshishein ==")
rows = conn.execute("SELECT at, status, detail FROM events WHERE step = 'fetch' "
                    "ORDER BY id DESC LIMIT 5").fetchall()
for at, status, detail in rows:
    print(f"  {at}  {status:<4}  {detail}")
if rows:
    mins = (datetime.now() - datetime.fromisoformat(rows[0][0])).total_seconds() / 60
    print(f"  -> Aakhri koshish {mins:.0f} minute pehle")
    if mins > 15:
        print("  !! 15 minute se zyada: koi updater nahi chal raha")

print("\n== DB ==")
newest = conn.execute("SELECT prid, title, fetched_at FROM releases "
                      "ORDER BY CAST(prid AS INTEGER) DESC LIMIT 1").fetchone()
print("  Sabse nayi release:", newest[0], "|", newest[2], "|", newest[1][:60])
saved = {r[0] for r in conn.execute("SELECT prid FROM releases")}
conn.close()

print("\n== PIB pe abhi ==")
entries = fetch_feed()
live = [get_prid(e.get("link")) for e in entries]
missing = [p for p in live if p and p not in saved]
print(f"  Feed mein {len(live)} releases, inme se {len(missing)} DB mein NAHI hain")
if missing:
    print("  !! Nayi khabrein PIB pe hain lekin humne uthayi nahi:", ", ".join(missing[:5]))
else:
    print("  OK: PIB ki saari releases DB mein hain")
