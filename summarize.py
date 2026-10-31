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

PROMPT = """You explain Indian government press releases to ordinary citizens.
Write the summary in very simple {language}, the way you would explain it to a
person in a village. Use the native script of {language}.

Rules:
- Use ONLY facts from the press release below. Never add any number, date or name.
- Write every number with digits 0-9, even inside {language} text.
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


# ---------- Provider 1: Gemini ----------
def call_gemini(contents, tries=3):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("  GEMINI_API_KEY set nahi hai")
        return None
    client = genai.Client(api_key=api_key, http_options={"timeout": 60000})

    wait = 2
    for attempt in range(1, tries + 1):
        try:
            resp = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config={"response_mime_type": "application/json"},
            )
            return resp.text
        except Exception as err:
            busy = any(code in str(err) for code in RETRY_CODES)
            if busy and attempt < tries:
                print(f"  Gemini busy hai, {wait}s baad dobara try ({attempt}/{tries})")
                time.sleep(wait)
                wait *= 2
                continue
            print("  Gemini fail:", str(err)[:200])
            return None


# ---------- Provider 2: Groq (backup) ----------
def call_groq(contents, json_mode=True):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or not GROQ_MODEL:
        print("  GROQ_API_KEY ya GROQ_MODEL set nahi hai, backup nahi chal sakta")
        return None
    body = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": contents}],
        "temperature": 0.2,
        "max_tokens": 800,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        resp = requests.post(GROQ_URL, json=body, timeout=60,
                             headers={"Authorization": f"Bearer {api_key}"})
    except requests.RequestException as err:
        print("  Groq network problem:", err)
        return None

    if resp.status_code == 400 and "json_validate_failed" in resp.text and json_mode:
        print("  Groq JSON mode fail, bina JSON mode ke dobara try...")
        return call_groq(contents, json_mode=False)
    if resp.status_code != 200:
        print("  Groq error:", resp.status_code, resp.text[:300])
        return None
    return resp.json()["choices"][0]["message"]["content"]


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
