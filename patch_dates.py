# Patch: chhota input, saal != tareekh niyam, verifier year-only rule

CHANGES = {
    "summarize.py": [
        ("- Write every number with digits 0-9, even inside {language} text.\n",
         "- Write every number with digits 0-9, even inside {language} text.\n"
         "- A year alone (like 2047 or 2014) is a NUMBER, not a date. Put it in sankhya, never in tareekh_iso.\n"
         "- Only put a date in tareekh_iso if the press release gives a day and a month.\n"),
    ],
    "voice.py": [
        ("        summary = summarize(title, text + feedback, lang)\n",
         "        summary = summarize(title, text[:3000] + feedback, lang)   # chhota input = kam tokens\n"),
    ],
    "verify.py": [
        ('        if d not in dates and str(d)[5:] not in dates:\n'
         '            problems.append(f"date {d} is not in the press release")\n',
         '        d = str(d)\n'
         '        if d in dates or d[5:] in dates:\n'
         '            continue\n'
         '        if d.endswith("-01-01") and d[:4] in numbers:\n'
         '            continue        # sirf saal tha (jaise 2047), AI ne use date bana diya\n'
         '        problems.append(f"date {d} is not in the press release")\n'),
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
