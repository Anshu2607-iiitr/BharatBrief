# Lesson 10: Ek command se saare APIs aur models check karna

import os
import sqlite3
import sys
import time

import requests
from google import genai

from collector import fetch_feed
from summarize import GEMINI_MODEL, GROQ_MODEL, GROQ_URL
from voice import SARVAM_MODEL, text_to_speech

DB_FILE = "practice.db"


def check_pib():
    entries = fetch_feed()
    return (len(entries) > 0, f"{len(entries)} releases")


def check_gemini():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return (False, "GEMINI_API_KEY set nahi")
    client = genai.Client(api_key=key, http_options={"timeout": 30000})
    try:
        resp = client.models.generate_content(model=GEMINI_MODEL, contents="Reply with just: OK")
        return (True, f"{GEMINI_MODEL} -> {resp.text.strip()[:20]}")
    except Exception as err:
        return (False, f"{GEMINI_MODEL}: {str(err)[:120]}")


def check_groq():
    key = os.environ.get("GROQ_API_KEY")
    if not key or not GROQ_MODEL:
        return (False, "GROQ_API_KEY ya model nahi")
    body = {"model": GROQ_MODEL, "max_tokens": 20,
            "messages": [{"role": "user", "content": "Reply with just: OK"}]}
    try:
        r = requests.post(GROQ_URL, json=body, timeout=30,
                          headers={"Authorization": f"Bearer {key}"})
    except requests.RequestException as err:
        return (False, f"network: {err}")
    if r.status_code != 200:
        return (False, f"{GROQ_MODEL}: {r.status_code} {r.text[:100]}")
    return (True, GROQ_MODEL)


def check_sarvam():
    path = "_check.wav"
    ok = text_to_speech("Namaste", "hi", path)
    if os.path.exists(path):
        os.remove(path)
    return (ok, SARVAM_MODEL)


def check_telegram():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return (False, "TELEGRAM_BOT_TOKEN set nahi")
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15)
        data = r.json()
    except Exception as err:
        return (False, f"network: {str(err)[:80]}")
    if data.get("ok"):
        return (True, "@" + data["result"]["username"])
    return (False, "token galat")        # token kabhi print nahi karte


def check_db():
    if not os.path.exists(DB_FILE):
        return (False, "practice.db nahi mili")
    conn = sqlite3.connect(DB_FILE)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    needed = {"releases", "users", "summaries", "processed", "sent_log"}
    missing = needed - tables
    counts = ", ".join(f"{t}={conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}"
                       for t in sorted(needed & tables))
    conn.close()
    if missing:
        return (False, f"tables nahi: {', '.join(sorted(missing))}")
    return (True, counts)


CHECKS = [
    ("PIB feed", check_pib),
    ("Gemini", check_gemini),
    ("Groq (backup)", check_groq),
    ("Sarvam TTS", check_sarvam),
    ("Telegram bot", check_telegram),
    ("Database", check_db),
]


def main():
    print("Health check chal raha hai...\n")
    results = {}
    for name, fn in CHECKS:
        start = time.time()
        try:
            ok, detail = fn()
        except Exception as err:
            ok, detail = False, f"crash: {str(err)[:100]}"
        ms = int((time.time() - start) * 1000)
        results[name] = ok
        mark = "[ OK ]" if ok else "[FAIL]"
        print(f"{mark} {name:<15} {ms:>6} ms   {detail}")

    print()
    ai_ok = results["Gemini"] or results["Groq (backup)"]
    if not results["Gemini"] and results["Groq (backup)"]:
        print("WARN: Gemini nahi chal raha, lekin Groq backup se kaam chalega.")
    must = ["PIB feed", "Sarvam TTS", "Telegram bot", "Database"]
    if ai_ok and all(results[m] for m in must):
        print("Sab taiyaar hai. Demo ke liye GO! ✓")
        sys.exit(0)
    print("Kuch zaroori cheez fail hai. Upar [FAIL] wali lines theek karo.")
    sys.exit(1)


if __name__ == "__main__":
    main()
