# Bot ki baatein baaki bhashaon mein: AI translate karta hai, hum check karte hain, JSON mein save.
# Chalana:  python make_bot_text.py bn ta te mr gu kn ml or pa
# Check: button ka emoji wahi rahe (bot emoji se button pehchanta hai), {d}/{when} jaise khaane na tootein.

import json
import os
import re
import sys
import time

from bot_text import T
from languages import ALL
from summarize import call_gemini, call_groq, parse_json

OUT = "bot_text_auto.json"
PROMPT = """Translate the VALUES of this JSON into simple, warm, spoken {language} (native script), for rural users.
Rules: keep every emoji exactly as is and in the same position; keep placeholders like {{d}} and {{when}} unchanged;
keep "/yaad", "PIB", "WhatsApp" unchanged; keep line breaks (\\n). Do not translate the keys.
Reply ONLY with the JSON object.

{payload}"""


# Har bhasha ki lipi (Unicode range). AI kabhi-kabhi doosri lipi ke akshar mila deta hai.
SCRIPT = {"hi": (0x0900, 0x097F), "mr": (0x0900, 0x097F), "bn": (0x0980, 0x09FF), "pa": (0x0A00, 0x0A7F),
          "gu": (0x0A80, 0x0AFF), "or": (0x0B00, 0x0B7F), "ta": (0x0B80, 0x0BFF), "te": (0x0C00, 0x0C7F),
          "kn": (0x0C80, 0x0CFF), "ml": (0x0D00, 0x0D7F)}


def same_script(lang, text):
    if lang not in SCRIPT:
        return True
    lo, hi = SCRIPT[lang]
    return all(c.isascii() or not c.isalpha() or lo <= ord(c) <= hi for c in text)


def ok(en, tr, lang=None):
    if not same_script(lang, tr):
        return False                                          # doosri lipi ke akshar mile
    lead = re.match(r"^\W+", en)
    if lead and not tr.startswith(lead.group(0).strip()):
        return False                                          # button emoji badal gaya
    return set(re.findall(r"\{\w+\}", en)) == set(re.findall(r"\{\w+\}", tr))


def main(langs):
    out = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    en = T["en"]
    for lang in langs:
        language = ALL.get(lang, {}).get("en")
        if not language:
            print(lang, ": bhasha nahi pata")
            continue
        todo = {k: v for k, v in en.items() if k not in out.get(lang, {})}   # sirf jo missing hain
        if not todo:
            print(lang, ": sab pehle se theek")
            continue
        payload = json.dumps(todo, ensure_ascii=False, indent=1)
        res = None
        for call in (call_gemini, call_groq):
            res = parse_json(call(PROMPT.format(language=language, payload=payload)))
            if isinstance(res, dict) and res:
                break
        if not isinstance(res, dict):
            print(lang, ": AI se nahi bana")
            continue
        good = {k: v for k, v in res.items() if k in todo and isinstance(v, str) and ok(en[k], v, lang)}
        out.setdefault(lang, {}).update(good)
        bad = sorted(set(todo) - set(good))
        print(f"{lang}: {len(good)}/{len(todo)} naye theek" + (f", English rahega: {bad}" if bad else ""))
        json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(4)


if __name__ == "__main__":
    main(sys.argv[1:] or ["bn", "ta", "te", "mr", "gu", "kn", "ml", "or", "pa"])
