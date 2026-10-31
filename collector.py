# Lesson 3: Feed + text ko SQLite mein save karna, duplicate rokna

import re
import sqlite3
import time
from datetime import datetime

import feedparser
import requests
from bs4 import BeautifulSoup

from trace_log import log_event, simulate_pib_down

FEED_URL = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=2&Regid=3"
DB_FILE = "practice.db"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


# ---------- Database ----------
def setup_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS releases (
            prid        TEXT PRIMARY KEY,
            title       TEXT,
            link        TEXT,
            full_text   TEXT,
            fetched_at  TEXT
        )
    """)
    conn.commit()
    return conn


def already_saved(conn, prid):
    row = conn.execute("SELECT 1 FROM releases WHERE prid = ?", (prid,)).fetchone()
    return row is not None


def save(conn, prid, title, link, text):
    conn.execute(
        "INSERT INTO releases (prid, title, link, full_text, fetched_at) VALUES (?, ?, ?, ?, ?)",
        (prid, title, link, text, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()


# ---------- PIB ----------
def get(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp
        print("  Status:", resp.status_code, "for", url)
    except requests.RequestException as err:
        print("  Network problem:", err)
    return None


def fetch_feed():
    if simulate_pib_down():
        print("PIB down (demo toggle) - purane data se kaam chalega")
        log_event("-", "fetch", "fail", "PIB down (demo toggle)")
        return []
    resp = get(FEED_URL)
    if resp is None or b"<rss" not in resp.content[:500]:
        print("Feed nahi mili, baad mein dobara try karo")
        return []
    return feedparser.parse(resp.content).entries


def get_prid(link):
    m = re.search(r"PRID=(\d+)", link or "")
    return m.group(1) if m else None


def fetch_text(link):
    resp = get(link)
    if resp is None:
        return ""
    soup = BeautifulSoup(resp.content, "html.parser")
    paras, seen = [], set()
    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if len(text) > 40 and text not in seen:
            seen.add(text)
            paras.append(text)
    return "\n\n".join(paras)


# ---------- Main ----------
def main(limit=5):
    conn = setup_db()
    entries = fetch_feed()
    print("Feed mein releases:", len(entries))

    new, skipped = 0, 0
    for e in entries[:limit]:
        link = e.get("link")
        prid = get_prid(link)
        if not prid:
            continue

        if already_saved(conn, prid):
            skipped += 1
            continue

        text = fetch_text(link)
        save(conn, prid, e.get("title"), link, text)
        new += 1
        print(f"  Saved {prid}: {len(text)} akshar")
        time.sleep(1)  # PIB server pe ek saath bojh na daalein

    total = conn.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
    print(f"Naye: {new} | Pehle se the (skip): {skipped} | DB mein total: {total}")
    conn.close()


if __name__ == "__main__":
    main()
