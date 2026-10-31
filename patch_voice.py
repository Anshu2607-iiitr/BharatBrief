# Ek baar chalane wali script: bot.py aur alerts.py mein send_clip lagana

CHANGES = {
    "alerts.py": [
        ("from voice import text_to_speech, verified_summary, voice_script\n",
         "from voice import text_to_speech, verified_summary, voice_script\nfrom audio_util import send_clip\n"),
        ('            if d["audio"]:\n'
         '                with open(d["audio"], "rb") as f:\n'
         '                    await bot.send_audio(d["uid"], f, title="Nayi khabar (AI awaaz)")\n',
         '            if d["audio"]:\n'
         '                await send_clip(bot, d["uid"], d["audio"], "Nayi khabar (AI awaaz)")\n'),
    ],
    "bot.py": [
        ("from alerts import register_alerts\n",
         "from alerts import register_alerts\nfrom audio_util import send_clip\n"),
        ('    with open(audio_path, "rb") as f:\n'
         '        await update.message.reply_audio(f, title="Khabar (AI awaaz)")\n',
         '    await send_clip(context.bot, update.effective_chat.id, audio_path, "Khabar (AI awaaz)")\n'),
    ],
}

for filename, pairs in CHANGES.items():
    with open(filename, encoding="utf-8-sig") as f:
        code = f.read()
    ok = True
    for old, new in pairs:
        if new in code:
            print(f"{filename}: pehle se badla hua hai, skip")
            continue
        if code.count(old) != 1:
            print(f"{filename}: ye hissa nahi mila, kuch nahi badla ->", old.strip()[:60])
            ok = False
            break
        code = code.replace(old, new)
    if ok:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"{filename}: update ho gaya")
