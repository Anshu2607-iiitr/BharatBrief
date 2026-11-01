# Lesson 23: Telegram-first bot
# Badi buttons (commands yaad nahi rakhne), user ki bhasha, role ke hisaab se "agli khabar",
# WhatsApp share, aur awaaz se sawaal -> jawab awaaz mein.

import dbfix  # noqa: F401  (SQLite: WAL + 30s wait, sabse pehle)
import asyncio
import html
import os
import sqlite3
import tempfile
import time
import urllib.parse
from datetime import date, datetime

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from alerts import cached_summary, mark_sent, register_alerts, setup_alert_tables
from audio_util import send_clip
from bot_text import t
from collector import setup_db as setup_releases
from digest import IST, register_digest, send_digest, top_releases
from digest import _setup as setup_digest_tables
from labels import LABELS, ROLES as ROLE_MAP
from languages import ALL as ALL_LANGS
from qa import answer_question, last_sent_prid
from reminders import add_reminder, future_dates, parse_deeplink, register_reminders
from voice import text_to_speech, voice_file, voice_script
from voice_input import transcribe
from translate import translated_titles

DB_FILE = "practice.db"
ROLES = list(ROLE_MAP.items())                       # [("छात्र · Student", "student"), ...]
LANGS = [(v["native"], c) for c, v in ALL_LANGS.items()]
ALLOWED_FIELDS = {"role", "state", "lang"}


# ---------- Database ----------
def setup_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY, role TEXT, state TEXT, lang TEXT, joined_at TEXT)""")
    conn.commit()
    setup_digest_tables(conn)                        # users.digest column
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
    """(role, lang, digest, voice) ya None."""
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT role, lang, COALESCE(digest, 1), COALESCE(voice, 'f') FROM users WHERE telegram_id = ?",
                       (user_id,)).fetchone()
    conn.close()
    return row


def lang_of(user_id):
    row = get_user(user_id)
    return row[1] if row and row[1] else "hi"


def voice_of(user_id):
    row = get_user(user_id)
    return row[3] if row else "f"


def toggle_voice(user_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE users SET voice = CASE WHEN COALESCE(voice, 'f') = 'f' THEN 'm' ELSE 'f' END "
                 "WHERE telegram_id = ?", (user_id,))
    conn.commit()
    conn.close()


def toggle_digest(user_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE users SET digest = 1 - COALESCE(digest, 1) WHERE telegram_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ---------- Keyboards ----------
def main_menu(lang):
    """Neeche hamesha dikhne wale bade buttons: commands yaad rakhne ki zaroorat nahi."""
    return ReplyKeyboardMarkup([[t(lang, "btn_news"), t(lang, "btn_digest")],
                                [t(lang, "btn_ask"), t(lang, "btn_settings")]],
                               resize_keyboard=True, is_persistent=True)


def grid(prefix, options, cols=2):
    buttons = [InlineKeyboardButton(label, callback_data=f"{prefix}:{value}") for label, value in options]
    return InlineKeyboardMarkup([buttons[i:i + cols] for i in range(0, len(buttons), cols)])


def label_of(options, value):
    return next((label for label, v in options if v == value), value or "-")


def news_keyboard(prid, title, s, lang, bot_username):
    share_text = (f"📰 {title}\n\n{s.get('kya_hua', '')}\n\n{t(lang, 'share_from')} "
                  f"https://t.me/{bot_username}")[:900]
    rows = [[InlineKeyboardButton(t(lang, "next"), callback_data="next:1"),
             InlineKeyboardButton(t(lang, "share"), url="https://wa.me/?text=" + urllib.parse.quote(share_text))]]
    for d in future_dates(s):
        rows.append([InlineKeyboardButton(t(lang, "remind", d=f"{date.fromisoformat(d):%d %b}"),
                                          callback_data=f"rem:{prid}:{d}")])
    return InlineKeyboardMarkup(rows)


# ---------- Khabar ka card (user ki bhasha mein labels) ----------
SCRIPTS = [("bn", 0x0980, 0x09FF), ("ta", 0x0B80, 0x0BFF), ("te", 0x0C00, 0x0C7F), ("hi", 0x0900, 0x097F)]


def guess_lang(text):
    """Alerts mein bhasha pata nahi hoti: summary ki lipi (script) se andaza."""
    for ch in text or "":
        for code, lo, hi_ in SCRIPTS:
            if lo <= ord(ch) <= hi_:
                return code
    return "en" if any(c.isascii() and c.isalpha() for c in (text or "")) else "hi"


def card(title, link, s, lang=None):
    lang = lang or guess_lang(s.get("kya_hua", ""))
    L = LABELS.get(lang, LABELS["en"])
    e = html.escape
    return (f"📰 <b>{e(title)}</b>\n\n"
            f"<b>{e(L['kya'])}:</b> {e(str(s.get('kya_hua', '')))}\n\n"
            f"<b>{e(L['asar'])}:</b> {e(str(s.get('aap_pe_asar', '')))}\n\n"
            f"<b>{e(L['karna'])}:</b> {e(str(s.get('kya_karna_hai', '')))}\n\n"
            f"<i>{e(L['checked'])}</i>\n"
            f'🔗 <a href="{e(link)}">{e(L["original"])}</a>')


# ---------- Agli khabar chunna ----------
def pick_next(role, lang, seen, tries=3):
    """Role wali khabrein pehle, naye pehle. Jinki summary cache mein hai unhe pehle (turant jawab).
    Return (prid, title, link, summary) ya None, aur jo khabrein verify nahi hui unki list."""
    conn = setup_releases()
    setup_alert_tables(conn)
    skipped = []
    try:
        rows = top_releases(conn, role if role != "sabhi" else None, hours=72)
        if not rows:                                  # 3 din mein kuch nahi: jo bhi sabse naya hai
            rows = conn.execute("""SELECT prid, title, link, '' FROM releases WHERE full_text != ''
                ORDER BY COALESCE(NULLIF(posted_at, 'unknown'), fetched_at) DESC LIMIT 30""").fetchall()
        rows = [r for r in rows if r[0] not in seen]
        cached = {p for (p,) in conn.execute("SELECT prid FROM summaries WHERE lang = ?", (lang,))}
        order = sorted(rows[:5], key=lambda r: r[0] not in cached) + rows[5:]
        for prid, title, link, _ in order[:tries]:
            s = cached_summary(conn, prid, lang)      # cache, warna AI + verify
            if s:
                try:                                  # title bhi user ki bhasha mein (cache, warna 1 AI call)
                    title = translated_titles([(prid, title)], lang).get(prid, title)
                except Exception as err:
                    print("  title translate skip:", err)
                return (prid, title, link, s), skipped
            skipped.append(prid)
        return None, skipped
    finally:
        conn.close()


# ---------- Khabar bhejna ----------
async def send_news(context, chat_id, uid):
    row = get_user(uid)
    role, lang = ((row[0] or "sabhi"), (row[1] or "hi")) if row else ("sabhi", "hi")
    seen = context.user_data.setdefault("seen", [])

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    wait = await context.bot.send_message(chat_id, t(lang, "preparing"))
    found, skipped = await asyncio.to_thread(pick_next, role, lang, set(seen))
    seen.extend(skipped)
    try:
        await wait.delete()
    except Exception:
        pass

    if not found:
        context.user_data["seen"] = []                # agli baar shuru se
        await context.bot.send_message(chat_id, t(lang, "no_more"), reply_markup=main_menu(lang))
        return
    prid, title, link, s = found
    seen.append(prid)
    context.user_data["last_prid"] = prid

    await context.bot.send_message(chat_id, card(title, link, s, lang), parse_mode=ParseMode.HTML,
                                   disable_web_page_preview=True,
                                   reply_markup=news_keyboard(prid, title, s, lang, context.bot.username))
    await asyncio.to_thread(mark_sent, uid, prid)   # alert mein dobara na aaye; sawaal isi pe

    if ALL_LANGS.get(lang, {}).get("voice"):
        g = row[3] if row else "f"
        path = voice_file(prid, lang, g)
        await context.bot.send_chat_action(chat_id, ChatAction.RECORD_VOICE)
        ok = os.path.exists(path) or await asyncio.to_thread(text_to_speech, voice_script(s, lang), lang, path, g)
        if ok:
            await send_clip(context.bot, chat_id, path, title[:60])


# ---------- Sawaal -> jawab (likh ke ya bol ke) ----------
async def answer(update, context, question, lang, by_voice=False):
    uid = update.effective_user.id
    prid = context.user_data.get("last_prid") or await asyncio.to_thread(last_sent_prid, uid)
    if not prid:
        await update.message.reply_text(t(lang, "need_news"), reply_markup=main_menu(lang))
        return
    await update.message.reply_text(t(lang, "thinking"))
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    res = await asyncio.to_thread(answer_question, prid, question, lang)

    e = html.escape
    if res.get("ok"):
        src = "\n".join(f"<i>¶{n}: {e(p[:200])}…</i>" for n, p in res["paras"])
        await update.message.reply_text(f"💬 {e(res['answer'])}\n\n{e(t(lang, 'source'))}\n{src}",
                                        parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        if by_voice and ALL_LANGS.get(lang, {}).get("voice"):      # bol ke poochha -> jawab bhi awaaz mein
            path = os.path.join(tempfile.gettempdir(), f"ans_{uid}_{int(time.time())}.wav")
            if await asyncio.to_thread(text_to_speech, res["answer"], lang, path, voice_of(uid)):
                await send_clip(context.bot, update.effective_chat.id, path, "💬")
                try:
                    os.remove(path)
                except OSError:
                    pass
    else:
        await update.message.reply_text(t(lang, "qa_" + res.get("reason", "busy")))


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = lang_of(uid)
    media = update.message.voice or update.message.audio
    if media.duration and media.duration > 60:
        await update.message.reply_text(t(lang, "too_long"))
        return
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    path = os.path.join(tempfile.gettempdir(), f"q_{uid}_{media.file_unique_id}.ogg")
    await (await media.get_file()).download_to_drive(path)
    text = await asyncio.to_thread(transcribe, path, lang)
    try:
        os.remove(path)
    except OSError:
        pass
    if not text:
        await update.message.reply_text(t(lang, "not_heard"))
        return
    await update.message.reply_text(f"{t(lang, 'heard')} <i>{html.escape(text)}</i>", parse_mode=ParseMode.HTML)
    if len(text) < 25 and any(w in text.lower() for w in ("खबर", "ख़बर", "समाचार", "khabar", "news")):
        await send_news(context, update.effective_chat.id, uid)      # "aaj ki khabar sunao"
        return
    await answer(update, context, text, lang, by_voice=True)


# ---------- Onboarding: pehle bhasha (taaki agla sawaal apni bhasha mein ho), phir role. Bas 2 tap. ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    rem = parse_deeplink(context.args)                # website ka "Telegram pe yaad dilao" link
    if rem:
        when = add_reminder(uid, *rem)
        lang = lang_of(uid)
        await update.message.reply_text(t(lang, "remind_ok", when=f"{when:%d %b}"), reply_markup=main_menu(lang))
        return
    await update.message.reply_text(t("hi", "choose_lang"), reply_markup=grid("lang", LANGS, cols=3))


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row or not row[1]:
        await start(update, context)
        return
    role, lang, digest_on, g = row
    text = (f"<b>{t(lang, 'settings')}</b>\n\n"
            f"🌐 {t(lang, 'lang')}: {html.escape(label_of(LANGS, lang))}\n"
            f"👤 {t(lang, 'role')}: {html.escape(label_of(ROLES, role))}\n"
            f"🌅 {t(lang, 'digest')}: {t(lang, 'on' if digest_on else 'off')}\n"
            f"🗣️ {t(lang, 'voice')}: {t(lang, 'male' if g == 'm' else 'female')}")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(t(lang, "set_lang"), callback_data="set:lang"),
                                InlineKeyboardButton(t(lang, "set_role"), callback_data="set:role")],
                               [InlineKeyboardButton(t(lang, "set_voice"), callback_data="set:voice"),
                                InlineKeyboardButton(t(lang, "set_digest"), callback_data="set:digest")]])
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def digest_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    row = get_user(uid)
    if not row or not row[1]:
        await start(update, context)
        return
    role, lang, _, g = row
    await update.message.reply_text(t(lang, "preparing"))
    day = datetime.now(IST).strftime("%Y-%m-%d")
    if not await send_digest(context.bot, [(uid, lang, role, g)], day, force=True):
        await update.message.reply_text(t(lang, "no_more"), reply_markup=main_menu(lang))


async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not get_user(uid):
        await start(update, context)
        return
    await send_news(context, update.effective_chat.id, uid)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    prefix, value = q.data.split(":", 1)
    uid = q.from_user.id
    lang = lang_of(uid)

    if prefix == "rem":                               # "rem:<prid>:<yyyy-mm-dd>"
        prid, due = value.split(":", 1)
        when = add_reminder(uid, prid, due)
        await q.message.reply_text(t(lang, "remind_ok", when=f"{when:%d %b}"))
    elif prefix == "next":
        await send_news(context, q.message.chat_id, uid)
    elif prefix == "lang":
        had_role = (get_user(uid) or (None,))[0]
        save_field(uid, "lang", value)
        await q.edit_message_text(f"🌐 {label_of(LANGS, value)} ✓")
        if had_role:                                  # sirf bhasha badli
            await q.message.reply_text(t(value, "saved"), reply_markup=main_menu(value))
        else:
            await q.message.reply_text(t(value, "role_q"), reply_markup=grid("role", ROLES))
    elif prefix == "role":
        had_role = (get_user(uid) or (None,))[0]
        save_field(uid, "role", value)
        await q.edit_message_text(f"👤 {label_of(ROLES, value)} ✓")
        if had_role:
            await q.message.reply_text(t(lang, "saved"), reply_markup=main_menu(lang))
        else:                                         # naya user: menu + turant pehli khabar
            await q.message.reply_text(t(lang, "done"), reply_markup=main_menu(lang))
            await send_news(context, q.message.chat_id, uid)
    elif prefix == "set":
        if value == "lang":
            await q.message.reply_text(t(lang, "choose_lang"), reply_markup=grid("lang", LANGS, cols=3))
        elif value == "role":
            await q.message.reply_text(t(lang, "role_q"), reply_markup=grid("role", ROLES))
        elif value == "digest":
            toggle_digest(uid)
            await settings(update, context)
        elif value == "voice":                        # 👩 <-> 👨, aur ek chhota sample sunao
            toggle_voice(uid)
            await settings(update, context)
            g = voice_of(uid)
            sample = f"voice_sample_{lang}_{g}.wav"
            if ALL_LANGS.get(lang, {}).get("voice") and (os.path.exists(sample) or await asyncio.to_thread(
                    text_to_speech, t(lang, "voice_hello"), lang, sample, g)):
                await send_clip(context.bot, q.message.chat_id, sample, "🗣️")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu ke buttons emoji se pehchaano (har bhasha mein same); baaki sab = sawaal."""
    text = (update.message.text or "").strip()
    uid = update.effective_user.id
    lang = lang_of(uid)
    if text.startswith("📰"):
        await news_cmd(update, context)
    elif text.startswith("🌅"):
        await digest_now(update, context)
    elif text.startswith("🎙"):
        await update.message.reply_text(t(lang, "ask_hint"))
    elif text.startswith("⚙"):
        await settings(update, context)
    else:
        await answer(update, context, text, lang)


# ---------- Bot ka chehra: menu commands + description (Telegram app mein dikhta hai) ----------
async def post_init(app):
    try:
        await app.bot.set_my_commands([
            BotCommand("khabar", "📰 आज की खबर · Today's news"),
            BotCommand("subah", "🌅 3 बड़ी खबरें · Top 3 stories"),
            BotCommand("settings", "⚙️ भाषा, सेटिंग · Language, settings"),
            BotCommand("yaad", "⏰ मेरे रिमाइंडर · My reminders"),
            BotCommand("start", "🔄 शुरू से · Start over"),
        ])
        await app.bot.set_my_short_description(
            "सरकारी खबरें आपकी भाषा में, आवाज़ में, हर तथ्य जाँचा हुआ। "
            "Govt news in your language, by voice, fact-checked.")
        await app.bot.set_my_description(
            "📰 PIB की सरकारी खबरें आसान भाषा में, 11 भाषाओं में आवाज़ के साथ।\n"
            "✓ हर नंबर और तारीख मूल खबर से जाँची जाती है।\n"
            "🎙️ बोलकर सवाल पूछिए, जवाब आवाज़ में।\n"
            "🌅 हर सुबह 8 बजे 3 बड़ी खबरें।\n\nStart दबाइए 👇")
        print("Bot menu + description set")
    except Exception as err:
        print("Bot menu set nahi hua:", err)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN set nahi hai.")
        return
    setup_db()
    app = ApplicationBuilder().token(token).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("khabar", news_cmd))
    app.add_handler(CommandHandler(["settings", "me", "bhasha"], settings))
    app.add_handler(CallbackQueryHandler(on_button))
    register_alerts(app, card)                        # alerts mein bhi naya card
    register_reminders(app)
    register_digest(app)                              # /subah
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    print("Bot chal raha hai... band karne ke liye Ctrl+C")
    app.run_polling()


if __name__ == "__main__":
    main()
