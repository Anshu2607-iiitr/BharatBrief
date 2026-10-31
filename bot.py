# Lesson 6: Telegram bot - user ka profile (role, rajya, bhasha) lena

import os
import sqlite3
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

DB_FILE = "practice.db"

ROLES = [("Student", "student"), ("Kisan", "kisan"), ("MSME / dukaan", "msme"),
         ("Mahila", "mahila"), ("Sabhi khabrein", "sabhi")]
STATES = [("Jharkhand", "Jharkhand"), ("Bihar", "Bihar"), ("Uttar Pradesh", "Uttar Pradesh"),
          ("West Bengal", "West Bengal"), ("Tamil Nadu", "Tamil Nadu"), ("Doosra rajya", "Other")]
LANGS = [("हिन्दी", "hi"), ("English", "en"), ("বাংলা", "bn"),
         ("தமிழ்", "ta"), ("తెలుగు", "te"), ("मराठी", "mr")]

ALLOWED_FIELDS = {"role", "state", "lang"}


# ---------- Database ----------
def setup_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            role        TEXT,
            state       TEXT,
            lang        TEXT,
            joined_at   TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_field(user_id, field, value):
    if field not in ALLOWED_FIELDS:      # column ka naam kabhi user se mat lo
        return
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT OR IGNORE INTO users (telegram_id, joined_at) VALUES (?, ?)",
        (user_id, datetime.now().isoformat(timespec="seconds")),
    )
    conn.execute(f"UPDATE users SET {field} = ? WHERE telegram_id = ?", (value, user_id))
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute(
        "SELECT role, state, lang FROM users WHERE telegram_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row


# ---------- Buttons ----------
def keyboard(prefix, options, cols=2):
    buttons = [InlineKeyboardButton(label, callback_data=f"{prefix}:{value}")
               for label, value in options]
    rows = [buttons[i:i + cols] for i in range(0, len(buttons), cols)]
    return InlineKeyboardMarkup(rows)


def label_of(options, value):
    for label, v in options:
        if v == value:
            return label
    return value


# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Main aapko nayi sarkari khabrein aasaan bhasha mein, "
        "awaaz mein bhejunga, original source ke link ke saath.\n\nAap kaun hain?",
        reply_markup=keyboard("role", ROLES),
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()                      # Telegram ko batao button click mil gaya
    prefix, value = q.data.split(":", 1)
    user_id = q.from_user.id

    if prefix == "role":
        save_field(user_id, "role", value)
        await q.edit_message_text(f"Aap: {label_of(ROLES, value)} ✓")
        await q.message.reply_text("Aap kis rajya se hain?", reply_markup=keyboard("state", STATES))

    elif prefix == "state":
        save_field(user_id, "state", value)
        await q.edit_message_text(f"Rajya: {label_of(STATES, value)} ✓")
        await q.message.reply_text("Khabar kis bhasha mein chahiye?", reply_markup=keyboard("lang", LANGS, cols=3))

    elif prefix == "lang":
        save_field(user_id, "lang", value)
        await q.edit_message_text(f"Bhasha: {label_of(LANGS, value)} ✓")
        await q.message.reply_text(
            "Ho gaya! Aapke liye nayi sarkari khabar aate hi main 1 minute ka voice note bhejunga.\n"
            "Apni settings dekhne ke liye /me likhein. Badalne ke liye /start."
        )


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    row = get_user(update.effective_user.id)
    if not row:
        await update.message.reply_text("Aapka profile nahi mila. /start se shuru karein.")
        return
    role, state, lang = row
    await update.message.reply_text(
        f"Aap: {label_of(ROLES, role)}\nRajya: {label_of(STATES, state)}\nBhasha: {label_of(LANGS, lang)}"
    )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN set nahi hai.")
        return

    setup_db()
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CallbackQueryHandler(on_button))

    print("Bot chal raha hai... band karne ke liye Ctrl+C")
    app.run_polling()


if __name__ == "__main__":
    main()
