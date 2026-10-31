# Lesson 4: AI se user ki bhasha mein summary banwana

import json
import os
import sqlite3
import sys

from google import genai

DB_FILE = "practice.db"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

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

Reply ONLY in this JSON format (keep the keys in English):
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


def summarize(title, text, lang_code):
    language = LANGUAGES.get(lang_code)
    if not language:
        print("Ye bhasha abhi supported nahi:", lang_code)
        return None

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY set nahi hai.")
        return None

    client = genai.Client(api_key=api_key)
    prompt = PROMPT.format(language=language)
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt + "Title: " + title + "\n\n" + text,
            config={"response_mime_type": "application/json"},
        )
    except Exception as err:
        print("AI call fail hua:", err)
        return None

    try:
        return json.loads(resp.text)
    except json.JSONDecodeError:
        print("AI ne sahi JSON nahi diya. Jo aaya:")
        print(resp.text[:500])
        return None


def main():
    # Chalane ka tareeka: python summarize.py ta   (ta = Tamil)
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
