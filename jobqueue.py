# Summary queue: ek-ek karke, AI limits ke hisaab se. User ko kabhi "busy, try again" nahi.

import sqlite3
import threading
import time
from datetime import datetime, timedelta

import streamlit as st

from alerts import cached_summary, setup_alert_tables
from collector import setup_db as setup_releases

DB_FILE = "practice.db"
GAP_SECONDS = 15          # do summaries ke beech (free AI limits)
MAX_ATTEMPTS = 3          # itni baar fail ho to chhod do


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        prid TEXT, lang TEXT, status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0,
        requested_at TEXT, started_at TEXT, PRIMARY KEY (prid, lang))""")
    return conn


def enqueue(prid, lang):
    """Queue mein daalo. Pehle se hai to kuch mat likho (har 30 sec 21 cards = DB pe bheed)."""
    try:
        conn = _conn()
        if conn.execute("SELECT 1 FROM jobs WHERE prid = ? AND lang = ?", (prid, lang)).fetchone() is None:
            conn.execute("INSERT OR IGNORE INTO jobs (prid, lang, requested_at) VALUES (?, ?, ?)",
                         (prid, lang, _now()))
            conn.commit()
        conn.close()
    except sqlite3.OperationalError as err:          # DB busy: koi baat nahi, agle refresh pe phir daalenge
        print("[queue] enqueue skip:", err)


def job_status(prid, lang):
    try:
        conn = _conn()
        row = conn.execute("SELECT status FROM jobs WHERE prid = ? AND lang = ?", (prid, lang)).fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None


def _claim():
    """Agla kaam uthao. Do worker ek hi kaam na uthayein, isliye 'pending -> running' ek hi baar."""
    conn = _conn()
    stale = (datetime.now() - timedelta(minutes=10)).isoformat(timespec="seconds")
    conn.execute("UPDATE jobs SET status = 'pending' WHERE status = 'running' AND started_at < ?", (stale,))
    row = conn.execute("SELECT prid, lang FROM jobs WHERE status = 'pending' "
                       "ORDER BY requested_at, rowid LIMIT 1").fetchone()
    claimed = None
    if row:
        cur = conn.execute("UPDATE jobs SET status = 'running', started_at = ? "
                           "WHERE prid = ? AND lang = ? AND status = 'pending'", (_now(), *row))
        claimed = row if cur.rowcount == 1 else None
    conn.commit()
    conn.close()
    return claimed


def _finish(prid, lang, ok):
    conn = _conn()
    if ok:
        conn.execute("UPDATE jobs SET status = 'done' WHERE prid = ? AND lang = ?", (prid, lang))
    else:
        conn.execute("""UPDATE jobs SET attempts = attempts + 1,
                        status = CASE WHEN attempts + 1 >= ? THEN 'failed' ELSE 'pending' END
                        WHERE prid = ? AND lang = ?""", (MAX_ATTEMPTS, prid, lang))
    conn.commit()
    conn.close()


def run_one():
    """Ek kaam karo. None = queue khaali, True = bana, False = fail."""
    job = _claim()
    if not job:
        return None
    prid, lang = job
    conn = setup_releases()
    setup_alert_tables(conn)
    try:
        summary = cached_summary(conn, prid, lang)
    finally:
        conn.close()
    _finish(prid, lang, bool(summary))
    print(f"[queue] {prid} ({lang}): {'bana' if summary else 'fail'}")
    return bool(summary)


def _ai_was_busy():
    """Aakhri fail AI ke busy hone se tha (dono provider fail), ya sirf verify se?"""
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT step, detail FROM events WHERE status = 'fail' ORDER BY rowid DESC LIMIT 1").fetchone()
    conn.close()
    return bool(row) and row[0] == "summary" and "dono fail" in (row[1] or "")


def _loop():
    backoff = 0
    while True:
        try:
            result = run_one()
        except Exception as err:
            print("[queue] error:", err)
            result = False
        if result is None:
            time.sleep(5)                                   # kuch kaam nahi, thoda ruko
        elif result or not _ai_was_busy():
            backoff = 0                                     # bana, ya sirf verify fail: AI theek hai
            time.sleep(GAP_SECONDS)
        else:
            backoff = min(300, max(30, backoff * 2))        # 30s -> 1 -> 2 -> 4 -> 5 minute
            print(f"[queue] AI busy, {backoff}s ruk ke agla kaam")
            time.sleep(backoff)


@st.cache_resource
def start_queue_once():
    t = threading.Thread(target=_loop, daemon=True, name="summary-queue")
    t.start()
    print("[queue] Summary queue chalu")
    return t
