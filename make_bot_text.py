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


def ok(en, tr):
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
        payload = json.dumps(en, ensure_ascii=False, indent=1)
        res = None
        for call in (call_gemini, call_groq):
            res = parse_json(call(PROMPT.format(language=language, payload=payload)))
            if isinstance(res, dict) and res:
                break
        if not isinstance(res, dict):
            print(lang, ": AI se nahi bana")
            continue
        good = {k: v for k, v in res.items() if k in en and isinstance(v, str) and ok(en[k], v)}
        bad = sorted(set(en) - set(good))
        out[lang] = good
        print(f"{lang}: {len(good)}/{len(en)} theek" + (f", English rahega: {bad}" if bad else ""))
        json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(4)


if __name__ == "__main__":
    main(sys.argv[1:] or ["bn", "ta", "te", "mr", "gu", "kn", "ml", "or", "pa"])
