# Lesson 22: SQLite ko kai process ke saath chalana (worker + bot + website ek hi practice.db pe)
#
# Dikkat: default SQLite mein jab koi likh raha ho to baaki sab (padhne wale bhi) ruk jaate hain,
# aur sqlite3.connect() sirf 5 second rukta hai -> "database is locked".
# Hal:
#   WAL mode     -> padhne wale likhne wale ko nahi rokte (aur ulta bhi). DB file mein yaad rehta hai.
#   timeout=30   -> do likhne wale takraayein to 30 sec tak baari ka intezaar, turant error nahi.
#
# Har entry file (Home.py, bot.py, worker.py) ki SABSE PEHLI line: import dbfix

import sqlite3

_original_connect = sqlite3.connect


def _connect(database, *args, **kwargs):
    kwargs.setdefault("timeout", 30)
    conn = _original_connect(database, *args, **kwargs)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA synchronous=NORMAL")      # WAL ke saath safe aur tez
    except sqlite3.OperationalError:
        pass                                          # pehli baar lock mila to bhi connection de do
    return conn


if sqlite3.connect is not _connect and getattr(sqlite3.connect, "__name__", "") != "_connect":
    sqlite3.connect = _connect                        # baaki saari files isi ko use karengi


def _ensure_wal(path="practice.db", tries=10):
    """Process shuru hote hi ek baar WAL pakka karo, aur log mein batao (Render logs mein dikhega)."""
    import time
    for i in range(tries):
        try:
            c = _original_connect(path, timeout=30)
            mode = c.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            c.close()
            print(f"[db] journal_mode = {mode}", flush=True)
            if mode.lower() == "wal":
                return True
        except sqlite3.OperationalError as err:
            print(f"[db] WAL try {i + 1}: {err}", flush=True)
        time.sleep(1)
    return False


_ensure_wal()
