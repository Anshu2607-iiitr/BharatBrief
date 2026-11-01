# Lesson 3 (+ updates): PIB feed + text + posted time, SQLite, duplicate rokna

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
MONTHS = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
          "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}


# ---------- Database ----------
def setup_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS releases (
            prid TEXT PRIMARY KEY, title TEXT, link TEXT,
            full_text TEXT, fetched_at TEXT, posted_at TEXT
        )
    """)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(releases)")}
    if "posted_at" not in cols:                       # purani DB mein naya column
        conn.execute("ALTER TABLE releases ADD COLUMN posted_at TEXT")
    conn.commit()
    return conn


def already_saved(conn, prid):
    return conn.execute("SELECT 1 FROM releases WHERE prid = ?", (prid,)).fetchone() is not None


def save(conn, prid, title, link, text, posted_at=None):
    conn.execute(
        "INSERT OR IGNORE INTO releases (prid, title, link, full_text, fetched_at, posted_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (prid, title, link, text, datetime.now().isoformat(timespec="seconds"), posted_at),
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


def parse_posted(page_text):
    """Page pe likha '31 OCT 2026 4:15PM' -> '2026-10-31T16:15'. Na mile to None."""
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})[A-Za-z]*\s+(\d{4})\s+(\d{1,2}):(\d{2})\s*([AaPp][Mm])",
                  page_text)
    if not m:
        return None
    day, mon, year, hh, mm, ap = m.groups()
    month = MONTHS.get(mon.upper())
    if not month:
        return None
    hour = int(hh) % 12 + (12 if ap.upper() == "PM" else 0)
    try:
        return datetime(int(year), month, int(day), hour, int(mm)).isoformat(timespec="minutes")
    except ValueError:
        return None


def fetch_page(link):
    """Release page se (text, posted_at) dono."""
    resp = get(link)
    if resp is None:
        return "", None
    soup = BeautifulSoup(resp.content, "html.parser")
    posted = parse_posted(soup.get_text(" ", strip=True))
    paras, seen = [], set()
    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if len(text) > 40 and text not in seen:
            seen.add(text)
            paras.append(text)
    return "\n\n".join(paras), posted


def fetch_text(link):
    return fetch_page(link)[0]


def backfill_posted(conn, limit=10):
    """Purani releases jinka time nahi hai, unka time bharo."""
    rows = conn.execute("SELECT prid, link FROM releases WHERE posted_at IS NULL "
                        "ORDER BY CAST(prid AS INTEGER) DESC LIMIT ?", (limit,)).fetchall()
    found = 0
    for prid, link in rows:
        _, posted = fetch_page(link)
        conn.execute("UPDATE releases SET posted_at = ? WHERE prid = ?", (posted or "unknown", prid))
        conn.commit()
        found += posted is not None
        time.sleep(1)
    return found


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
        text, posted = fetch_page(link)
        save(conn, prid, e.get("title"), link, text, posted)
        new += 1
        print(f"  Saved {prid}: {len(text)} akshar, posted {posted}")
        time.sleep(1)
    total = conn.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
    print(f"Naye: {new} | Pehle se the (skip): {skipped} | DB mein total: {total}")
    conn.close()


if __name__ == "__main__":
    main()
