# Lesson 1: PIB ka Hindi press release RSS feed padhna

import feedparser
import requests

URL = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=2&Regid=3"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def fetch(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as err:
        print("Network problem:", err)
        return []

    print("HTTP status:", resp.status_code)
    print("Content-Type:", resp.headers.get("Content-Type"))

    if resp.status_code != 200:
        print("PIB ne sahi jawab nahi diya")
        return []

    if b"<rss" not in resp.content[:500]:
        print("Ye RSS nahi lag raha. Shuru ka hissa:")
        print(resp.text[:300])
        return []

    feed = feedparser.parse(resp.content)
    if feed.get("bozo"):
        print("Feed mein chhoti problem:", feed.get("bozo_exception"))
    return feed.entries


def main():
    entries = fetch(URL)
    print("Kitni entries mili:", len(entries))
    print("-" * 50)
    if not entries:
        return

    print("Fields:", list(entries[0].keys()))
    print("-" * 50)

    for e in entries[:5]:
        print("Title:", e.get("title"))
        print("Link: ", e.get("link"))
        print("Date: ", e.get("published", "date nahi mili"))
        print()


if __name__ == "__main__":
    main()
