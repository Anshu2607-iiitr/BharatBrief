with open("summarize.py", encoding="utf-8-sig") as f:
    code = f.read()
old = "            busy = any(code in str(err) for code in RETRY_CODES)\n"
new = ("            busy = any(code in str(err) for code in RETRY_CODES)\n"
       "            if \"quota\" in str(err).lower():\n"
       "                busy = False      # daily quota khatam: retry bekaar, seedha backup pe jao\n")
if new in code:
    print("pehle se hai")
elif code.count(old) == 1:
    with open("summarize.py", "w", encoding="utf-8") as f:
        f.write(code.replace(old, new))
    print("update ho gaya")
else:
    print("line nahi mili")
