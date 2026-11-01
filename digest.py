# Lesson 21: Subah ki digest - top 3 khabrein, ek voice note mein

import asyncio
import html
import os
import sqlite3
from datetime import datetime, time as dtime, timedelta, timezone

from telegram.constants import ParseMode
from telegram.ext import CommandHandler

from alerts import cached_summary, setup_alert_tables
from collector import setup_db as setup_releases
from voice import text_to_speech
from audio_util import send_clip
from trace_log import log_event

DB_FILE = "practice.db"
IST = timezone(timedelta(hours=5, minutes=30))     # Windows pe zoneinfo ke bina bhi chalega
DIGEST_HOUR = int(os.environ.get("DIGEST_HOUR", "8"))
TOP_N = 3

INTRO = {
    "hi": "🌅 <b>सुप्रभात! आज की 3 ज़रूरी सरकारी खबरें</b>",
    "en": "🌅 <b>Good morning! Today's 3 key government updates</b>",
}


def _setup(conn):
    setup_alert_tables(conn)
    conn.execute("""CREATE TABLE IF NOT EXISTS digest_log (
        telegram_id INTEGER, day TEXT, PRIMARY KEY (telegram_id, day))""")
    cols = [r[1] for r in conn.execute("PRAGMA table_info(users)")]
    if "voice" not in cols:                        # 👩 f / 👨 m
        conn.execute("ALTER TABLE users ADD COLUMN voice TEXT DEFAULT 'f'")
    if "digest" not in cols:                       # naya column: 1 = chalu (default), 0 = band
        conn.execute("ALTER TABLE users ADD COLUMN digest INTEGER DEFAULT 1")
    conn.commit()


def top_releases(conn, role, hours=24):
    """Pichhle 24 ghante: pehle user ke role wali, phir sabke liye, phir baaki. Naye pehle."""
    since = (datetime.now() - timedelta(hours=hours)).isoformat(timespec="seconds")
    rows = conn.execute("""
        SELECT r.prid, r.title, r.link, LOWER(TRIM(COALESCE(json_extract(s.json, '$.kiske_liye'), 'sabhi')))
        FROM releases r LEFT JOIN summaries s ON s.prid = r.prid AND s.lang = 'hi'
        WHERE r.full_text != ''
          AND COALESCE(NULLIF(r.posted_at, 'unknown'), r.fetched_at) >= ?
        ORDER BY COALESCE(NULLIF(r.posted_at, 'unknown'), r.fetched_at) DESC""", (since,)).fetchall()

    def rank(row):
        aud = row[3]
        return 0 if role and aud == role else (1 if aud == "sabhi" else 2)
    return sorted(rows, key=rank)                  # sorted() stable hai: same rank mein naya pehle


def build_digest(conn, lang, role, gender="f"):
    """(text, wav_path ya None). Summary na bane to agli khabar try karo."""
    items = []
    for prid, title, link, _ in top_releases(conn, role):
        s = cached_summary(conn, prid, lang)       # cache se, warna AI + verify
        if s:
            items.append((title, link, s))
        if len(items) == TOP_N:
            break
    if not items:
        return None, None

    e = html.escape
    lines = [INTRO.get(lang, INTRO["en"]), ""]
    voice_parts = []
    for i, (title, link, s) in enumerate(items, start=1):
        lines.append(f"<b>{i}. {e(title)}</b>\n{e(str(s.get('kya_hua', '')))}\n"
                     f'<a href="{e(link)}">PIB ↗</a>\n')
        voice_parts.append(f"{i}. {s.get('kya_hua', '')}")
    text = "\n".join(lines)

    day = datetime.now(IST).strftime("%Y%m%d")
    wav = f"digest_{day}_{lang}_{role or 'sabhi'}_{gender}.wav"
    if not os.path.exists(wav):
        script = " ".join(voice_parts)[:1400]      # TTS ki lambai limit ke andar
        if not text_to_speech(script, lang, wav, gender):
            wav = None
    return text, wav


def digest_users(conn, day):
    return conn.execute("""
        SELECT telegram_id, lang, role, COALESCE(voice, 'f') FROM users
        WHERE lang IS NOT NULL AND COALESCE(digest, 1) = 1
          AND telegram_id NOT IN (SELECT telegram_id FROM digest_log WHERE day = ?)""", (day,)).fetchall()


async def send_digest(bot, users, day, force=False):
    conn = setup_releases()
    _setup(conn)
    made = {}                                      # (lang, role, awaaz) -> (text, wav): ek baar banao, sabko bhejo
    sent = 0
    for uid, lang, role, *rest in users:
        k = (lang, (role or "").lower(), rest[0] if rest else "f")
        if k not in made:
            made[k] = await asyncio.to_thread(build_digest, conn, *k)
        text, wav = made[k]
        if not text:
            continue
        try:
            await bot.send_message(uid, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            if wav:
                await send_clip(bot, uid, wav, "Subah ki khabar (AI awaaz)")
            if not force:
                conn.execute("INSERT OR IGNORE INTO digest_log VALUES (?, ?)", (uid, day))
                conn.commit()
            sent += 1
        except Exception as err:
            print(f"[digest] {uid} ko nahi gaya:", err)
    conn.close()
    log_event("-", "digest", "ok", f"{sent} users ko bheja")
    print(f"[digest] {sent} users ko bheja")
    return sent


def register_digest(app):
    async def morning_job(context):
        day = datetime.now(IST).strftime("%Y-%m-%d")
        conn = setup_releases()
        _setup(conn)
        users = digest_users(conn, day)
        conn.close()
        await send_digest(context.bot, users, day)

    async def subah(update, context):
        """/subah = abhi bhejo (test) · /subah band · /subah chalu"""
        uid = update.effective_user.id
        arg = (context.args[0].lower() if context.args else "")
        conn = setup_releases()
        _setup(conn)
        if arg in ("band", "off", "stop"):
            conn.execute("UPDATE users SET digest = 0 WHERE telegram_id = ?", (uid,))
            conn.commit(); conn.close()
            await update.message.reply_text("🔕 Subah ki digest band. Wapas chalu: /subah chalu")
            return
        if arg in ("chalu", "on", "start"):
            conn.execute("UPDATE users SET digest = 1 WHERE telegram_id = ?", (uid,))
            conn.commit(); conn.close()
            await update.message.reply_text(f"🔔 Har subah {DIGEST_HOUR} baje digest aayegi.")
            return
        row = conn.execute("SELECT telegram_id, lang, role, COALESCE(voice, 'f') FROM users WHERE telegram_id = ?", (uid,)).fetchone()
        conn.close()
        if not row or not row[1]:
            await update.message.reply_text("Pehle /start se bhasha chuno.")
            return
        await update.message.reply_text("☕ Aaj ki digest bana raha hoon, 1-2 minute...")
        day = datetime.now(IST).strftime("%Y-%m-%d")
        if not await send_digest(context.bot, [row], day, force=True):
            await update.message.reply_text("Pichhle 24 ghante mein abhi koi verified khabar nahi mili.")

    app.add_handler(CommandHandler("subah", subah))
    if app.job_queue:
        app.job_queue.run_daily(morning_job, time=dtime(DIGEST_HOUR, 0, tzinfo=IST))
        print(f"Subah ki digest chalu: roz {DIGEST_HOUR}:00 IST")
