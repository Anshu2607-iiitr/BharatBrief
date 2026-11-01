# Lesson 19: Deadline reminders - Telegram button, deep link, calendar (.ics) file

import functools
import html
import os
import re
import sqlite3
from datetime import date, datetime, timedelta

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler

DB_FILE = "practice.db"


def _conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""CREATE TABLE IF NOT EXISTS reminders (
        telegram_id INTEGER, prid TEXT, due_date TEXT, remind_on TEXT, sent INTEGER DEFAULT 0,
        PRIMARY KEY (telegram_id, prid, due_date))""")
    return conn


def future_dates(summary, limit=2):
    """Summary ki verified tareekhon mein se sirf aaj ya aage ki."""
    out = set()
    for d in summary.get("tareekh_iso", []) or []:
        try:
            if date.fromisoformat(str(d)) >= date.today():
                out.add(str(d))
        except ValueError:
            pass
    return sorted(out)[:limit]


def add_reminder(telegram_id, prid, due):
    due_d = date.fromisoformat(due)
    remind_on = max(due_d - timedelta(days=1), date.today())
    conn = _conn()
    conn.execute("INSERT OR IGNORE INTO reminders (telegram_id, prid, due_date, remind_on) VALUES (?, ?, ?, ?)",
                 (telegram_id, prid, due, remind_on.isoformat()))
    conn.commit()
    conn.close()
    return remind_on


def parse_deeplink(args):
    """Website ka link: /start rem_2330875_20261231 -> ('2330875', '2026-12-31')."""
    if not args:
        return None
    m = re.fullmatch(r"rem_(\d+)_(\d{4})(\d{2})(\d{2})", args[0])
    return (m.group(1), f"{m.group(2)}-{m.group(3)}-{m.group(4)}") if m else None


def reminder_keyboard(prid, summary):
    dates = future_dates(summary or {})
    if not dates:
        return None
    buttons = [[InlineKeyboardButton(f"⏰ Yaad dilao · {date.fromisoformat(d):%d %b}",
                                     callback_data=f"rem:{prid}:{d}")] for d in dates]
    return InlineKeyboardMarkup(buttons)


def ics_file(prid, title, link, due):
    """Calendar file: tareekh ke din ka event, ek din pehle alarm."""
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    d1, d2 = due.strftime("%Y%m%d"), (due + timedelta(days=1)).strftime("%Y%m%d")
    safe = title.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", " ")[:150]
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//BharatBrief//EN", "BEGIN:VEVENT",
             f"UID:{prid}-{d1}@bharatbrief", f"DTSTAMP:{stamp}",
             f"DTSTART;VALUE=DATE:{d1}", f"DTEND;VALUE=DATE:{d2}",
             f"SUMMARY:{safe}", f"DESCRIPTION:{link}",
             "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", "DESCRIPTION:BharatBrief reminder", "END:VALARM",
             "END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lines) + "\r\n"


@functools.lru_cache(maxsize=1)
def bot_username():
    """Bot ka @username, website ke Telegram link ke liye (sirf ek baar poochte hain)."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return ""
    try:
        return requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10).json()["result"]["username"]
    except Exception:
        return ""


def register_reminders(app):
    """bot.py se: har ghante reminders check karo + /yaad command."""

    async def check(context):
        conn = _conn()
        rows = conn.execute("""
            SELECT r.telegram_id, r.prid, r.due_date, rel.title, rel.link
            FROM reminders r JOIN releases rel ON rel.prid = r.prid
            WHERE r.sent = 0 AND r.remind_on <= ?""", (date.today().isoformat(),)).fetchall()
        for uid, prid, due, title, link in rows:
            try:
                d = date.fromisoformat(due)
                await context.bot.send_message(
                    uid, f"⏰ <b>Yaad dilana:</b> {d:%d %b %Y} ki tareekh aa rahi hai\n\n"
                         f"{html.escape(title)}\n\n<a href=\"{html.escape(link)}\">PIB release padhein</a>",
                    parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                conn.execute("UPDATE reminders SET sent = 1 WHERE telegram_id = ? AND prid = ? AND due_date = ?",
                             (uid, prid, due))
                conn.commit()
            except Exception as err:
                print("[reminder] bhejne mein dikkat:", err)
        conn.close()

    async def list_cmd(update, context):
        conn = _conn()
        rows = conn.execute("""
            SELECT r.due_date, rel.title FROM reminders r JOIN releases rel ON rel.prid = r.prid
            WHERE r.telegram_id = ? AND r.sent = 0 ORDER BY r.due_date""",
                            (update.effective_user.id,)).fetchall()
        conn.close()
        if not rows:
            await update.message.reply_text("Abhi koi reminder nahi hai. Khabar ke neeche ⏰ button dabaiye.")
            return
        text = "\n".join(f"⏰ {date.fromisoformat(d):%d %b %Y} · {t[:70]}" for d, t in rows)
        await update.message.reply_text("Aapke reminders:\n\n" + text)

    app.add_handler(CommandHandler("yaad", list_cmd))
    if app.job_queue:
        app.job_queue.run_repeating(check, interval=3600, first=20)
