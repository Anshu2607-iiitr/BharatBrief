# Lesson 18: Khabar se sawaal-jawab (chhota RAG) - sirf release ke paragraphs se, source ke saath

import html
import re
import sqlite3

from summarize import LANGUAGES, call_gemini, call_groq, get_release, parse_json
from trace_log import log_event
from verify import facts_from_original

DB_FILE = "practice.db"

PROMPT = """You answer a citizen's question about ONE Indian government press release.
Answer in very simple {language} (native script), in 1-3 short sentences.

Rules:
- Use ONLY the numbered paragraphs below. Never use outside knowledge.
- Write numbers with digits 0-9.
- If the paragraphs do not contain the answer, set "found" to false.
- List the paragraph numbers you used.

Reply ONLY with JSON:
{{"found": true, "answer": "...", "paragraphs": [1, 2]}}

QUESTION: {question}

PARAGRAPHS:
{paragraphs}
"""


def split_paragraphs(text):
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def pick_relevant(paras, question, k=6):
    """Retrieval: jis paragraph mein sawaal ke zyada shabd hon, wo pehle. Pehla paragraph hamesha."""
    words = {w for w in re.split(r"[\s,.।?!:;\"'()\-]+", question.lower()) if len(w) > 1}
    scores = [(sum(1 for w in words if w in p.lower()), i) for i, p in enumerate(paras)]
    best = {i for _, i in sorted(scores, key=lambda x: (-x[0], x[1]))[:k]}
    best.add(0)
    return sorted(best)


def _ask_ai(contents):
    for call in (call_gemini, call_groq):
        res = parse_json(call(contents))
        if res:
            return res
    return None


def answer_question(prid, question, lang):
    row = get_release(prid)
    if not row:
        return {"ok": False, "reason": "notfound"}
    _, title, text = row
    paras = split_paragraphs(text)
    if not paras:
        return {"ok": False, "reason": "notfound"}

    idx = pick_relevant(paras, question)
    block = "\n\n".join(f"[{i + 1}] {paras[i][:600]}" for i in idx)
    language = LANGUAGES.get(lang, "Hindi")

    feedback = ""
    for attempt in (1, 2):
        contents = PROMPT.format(language=language, question=question[:300], paragraphs=block) + feedback
        res = _ask_ai(contents)
        if not res:
            log_event(prid, "qa", "fail", "AI busy")
            return {"ok": False, "reason": "busy"}
        if not res.get("found"):
            log_event(prid, "qa", "ok", f"{lang}: jawab khabar mein nahi")
            return {"ok": False, "reason": "notfound"}

        used = sorted({int(n) for n in res.get("paragraphs", [])
                       if str(n).isdigit() and 1 <= int(n) <= len(paras)})
        if not used:
            feedback = "\n\nIMPORTANT: You must list the paragraph numbers you used."
            continue

        _, numbers = facts_from_original(title + "\n" + "\n".join(paras[n - 1] for n in used))
        bad = [n for n in re.findall(r"\d+", str(res.get("answer", ""))) if n not in numbers]
        if not bad:
            log_event(prid, "qa", "ok", f"{lang}: paragraph {used}")
            return {"ok": True, "answer": str(res.get("answer", "")),
                    "paras": [(n, paras[n - 1]) for n in used]}

        log_event(prid, "qa", "fail", f"{lang}: numbers {bad} cited paragraphs mein nahi")
        feedback = (f"\n\nIMPORTANT: these numbers are not in the paragraphs you cited: "
                    f"{', '.join(bad)}. Answer again using only the paragraphs.")

    return {"ok": False, "reason": "verify"}


def last_sent_prid(telegram_id):
    """User ko aakhri baar kaunsi khabar gayi thi."""
    conn = sqlite3.connect(DB_FILE)
    try:
        row = conn.execute("SELECT prid FROM sent_log WHERE telegram_id = ? ORDER BY sent_at DESC LIMIT 1",
                           (telegram_id,)).fetchone()
    except sqlite3.OperationalError:
        row = None
    conn.close()
    return row[0] if row else None


def answer_text_telegram(res):
    e = html.escape
    if res.get("ok"):
        src = "\n".join(f"<i>¶{n}: {e(t[:200])}…</i>" for n, t in res["paras"])
        return f"{e(res['answer'])}\n\n📌 <b>Source</b> (original release):\n{src}"
    return {"notfound": "Is khabar mein iska jawab nahi hai.",
            "busy": "AI abhi vyast hai, thodi der baad poochiye.",
            "verify": "Pakka jawab nahi mila. Original khabar padhein."}.get(res.get("reason"), "Jawab nahi mil paaya.")
