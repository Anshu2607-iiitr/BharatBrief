# Lesson 15: Worker - website se alag, har UPDATE_MINUTES pakka update

import dbfix  # noqa: F401  (SQLite: WAL + 30s wait, sabse pehle)
import os
import threading
import time
from datetime import datetime

from auto_updater import UPDATE_MINUTES, update_once
from trace_log import log_event


def _keep_awake():
    """Render ka free server 15 min bina website traffic ke so jaata hai, aur saath mein bot bhi.
    Bot ka Telegram se baat karna 'traffic' nahi ginta. Isliye har 10 min apni hi website ko ek request."""
    import requests
    url = os.environ.get("RENDER_EXTERNAL_URL")       # Render khud deta hai; laptop pe nahi hota
    if not url:
        return
    print(f"[worker] keep-awake chalu: har 10 min {url}", flush=True)
    while True:
        time.sleep(10 * 60)
        try:
            requests.get(url.rstrip("/") + "/_stcore/health", timeout=30)
        except Exception as err:
            print("[worker] keep-awake ping fail:", err, flush=True)


def main():
    print(f"[worker] chalu: har {UPDATE_MINUTES} minute update. Band karne ke liye Ctrl+C", flush=True)
    threading.Thread(target=_keep_awake, daemon=True, name="keep-awake").start()
    if os.environ.get("BB_WORKER"):                   # server pe: summary queue bhi yahin chale
        import jobqueue
        threading.Thread(target=jobqueue._loop, daemon=True, name="summary-queue").start()
        print("[worker] summary queue bhi chalu", flush=True)
    while True:
        start = time.time()
        try:
            new = update_once(force=True, who="worker")
            print(f"[worker] {datetime.now():%d %b %H:%M} update ho gaya: {new} nayi releases", flush=True)
        except Exception as err:                      # kuch bhi ho, worker marna nahi chahiye
            print(f"[worker] {datetime.now():%H:%M} fail:", err, flush=True)
            log_event("-", "fetch", "fail", f"worker: {err}")
        # Kaam mein jitna time laga, utna kam so jao, taaki har 10 min ka rhythm bana rahe
        time.sleep(max(30, UPDATE_MINUTES * 60 - (time.time() - start)))


if __name__ == "__main__":
    main()
