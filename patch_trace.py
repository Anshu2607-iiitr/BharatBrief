# Ek baar chalane wali script: logging + PIB down toggle jodna

CHANGES = {
    "collector.py": [
        ("from bs4 import BeautifulSoup\n",
         "from bs4 import BeautifulSoup\n\nfrom trace_log import log_event, simulate_pib_down\n"),
        ("def fetch_feed():\n    resp = get(FEED_URL)\n",
         "def fetch_feed():\n"
         "    if simulate_pib_down():\n"
         "        print(\"PIB down (demo toggle) - purane data se kaam chalega\")\n"
         "        log_event(\"-\", \"fetch\", \"fail\", \"PIB down (demo toggle)\")\n"
         "        return []\n"
         "    resp = get(FEED_URL)\n"),
    ],
    "summarize.py": [
        ('RETRY_CODES = ("503", "429", "504", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE_EXCEEDED")\n',
         'RETRY_CODES = ("503", "429", "504", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE_EXCEEDED")\nLAST_PROVIDER = ""\n'),
        ('            print(f"  Summary {provider} se bani")\n',
         '            global LAST_PROVIDER\n'
         '            LAST_PROVIDER = provider\n'
         '            print(f"  Summary {provider} se bani")\n'),
    ],
    "voice.py": [
        ("from summarize import get_release, summarize\n",
         "from summarize import get_release, summarize\nimport summarize as summarize_mod\nfrom trace_log import log_event\n"),
        ("        summary = summarize(title, text + feedback, lang)\n        if not summary:\n            return None\n",
         "        summary = summarize(title, text + feedback, lang)\n"
         "        if not summary:\n"
         "            log_event(prid, \"summary\", \"fail\", f\"{lang}: Gemini aur Groq dono fail\")\n"
         "            return None\n"),
        ('            print(f"Summary verified (koshish {attempt})")\n',
         '            log_event(prid, "verify", "ok", f"{lang} · koshish {attempt} · {summarize_mod.LAST_PROVIDER}")\n'
         '            print(f"Summary verified (koshish {attempt})")\n'),
        ('        print(f"Koshish {attempt} fail:", problems)\n',
         '        log_event(prid, "verify", "fail", f"{lang} · koshish {attempt}: " + "; ".join(problems))\n'
         '        print(f"Koshish {attempt} fail:", problems)\n'),
    ],
    "alerts.py": [
        ("from voice import text_to_speech, verified_summary, voice_script\n",
         "from voice import text_to_speech, verified_summary, voice_script\nfrom trace_log import log_event\n"),
        ('    print(f"[alert] Nayi releases: {collect_new(conn)}")\n',
         '    new = collect_new(conn)\n'
         '    log_event("-", "fetch", "ok", f"{new} nayi releases")\n'
         '    print(f"[alert] Nayi releases: {new}")\n'),
        ('        print(f"[alert] {prid}: kiske_liye={audience}, users={len(users)}")\n',
         '        log_event(prid, "match", "ok", f"{audience} · {len(users)} users")\n'
         '        print(f"[alert] {prid}: kiske_liye={audience}, users={len(users)}")\n'),
        ('            mark_sent(d["uid"], d["prid"])\n',
         '            mark_sent(d["uid"], d["prid"])\n'
         '            log_event(d["prid"], "send", "ok", "voice + card bheja")\n'),
        ("            print(f\"[alert] {d['uid']} ko bhejne mein dikkat:\", err)\n",
         "            log_event(d[\"prid\"], \"send\", \"fail\", str(err))\n"
         "            print(f\"[alert] {d['uid']} ko bhejne mein dikkat:\", err)\n"),
    ],
}

for filename, pairs in CHANGES.items():
    with open(filename, encoding="utf-8-sig") as f:
        code = f.read()
    ok = True
    for old, new in pairs:
        if new in code:
            print(f"{filename}: ek hissa pehle se badla hua hai, skip")
            continue
        if code.count(old) != 1:
            print(f"{filename}: ye hissa nahi mila, file NAHI badli ->", old.strip()[:70])
            ok = False
            break
        code = code.replace(old, new)
    if ok:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"{filename}: update ho gaya")
