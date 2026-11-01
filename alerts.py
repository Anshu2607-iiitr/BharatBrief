# Lesson 9: Proactive alerts - nayi release -> matching users ko unki bhasha mein

import asyncio
import json
import os
import sqlite3
import time
from datetime import datetime

from telegram.constants import ParseMode
from telegram.ext import CommandHandler

from collector import already_saved, fetch_feed, fetch_page, fetch_text, get_prid, save
from collector import setup_db as setup_releases
from voice import text_to_speech, verified_summary, voice_file, voice_script
from trace_log import log_event
from reminders import reminder_keyboard
from audio_util import send_clip

DB_FILE = "practice.db"
MAX_PER_RUN = int(os.environ.get("ALERT_MAX_PER_RUN", "2"))     # ek baar mein kitni releases
ALERT_MINUTES = int(os.environ.get("ALERT_MINUTES", "10"))     # kitni der mein check


def now():
    return datetime.now().isoformat(timespec="seconds")


# ---------- Tables ----------
def setup_alert_tables(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS summaries (
        prid TEXT, lang TEXT, json TEXT, created_at TEXT, PRIMARY KEY (prid, lang))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS processed (
        prid TEXT PRIMARY KEY, audience TEXT, processed_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS sent_log (
        telegram_id INTEGER, prid TEXT, sent_at TEXT, PRIMARY KEY (telegram_id, prid))""")
    conn.commit()


# ---------- Step 1: nayi releases ----------
def collect_new(conn, limit=20):
    new = 0
    for e in fetch_feed()[:limit]:
        link = e.get("link")
        prid = get_prid(link)
        if not prid or already_saved(conn, prid):
            continue
        text, posted_at = fetch_page(link)
        if not text:
            continue
        save(conn, prid, e.get("title"), link, text, posted_at)
        new += 1
        time.sleep(1)
    return new


# ---------- Step 2-4: summary, matching, awaaz ----------
def cached_summary(conn, prid, lang):
    row = conn.execute("SELECT json FROM summaries WHERE prid = ? AND lang = ?",
                       (prid, lang)).fetchone()
    if row:
        return json.loads(row[0])
    s = verified_summary(prid, lang)
    if s:
        conn.execute("INSERT OR REPLACE INTO summaries VALUES (?, ?, ?, ?)",
                     (prid, lang, json.dumps(s, ensure_ascii=False), now()))
        conn.commit()
    return s


def pending_releases(conn):
    return conn.execute("""
        SELECT prid, title, link FROM releases r
        WHERE full_text != ''
          AND NOT EXISTS (SELECT 1 FROM processed p WHERE p.prid = r.prid)
        ORDER BY CAST(prid AS INTEGER) DESC LIMIT ?""", (MAX_PER_RUN,)).fetchall()


def matching_users(conn, audience):
    if audience == "sabhi":
        sql, args = "SELECT telegram_id, lang, COALESCE(voice, 'f') FROM users WHERE lang IS NOT NULL", ()
    else:
        sql = "SELECT telegram_id, lang, COALESCE(voice, 'f') FROM users WHERE lang IS NOT NULL AND role IN (?, 'sabhi')"
        args = (audience,)
    return conn.execute(sql, args).fetchall()


def already_sent(conn, uid, prid):
    return conn.execute("SELECT 1 FROM sent_log WHERE telegram_id = ? AND prid = ?",
                        (uid, prid)).fetchone() is not None


def mark_sent(uid, prid):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR IGNORE INTO sent_log VALUES (?, ?, ?)", (uid, prid, now()))
    conn.commit()
    conn.close()


def run_once():
    """Ek round: nayi releases laao aur bhejne layak messages taiyaar karo."""
    conn = setup_releases()
    setup_alert_tables(conn)
    new = collect_new(conn)
    log_event("-", "fetch", "ok", f"{new} nayi releases")
    print(f"[alert] Nayi releases: {new}")

    deliveries = []
    for prid, title, link in pending_releases(conn):
        base = cached_summary(conn, prid, "hi")
        if not base:
            print(f"[alert] {prid}: verify nahi hui, skip")
            conn.execute("INSERT OR REPLACE INTO processed VALUES (?, ?, ?)", (prid, "unverified", now()))
            conn.commit()
            continue

        audience = str(base.get("kiske_liye", "sabhi")).strip().lower()
        users = [(u, l, g) for u, l, g in matching_users(conn, audience) if not already_sent(conn, u, prid)]
        log_event(prid, "match", "ok", f"{audience} · {len(users)} users")
        print(f"[alert] {prid}: kiske_liye={audience}, users={len(users)}")

        for uid, lang, g in users:
            s = base if lang == "hi" else cached_summary(conn, prid, lang)
            if not s:
                continue
            audio = voice_file(prid, lang, g)
            if not os.path.exists(audio) and not text_to_speech(voice_script(s, lang), lang, audio, g):
                audio = None
            deliveries.append({"uid": uid, "prid": prid, "title": title,
                               "link": link, "summary": s, "audio": audio})

        conn.execute("INSERT OR REPLACE INTO processed VALUES (?, ?, ?)", (prid, audience, now()))
        conn.commit()

    conn.close()
    return deliveries


# ---------- Step 5: Telegram pe bhejna ----------
async def deliver(bot, deliveries, card_fn):
    sent = 0
    for d in deliveries:
        try:
            await bot.send_message(d["uid"], card_fn(d["title"], d["link"], d["summary"]),
                                   parse_mode=ParseMode.HTML, disable_web_page_preview=True,
                                   reply_markup=reminder_keyboard(d["prid"], d["summary"]))
            if d["audio"]:
                await send_clip(bot, d["uid"], d["audio"], "Nayi khabar (AI awaaz)")
            mark_sent(d["uid"], d["prid"])
            log_event(d["prid"], "send", "ok", "voice + card bheja")
            sent += 1
        except Exception as err:
            log_event(d["prid"], "send", "fail", str(err))
            print(f"[alert] {d['uid']} ko bhejne mein dikkat:", err)
    return sent


def register_alerts(app, card_fn):
    """bot.py se bulaya jaata hai: /check command + har ALERT_MINUTES ka timer."""

    async def alert_job(context):
        deliveries = await asyncio.to_thread(run_once)
        sent = await deliver(context.bot, deliveries, card_fn)
        print(f"[alert] {len(deliveries)} taiyaar, {sent} bheje")

    async def check_now(update, context):
        await update.message.reply_text("Nayi khabrein check kar raha hoon, 1-2 minute lagenge...")
        deliveries = await asyncio.to_thread(run_once)
        sent = await deliver(context.bot, deliveries, card_fn)
        await update.message.reply_text(f"Ho gaya: {sent} alert bheje.")

    app.add_handler(CommandHandler("check", check_now))
    if app.job_queue:
        app.job_queue.run_repeating(alert_job, interval=ALERT_MINUTES * 60, first=60)
        print(f"Auto alerts chalu: har {ALERT_MINUTES} minute")
    else:
        print('Auto alerts band: pip install "python-telegram-bot[job-queue]" karo')
