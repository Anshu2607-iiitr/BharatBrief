# Updater ka core: nayi khabrein, unka time, summary pehle se. Worker aur website dono yahi use karte hain.

import os
import threading
import time
from datetime import datetime, timedelta

import streamlit as st

from alerts import cached_summary, collect_new, setup_alert_tables
from collector import backfill_posted
from collector import setup_db as setup_releases
from trace_log import _conn, log_event, simulate_pib_down

UPDATE_MINUTES = int(os.environ.get("UPDATE_MINUTES", "10"))
PREWARM_PER_RUN = int(os.environ.get("PREWARM_PER_RUN", "2"))
PREWARM_LANGS = os.environ.get("PREWARM_LANGS", "hi").split(",")


def last_update_time():
    conn = _conn()
    row = conn.execute("SELECT at FROM events WHERE step = 'fetch' ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return datetime.fromisoformat(row[0]) if row else None


def prewarm(conn):
    rows = conn.execute("""
        SELECT r.prid FROM releases r
        WHERE r.full_text != ''
          AND NOT EXISTS (SELECT 1 FROM summaries s WHERE s.prid = r.prid AND s.lang = 'hi')
          AND (SELECT COUNT(*) FROM events e WHERE e.prid = r.prid AND e.status = 'fail') < 4
        ORDER BY COALESCE(NULLIF(r.posted_at, 'unknown'), r.fetched_at) DESC
        LIMIT ?""", (PREWARM_PER_RUN,)).fetchall()
    made = 0
    for (prid,) in rows:
        for lang in PREWARM_LANGS:
            if cached_summary(conn, prid, lang.strip()):
                made += 1
            time.sleep(5)
    return made


def update_once(force=False, who="auto"):
    """force=False: agar haal hi mein update ho chuka hai to skip (double kaam se bachav)."""
    if not force:
        last = last_update_time()
        if last and datetime.now() - last < timedelta(minutes=UPDATE_MINUTES) - timedelta(seconds=30):
            return None
    conn = setup_releases()
    setup_alert_tables(conn)
    try:
        new = collect_new(conn)
        timed = backfill_posted(conn, limit=10)
        warmed = prewarm(conn)
    finally:
        conn.close()
    if not simulate_pib_down():
        log_event("-", "fetch", "ok", f"{who}: {new} nayi, {timed} ka time mila, {warmed} summary taiyaar")
    return new


def _loop():
    while True:
        start = time.time()
        try:
            result = update_once(who="website")
            if result is not None:
                print(f"[website] {datetime.now():%H:%M} update: {result} nayi releases")
        except Exception as err:
            print("[website] update fail:", err)
            log_event("-", "fetch", "fail", f"website: {err}")
        time.sleep(max(30, UPDATE_MINUTES * 60 - (time.time() - start)))


@st.cache_resource
def start_updater_once():
    """Backup updater: worker chal raha ho to ye khud skip kar deta hai."""
    t = threading.Thread(target=_loop, daemon=True, name="auto-updater")
    t.start()
    return t
