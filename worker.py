# Lesson 15: Worker - website se alag, har UPDATE_MINUTES pakka update

import dbfix  # noqa: F401  (SQLite: WAL + 30s wait, sabse pehle)
import os
import threading
import time
from datetime import datetime

from auto_updater import UPDATE_MINUTES, update_once
from trace_log import log_event


def main():
    print(f"[worker] chalu: har {UPDATE_MINUTES} minute update. Band karne ke liye Ctrl+C", flush=True)
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
