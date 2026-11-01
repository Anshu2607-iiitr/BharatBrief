# Lesson 8: Bot - onboarding + /khabar (verified summary + voice note)

import dbfix  # noqa: F401  (SQLite: WAL + 30s wait, sabse pehle)
import asyncio
import html
import os
import sqlite3
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from voice import text_to_speech, verified_summary, voice_script
from alerts import register_alerts
from reminders import add_reminder, parse_deeplink, register_reminders, reminder_keyboard
from qa import answer_question, answer_text_telegram, last_sent_prid
from audio_util import send_clip
from digest import register_digest

DB_FILE = "practice.db"

ROLES = [("Student", "student"), ("Kisan", "kisan"), ("MSME / dukaan", "msme"),
         ("Mahila", "mahila"), ("Sabhi khabrein", "sabhi")]
STATES = [("Jharkhand", "Jharkhand"), ("Bihar", "Bihar"), ("Uttar Pradesh", "Uttar Pradesh"),
          ("West Bengal", "West Bengal"), ("Tamil Nadu", "Tamil Nadu"), ("Doosra rajya", "Other")]
LANGS = [("हिन्दी", "hi"), ("English", "en"), ("বাংলা", "bn"),
         ("தமிழ்", "ta"), ("తెలుగు", "te"), ("मराठी", "mr")]

ALLOWED_FIELDS = {"role", "state", "lang"}
from languages import ALL as _ALL_LANGS
LANGS = [(v["native"], c) for c, v in _ALL_LANGS.items()]


# ---------- Database ----------
def setup_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            role TEXT, state TEXT, lang TEXT, joined_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_field(user_id, field, value):
    if field not in ALLOWED_FIELDS:
        return
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR IGNORE INTO users (telegram_id, joined_at) VALUES (?, ?)",
                 (user_id, datetime.now().isoformat(timespec="seconds")))
    conn.execute(f"UPDATE users SET {field} = ? WHERE telegram_id = ?", (value, user_id))
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT role, state, lang FROM users WHERE telegram_id = ?",
                       (user_id,)).fetchone()
    conn.close()
    return row


def latest_release():
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT prid, title, link FROM releases "
                       "WHERE full_text != '' ORDER BY fetched_at DESC, prid DESC LIMIT 1").fetchone()
    conn.close()
    return row


# ---------- Helpers ----------
def keyboard(prefix, options, cols=2):
    buttons = [InlineKeyboardButton(label, callback_data=f"{prefix}:{value}")
               for label, value in options]
    return InlineKeyboardMarkup([buttons[i:i + cols] for i in range(0, len(buttons), cols)])


def label_of(options, value):
    for label, v in options:
        if v == value:
            return label
    return value


def summary_card(title, link, s):
    e = html.escape
    return (
        f"<b>{e(title)}</b>\n\n"
        f"<b>Kya hua:</b> {e(s.get('kya_hua', ''))}\n\n"
        f"<b>Aap pe asar:</b> {e(s.get('aap_pe_asar', ''))}\n\n"
        f"<b>Aapko kya karna hai:</b> {e(s.get('kya_karna_hai', ''))}\n\n"
        f"✓ Har number aur tareekh original release se check ki gayi\n"
        f"Source: <a href=\"{e(link)}\">PIB press release</a>"
    )


# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rem = parse_deeplink(context.args)          # website ka 'Telegram pe yaad dilao' link
    if rem:
        when = add_reminder(update.effective_user.id, *rem)
        await update.message.reply_text(f"⏰ Theek hai! {when:%d %b} ko is khabar ki tareekh yaad dilaunga. "
                                        "Apne reminders dekhne ke liye /yaad likhein.")
        return
    await update.message.reply_text(
        "Namaste! Main aapko nayi sarkari khabrein aasaan bhasha mein, awaaz mein "
        "bhejunga, original source ke link ke saath.\n\nAap kaun hain?",
        reply_markup=keyboard("role", ROLES))


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    prefix, value = q.data.split(":", 1)
    uid = q.from_user.id

    if prefix == "rem":
        rem_prid, due = value.split(":", 1)
        when = add_reminder(uid, rem_prid, due)
        await q.message.reply_text(f"⏰ Theek hai! {when:%d %b} ko yaad dilaunga. /yaad se apne reminders dekhein.")
        return
    if prefix == "role":
        save_field(uid, "role", value)
        await q.edit_message_text(f"Aap: {label_of(ROLES, value)} ✓")
        await q.message.reply_text("Aap kis rajya se hain?", reply_markup=keyboard("state", STATES))
    elif prefix == "state":
        save_field(uid, "state", value)
        await q.edit_message_text(f"Rajya: {label_of(STATES, value)} ✓")
        await q.message.reply_text("Khabar kis bhasha mein chahiye?",
                                   reply_markup=keyboard("lang", LANGS, cols=3))
    elif prefix == "lang":
        save_field(uid, "lang", value)
        await q.edit_message_text(f"Bhasha: {label_of(LANGS, value)} ✓")
        await q.message.reply_text("Ho gaya! Abhi ki khabar sunne ke liye /khabar likhein.\n"
                                   "Settings dekhne ke liye /me, badalne ke liye /start.")


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    row = get_user(update.effective_user.id)
    if not row:
        await update.message.reply_text("Aapka profile nahi mila. /start se shuru karein.")
        return
    role, state, lang = row
    await update.message.reply_text(
        f"Aap: {label_of(ROLES, role)}\nRajya: {label_of(STATES, state)}\nBhasha: {label_of(LANGS, lang)}")


async def khabar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    row = get_user(update.effective_user.id)
    lang = (row[2] if row and row[2] else "hi")

    release = latest_release()
    if not release:
        await update.message.reply_text("Abhi koi khabar nahi hai. Thodi der baad try karein.")
        return
    prid, title, link = release

    await update.message.reply_text("Khabar taiyaar ho rahi hai, 30-60 second lagenge...")

    # AI calls blocking hain, isliye alag thread mein, taaki bot baaki users ke liye na ruke
    summary = await asyncio.to_thread(verified_summary, prid, lang)
    if not summary:
        await update.message.reply_text(
            "Maaf kijiye, is khabar ki summary verify nahi ho paayi, isliye nahi bhej rahe. "
            f"Original yahan padhein: {link}")
        return

    context.user_data["last_prid"] = prid
    await update.message.reply_text(summary_card(title, link, summary),
                                     parse_mode=ParseMode.HTML,
                                     disable_web_page_preview=True,
                                     reply_markup=reminder_keyboard(prid, summary))

    audio_path = f"khabar_{prid}_{lang}.wav"
    if not os.path.exists(audio_path):
        ok = await asyncio.to_thread(text_to_speech, voice_script(summary, lang), lang, audio_path)
        if not ok:
            await update.message.reply_text("Awaaz abhi nahi ban paayi, upar likhi khabar padhein.")
            return

    await send_clip(context.bot, update.effective_chat.id, audio_path, "Khabar (AI awaaz)")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Koi bhi likha hua message = aakhri khabar ke baare mein sawaal."""
    question = (update.message.text or "").strip()
    uid = update.effective_user.id
    prid = context.user_data.get("last_prid") or last_sent_prid(uid)
    if not prid:
        await update.message.reply_text("Pehle /khabar se koi khabar lijiye, phir uske baare mein sawaal poochiye.")
        return
    row = get_user(uid)
    lang = row[2] if row and row[2] else "hi"
    await update.message.reply_text("Sawaal mila, khabar mein jawab dhoondh raha hoon...")
    res = await asyncio.to_thread(answer_question, prid, question, lang)
    await update.message.reply_text(answer_text_telegram(res), parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN set nahi hai.")
        return
    setup_db()
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("khabar", khabar))
    app.add_handler(CallbackQueryHandler(on_button))
    register_alerts(app, summary_card)
    register_reminders(app)
    register_digest(app)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    print("Bot chal raha hai... band karne ke liye Ctrl+C (na chale to: taskkill /IM python.exe /F)")
    app.run_polling()


if __name__ == "__main__":
    main()
