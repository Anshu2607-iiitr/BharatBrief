# Lesson 4: Summary - Gemini pehle, busy ho to Groq (fallback), JSON safe parsing

import json
import os
import re
import sqlite3
import sys
import time

import requests
from google import genai
from groq_pick import pick_groq_model

DB_FILE = "practice.db"
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
GROQ_MODEL = os.environ.get("GROQ_MODEL") or pick_groq_model()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
RETRY_CODES = ("503", "429", "504", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE_EXCEEDED")
LAST_PROVIDER = ""

LANGUAGES = {
    "hi": "Hindi", "en": "English", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu", "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada",
    "ml": "Malayalam", "or": "Odia", "pa": "Punjabi",
}

from languages import ALL as _ALL_LANGS
LANGUAGES.update({c: v["en"] for c, v in _ALL_LANGS.items()})   # saari 23 bhashayein

PROMPT = """You explain Indian government press releases to ordinary citizens.
Write the summary in very simple {language}, the way you would explain it to a
person in a village. Use the native script of {language}.

Rules:
- Use ONLY facts from the press release below. Never add any number, date or name.
- Write every number with digits 0-9, even inside {language} text.
- A year alone (like 2047 or 2014) is a NUMBER, not a date. Put it in sankhya, never in tareekh_iso.
- Only put a date in tareekh_iso if the press release gives a day and a month.
- Each field: 1-2 short sentences.
- If something is not in the text, write that it is not mentioned, in {language}.

Reply ONLY with a JSON object in this format (keep the keys in English), no other text:
{{
  "kiske_liye": "kisan | student | msme | mahila | sabhi",
  "prakar": "nayi scheme | deadline | niyam badla | ghoshna | anya",
  "kya_hua": "...",
  "aap_pe_asar": "...",
  "kya_karna_hai": "...",
  "tareekh_iso": ["every date you used, written as YYYY-MM-DD"],
  "sankhya": ["every other number you used, digits only"]
}}

PRESS RELEASE:
"""


def get_release(prid):
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute(
        "SELECT prid, title, full_text FROM releases WHERE prid = ?", (prid,)
    ).fetchone()
    conn.close()
    return row


def parse_json(raw):
    """Text se JSON nikalo, chahe aage-peeche kuch extra likha ho."""
    if not raw:
        return None
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)   # pehle { se aakhri } tak
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


# ---------- Provider 1: Gemini - kai models, har model ka quota alag ----------
# Pehla wala sabse achha; quota khatam to agla. Env GEMINI_FALLBACKS="a,b,c" se badal sakte ho.
GEMINI_FALLBACKS = [m.strip() for m in os.environ.get(
    "GEMINI_FALLBACKS",
    "gemini-3.6-flash,gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemma-4-26b-a4b-it",
).split(",") if m.strip()]
_gemini_resting = {}        # model -> kab tak mat poochho


def _gemini_models():
    return list(dict.fromkeys([m for m in [GEMINI_MODEL] + GEMINI_FALLBACKS if m]))


def _gemini_once(client, model, contents, tries=3):
    """Ek model: busy (503) pe thoda ruk ke retry. Return (text, 'ok'|'quota'|'gone'|'fail')."""
    wait = 2
    for attempt in range(1, tries + 1):
        try:
            cfg = {} if model.startswith("gemma") else {"response_mime_type": "application/json"}
            resp = client.models.generate_content(model=model, contents=contents, config=cfg)
            return resp.text, "ok"
        except Exception as err:
            msg = str(err)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                return None, "quota"
            if "404" in msg or "NOT_FOUND" in msg:
                return None, "gone"
            if any(code in msg for code in RETRY_CODES) and attempt < tries:
                print(f"  Gemini {model} busy, {wait}s baad dobara ({attempt}/{tries})")
                time.sleep(wait)
                wait *= 2
                continue
            print(f"  Gemini {model} fail:", msg[:120])
            return None, "fail"
    return None, "fail"


def call_gemini(contents, tries=3):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("  GEMINI_API_KEY set nahi hai")
        return None
    client = genai.Client(api_key=api_key, http_options={"timeout": 60000})
    for model in _gemini_models():
        if _gemini_resting.get(model, 0) > time.time():
            continue
        text, status = _gemini_once(client, model, contents, tries)
        if status == "ok":
            global LAST_PROVIDER_MODEL
            LAST_PROVIDER_MODEL = model
            return text
        if status == "quota":
            _gemini_resting[model] = time.time() + 30 * 60      # 30 min baad phir dekhenge
            print(f"  Gemini {model}: quota khatam, agla model")
        elif status == "gone":
            _gemini_resting[model] = time.time() + 24 * 3600    # model hi nahi hai
    return None


# ---------- Provider 2: Groq (backup) - kai models, ek ka quota khatam to agla ----------
LAST_PROVIDER_MODEL = ""
GROQ_FALLBACKS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
_groq_resting = {}          # model -> kab tak mat poochho (time.time())


def _groq_models():
    models = [m for m in [GROQ_MODEL] + GROQ_FALLBACKS if m]
    return list(dict.fromkeys(models))           # duplicate hatao, order wahi


def _wait_seconds(text):
    """'try again in 8m44.01s' -> 524 second. Na mile to 1 ghanta."""
    m = re.search(r"try again in (?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?", text)
    if not m or not any(m.groups()):
        return 3600
    h, mi, sec = (float(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + sec


def _groq_once(model, contents, api_key, json_mode):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": contents + "\n\n/no_think"}],
        "temperature": 0.2,
        "max_tokens": 800,
    }
    if "gpt-oss" in model:                       # reasoning model: kam sochna, zyada jagah jawab ke liye
        body["reasoning_effort"] = "low"
        body["max_tokens"] = 2000
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    return requests.post(GROQ_URL, json=body, timeout=60, headers={"Authorization": f"Bearer {api_key}"})


def call_groq(contents, json_mode=True):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("  GROQ_API_KEY set nahi hai, backup nahi chal sakta")
        return None
    for model in _groq_models():
        if _groq_resting.get(model, 0) > time.time():
            continue                             # is model ka quota abhi khatam, agla
        try:
            resp = _groq_once(model, contents, api_key, json_mode)
            if resp.status_code == 400 and "json_validate_failed" in resp.text and json_mode:
                resp = _groq_once(model, contents, api_key, False)
        except requests.RequestException as err:
            print(f"  Groq ({model}) network problem:", err)
            continue
        if resp.status_code == 200:
            global LAST_PROVIDER_MODEL
            LAST_PROVIDER_MODEL = model
            return resp.json()["choices"][0]["message"]["content"]
        if resp.status_code == 429:
            wait = _wait_seconds(resp.text)
            per_day = "per day" in resp.text or "TPD" in resp.text or "RPD" in resp.text
            _groq_resting[model] = time.time() + (wait if per_day else min(wait, 60))
            print(f"  Groq {model}: limit ({'aaj ka' if per_day else 'is minute ka'}), {int(wait)}s aaraam, agla model")
            continue
        print(f"  Groq {model} error:", resp.status_code, resp.text[:200])
    return None




def summarize(title, text, lang_code):
    language = LANGUAGES.get(lang_code)
    if not language:
        print("Ye bhasha abhi supported nahi:", lang_code)
        return None

    contents = PROMPT.format(language=language) + "Title: " + title + "\n\n" + text

    for provider, call in (("Gemini", call_gemini), ("Groq", call_groq)):
        raw = call(contents)
        summary = parse_json(raw)
        if summary:
            global LAST_PROVIDER
            LAST_PROVIDER = provider
            print(f"  Summary {provider} se bani")
            return summary
        if raw:
            print(f"  {provider} ka jawab JSON nahi tha:", raw[:200])
        if provider == "Gemini":
            print("  Gemini nahi chala, backup Groq try kar rahe hain...")

    print("Dono providers fail. Summary nahi bani.")
    return None


def main():
    lang_code = sys.argv[1] if len(sys.argv) > 1 else "hi"
    row = get_release("2330875")
    if not row:
        print("Release DB mein nahi mili. Pehle collector.py chalao.")
        return
    prid, title, text = row
    print("PRID:", prid, "| Bhasha:", LANGUAGES.get(lang_code, lang_code))
    print("-" * 50)
    summary = summarize(title, text, lang_code)
    if summary:
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
