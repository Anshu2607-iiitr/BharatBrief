# Titles ka translation: ek AI call mein 10 titles, DB mein cache, numbers check

import re
import sqlite3
import time

from summarize import LANGUAGES, call_gemini, call_groq, parse_json

DB_FILE = "practice.db"
BATCH = 10
_last_fail = {}            # bhasha -> kab fail hua (taaki har refresh pe quota na jale)

PROMPT = """Translate these Indian government news headlines into simple, natural {language} (native script).
Keep every number as digits 0-9, exactly as in the original. Do not add anything.
Reply ONLY with JSON: {{"titles": {{"<id>": "<translated headline>"}}}}

HEADLINES:
{items}
"""


def _conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("CREATE TABLE IF NOT EXISTS title_tr (prid TEXT, lang TEXT, title TEXT, PRIMARY KEY (prid, lang))")
    return conn


def _digits(s):
    return set(re.findall(r"\d+", re.sub(r"(?<=\d),(?=\d)", "", s or "")))


def translated_titles(rows, lang):
    """{prid: translated title}. Hindi ke liye kuch nahi (original hi Hindi hai)."""
    if lang == "hi":
        return {}
    conn = _conn()
    have = {p: t for p, t in conn.execute("SELECT prid, title FROM title_tr WHERE lang = ?", (lang,))}
    missing = [(r[0], r[1]) for r in rows if r[0] not in have][:BATCH]

    if missing and time.time() - _last_fail.get(lang, 0) > 300:
        items = "\n".join(f"{p}: {t}" for p, t in missing)
        contents = PROMPT.format(language=LANGUAGES.get(lang, "English"), items=items)
        res = None
        for call in (call_gemini, call_groq):
            res = parse_json(call(contents))
            if res:
                break
        got = res.get("titles", {}) if isinstance(res, dict) else {}
        if not got:
            _last_fail[lang] = time.time()          # 5 minute tak dobara mat poocho
        original = dict(missing)
        for p, t in got.items():
            p = str(p)
            if p in original and isinstance(t, str) and t.strip() and _digits(t) <= _digits(original[p]):
                conn.execute("INSERT OR REPLACE INTO title_tr VALUES (?, ?, ?)", (p, lang, t.strip()))
                have[p] = t.strip()
        conn.commit()
    conn.close()
    return have
