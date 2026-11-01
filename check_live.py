# Live deployment check: judges ke kholne se pehle ek command mein sab dekh lo.
# Kuch badalta nahi, sirf dekhta hai.   Chalana:  python check_live.py

import os
import subprocess
import time

import requests

SITE = os.environ.get("LIVE_URL", "https://bharatbrief-j3e3.onrender.com")
results = []


def check(name, fn):
    t = time.time()
    try:
        ok, note = fn()
    except Exception as err:
        ok, note = False, str(err)[:120]
    results.append(ok)
    print(f"{'✅' if ok else '❌'} {name:<26} {note}  ({time.time() - t:.1f}s)")


def website():
    r = requests.get(SITE + "/_stcore/health", timeout=90)       # so raha ho to jagne mein 1 min
    return r.text.strip() == "ok", f"{SITE} -> {r.text.strip()[:30]}"


def bot():
    tok = os.environ.get("TELEGRAM_BOT_TOKEN") or ""
    me = requests.get(f"https://api.telegram.org/bot{tok}/getMe", timeout=15).json()
    if not me.get("ok"):
        return False, "token galat ya bot band"
    info = requests.get(f"https://api.telegram.org/bot{tok}/getWebhookInfo", timeout=15).json()["result"]
    pending = info.get("pending_update_count", 0)
    # Render ka bot chal raha hai to messages turant uthata hai: pending 0 rehna chahiye
    return pending == 0, f"@{me['result']['username']}, bina jawab ke messages: {pending}"


def sarvam():
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        return False, "key nahi (laptop pe)"
    r = requests.post("https://api.sarvam.ai/text-to-speech", timeout=30, headers={"api-subscription-key": key},
                      json={"text": "ok", "target_language_code": "hi-IN", "model": "bulbul:v3"})
    if r.status_code == 402:
        return False, "credits khatam (backup Edge awaaz chalegi)"
    return r.status_code == 200, f"HTTP {r.status_code}"


def edge_voice():
    import asyncio
    import edge_tts
    path = "_check_voice.mp3"
    asyncio.run(edge_tts.Communicate("नमस्ते", "hi-IN-SwaraNeural").save(path))
    size = os.path.getsize(path)
    os.remove(path)
    return size > 1000, "backup awaaz ban rahi hai"


def ai():
    from summarize import call_gemini, call_groq
    for name, fn in (("Gemini", call_gemini), ("Groq", call_groq)):
        if fn('Reply only JSON: {"ok": true}'):
            return True, f"{name} jawab de raha hai"
    return False, "Gemini aur Groq dono ka quota khatam"


def git_pushed():
    head = subprocess.run(["git", "status", "-sb"], capture_output=True, text=True).stdout.splitlines()[0]
    changed = [l[3:] for l in subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout.splitlines()
               if l.startswith(" M") or l.startswith("M ")]
    if "ahead" in head:
        return False, "commit hai par push nahi hua: git push"
    if changed:
        return False, "badli hui files live pe nahi: " + ", ".join(changed[:6])
    return True, "live code = laptop ka code"


if __name__ == "__main__":
    print(f"BharatBrief live check · {time.strftime('%d %b %H:%M')}\n")
    check("Website", website)
    check("Telegram bot (Render)", bot)
    check("AI (summaries)", ai)
    check("Sarvam awaaz", sarvam)
    check("Backup awaaz (Edge)", edge_voice)
    check("Code GitHub pe push", git_pushed)
    print("\nSab theek ✅" if all(results) else "\nUpar ❌ wali line dekho")
