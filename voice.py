# Lesson 7: Verified summary ko Sarvam TTS se voice note banana

import base64
import os
import sys

import requests

from summarize import get_release, summarize
import summarize as summarize_mod
from trace_log import log_event
from verify import facts_from_original, check

SARVAM_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_MODEL = os.environ.get("SARVAM_TTS_MODEL", "bulbul:v3")

# Do awaazein: user Setting mein chunta hai. Env se badal sakte ho (Sarvam ke 37 speakers mein se koi bhi).
VOICES = {"f": os.environ.get("SARVAM_FEMALE", "priya"), "m": os.environ.get("SARVAM_MALE", "rahul")}


def voice_file(prid, lang, gender="f"):
    """Har khabar + bhasha + awaaz ki alag file (cache)."""
    return f"khabar_{prid}_{lang}_{gender if gender in VOICES else 'f'}.wav"


# Hamare code -> Sarvam ka language code
LANG_CODES = {
    "hi": "hi-IN", "en": "en-IN", "bn": "bn-IN", "ta": "ta-IN", "te": "te-IN",
    "mr": "mr-IN", "gu": "gu-IN", "kn": "kn-IN", "ml": "ml-IN",
    "or": "od-IN", "pa": "pa-IN",
}

# AI awaaz ka label (naye IT Rules ke hisaab se AI content batana chahiye)
AI_LABEL = {
    "hi": "Ye awaaz AI se bani hai.",
    "en": "This voice is AI generated.",
}


def verified_summary(prid, lang):
    """Summary banao aur verify karo. Do baar fail ho to None."""
    row = get_release(prid)
    if not row:
        print("Release DB mein nahi mili.")
        return None
    _, title, text = row
    dates, numbers = facts_from_original(text)
    try:                                   # release ki posted date bhi valid tareekh hai
        import sqlite3
        _c = sqlite3.connect("practice.db")
        _r = _c.execute("SELECT posted_at FROM releases WHERE prid = ?", (prid,)).fetchone()
        _c.close()
        if _r and _r[0] and _r[0] != "unknown":
            dates.add(_r[0][:10])
            dates.add(_r[0][5:10])
    except Exception:
        pass

    feedback = ""
    for attempt in (1, 2):
        summary = summarize(title, text[:2000] + feedback, lang)   # chhota input = kam tokens
        if not summary:
            log_event(prid, "summary", "fail", f"{lang}: Gemini aur Groq dono fail")
            return None
        problems = check(summary, dates, numbers)
        if not problems:
            log_event(prid, "verify", "ok", f"{lang} · koshish {attempt} · {summarize_mod.LAST_PROVIDER}")
            print(f"Summary verified (koshish {attempt})")
            return summary
        log_event(prid, "verify", "fail", f"{lang} · koshish {attempt}: " + "; ".join(problems))
        print(f"Koshish {attempt} fail:", problems)
        feedback = ("\n\nIMPORTANT: Your previous summary had these errors: "
                    + "; ".join(problems)
                    + ". Rewrite it using ONLY facts from the press release.")
    return None


def voice_script(summary, lang):
    """Summary ke hisson ko ek bolne layak paragraph mein jodo."""
    parts = [
        AI_LABEL.get(lang, AI_LABEL["en"]),
        summary.get("kya_hua", ""),
        summary.get("aap_pe_asar", ""),
        summary.get("kya_karna_hai", ""),
    ]
    return " ".join(p for p in parts if p)


def text_to_speech(text, lang, out_path, gender="f"):
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        print("SARVAM_API_KEY set nahi hai.")
        return False
    if lang not in LANG_CODES:
        print("Is bhasha ki awaaz abhi nahi:", lang)
        return False

    body = {
        "text": text[:1500],                     # bahut lamba text na bhejein
        "target_language_code": LANG_CODES[lang],
        "model": SARVAM_MODEL,
        "speaker": VOICES.get(gender, VOICES["f"]),
    }
    try:
        resp = requests.post(SARVAM_URL, json=body,
                             headers={"api-subscription-key": key}, timeout=60)
    except requests.RequestException as err:
        print("Network problem:", err)
        return False

    if resp.status_code != 200:
        print("Sarvam error:", resp.status_code)
        print(resp.text[:400])                   # error message se pata chalega kya badalna hai
        return False

    audios = resp.json().get("audios") or []
    if not audios:
        print("Audio nahi aaya. Jawab:", resp.text[:400])
        return False

    with open(out_path, "wb") as f:
        f.write(base64.b64decode(audios[0]))     # Sarvam audio ko base64 text mein bhejta hai
    return True


def main():
    lang = sys.argv[1] if len(sys.argv) > 1 else "hi"

    summary = verified_summary("2330875", lang)
    if not summary:
        print("Verified summary nahi bani, isliye voice nahi banegi.")
        return

    script = voice_script(summary, lang)
    print("Bolne wala text:")
    print(script)
    print("-" * 50)

    out_path = f"khabar_{lang}.wav"
    if text_to_speech(script, lang, out_path):
        print("Voice note save hua:", out_path)


if __name__ == "__main__":
    main()
