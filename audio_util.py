# Lesson 11: WAV -> OGG/Opus (Telegram voice bubble), ffmpeg na ho to WAV hi bhejo

import asyncio
import os
import shutil
import subprocess


def to_ogg(wav_path):
    """WAV ko OGG/Opus mein badlo. Na ho paaye to None (WAV se kaam chalayenge)."""
    if not shutil.which("ffmpeg"):
        print("  ffmpeg nahi mila, WAV hi bhejenge")
        return None
    ogg_path = os.path.splitext(wav_path)[0] + ".ogg"
    if os.path.exists(ogg_path):
        return ogg_path                          # pehle se bani hai, dobara mat banao
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path,
             "-c:a", "libopus", "-b:a", "32k", ogg_path],
            capture_output=True, timeout=60)
    except Exception as err:
        print("  ffmpeg chal nahi paaya:", err)
        return None
    if r.returncode != 0:
        print("  ffmpeg error:", r.stderr.decode(errors="ignore")[:200])
        return None
    return ogg_path


async def send_clip(bot, chat_id, wav_path, title):
    """Ho sake to voice bubble, warna audio file."""
    ogg_path = await asyncio.to_thread(to_ogg, wav_path)
    if ogg_path:
        with open(ogg_path, "rb") as f:
            await bot.send_voice(chat_id, f)
    else:
        with open(wav_path, "rb") as f:
            await bot.send_audio(chat_id, f, title=title)
