with open("alerts.py", encoding="utf-8-sig") as f:
    code = f.read()
changes = [
    ("from collector import already_saved, fetch_feed, fetch_text, get_prid, save\n",
     "from collector import already_saved, fetch_feed, fetch_page, fetch_text, get_prid, save\n"),
    ("        text = fetch_text(link)\n        if not text:\n            continue\n"
     "        save(conn, prid, e.get(\"title\"), link, text)\n",
     "        text, posted_at = fetch_page(link)\n        if not text:\n            continue\n"
     "        save(conn, prid, e.get(\"title\"), link, text, posted_at)\n"),
]
for old, new in changes:
    if new in code:
        print("pehle se hai")
    elif code.count(old) == 1:
        code = code.replace(old, new)
        print("update ho gaya")
    else:
        print("line nahi mili:", old.strip()[:60])
with open("alerts.py", "w", encoding="utf-8") as f:
    f.write(code)
