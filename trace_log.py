# Lesson 12: Har step ka log (agent trace) + demo settings (PIB down toggle)

import sqlite3
from datetime import datetime

DB_FILE = "practice.db"


def _conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        at TEXT, prid TEXT, step TEXT, status TEXT, detail TEXT)""")
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    return conn


def log_event(prid, step, status, detail=""):
    """step: fetch / summary / verify / match / send   status: ok / fail"""
    try:
        conn = _conn()
        conn.execute("INSERT INTO events (at, prid, step, status, detail) VALUES (?, ?, ?, ?, ?)",
                     (datetime.now().isoformat(timespec="seconds"), prid, step, status, str(detail)[:300]))
        conn.commit()
        conn.close()
    except Exception as err:
        print("  log nahi hua:", err)          # logging fail ho to asli kaam na ruke


def simulate_pib_down():
    conn = _conn()
    row = conn.execute("SELECT value FROM settings WHERE key = 'pib_down'").fetchone()
    conn.close()
    return bool(row and row[0] == "1")


def set_pib_down(flag):
    conn = _conn()
    conn.execute("INSERT OR REPLACE INTO settings VALUES ('pib_down', ?)", ("1" if flag else "0",))
    conn.commit()
    conn.close()
