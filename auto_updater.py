# Lesson 14: Background updater - har kuch minute PIB se nayi khabrein khud laana

import os
import threading
import time
from datetime import datetime

import streamlit as st

from alerts import collect_new, setup_alert_tables
from collector import setup_db as setup_releases
from trace_log import log_event, simulate_pib_down

UPDATE_MINUTES = int(os.environ.get("UPDATE_MINUTES", "10"))


def update_once():
    """Ek baar PIB check karo, nayi releases DB mein daalo."""
    conn = setup_releases()
    setup_alert_tables(conn)
    try:
        new = collect_new(conn)
    finally:
        conn.close()
    if not simulate_pib_down():
        log_event("-", "fetch", "ok", f"{new} nayi releases (auto)")
    return new


def _loop():
    while True:
        try:
            print(f"[auto] {datetime.now():%H:%M} update: {update_once()} nayi releases")
        except Exception as err:                 # ek baar fail ho to thread marna nahi chahiye
            print("[auto] update fail:", err)
            log_event("-", "fetch", "fail", f"auto update: {err}")
        time.sleep(UPDATE_MINUTES * 60)


@st.cache_resource
def start_updater_once():
    """Server mein sirf EK thread chale, chahe kitne bhi log page kholein."""
    t = threading.Thread(target=_loop, daemon=True, name="auto-updater")
    t.start()
    print(f"[auto] Background updater chalu: har {UPDATE_MINUTES} minute")
    return t
