with open("summarize.py", encoding="utf-8-sig") as f:
    code = f.read()

changes = [
    # 1. Qwen ko sochne se roko
    ('        "messages": [{"role": "user", "content": contents}],\n',
     '        "messages": [{"role": "user", "content": contents + "\\n\\n/no_think"}],\n'),
    # 2. <think>...</think> hata ke JSON dhoondho
    ('    if not raw:\n        return None\n    try:\n        return json.loads(raw)\n',
     '    if not raw:\n        return None\n'
     '    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()\n'
     '    try:\n        return json.loads(raw)\n'),
]
for old, new in changes:
    if new in code:
        print("pehle se hai")
    elif code.count(old) == 1:
        code = code.replace(old, new)
        print("update ho gaya")
    else:
        print("line nahi mili:", old.strip()[:50])

with open("summarize.py", "w", encoding="utf-8") as f:
    f.write(code)

with open("voice.py", encoding="utf-8-sig") as f:
    v = f.read()
v2 = v.replace("text[:3000] + feedback", "text[:2000] + feedback")
with open("voice.py", "w", encoding="utf-8") as f:
    f.write(v2)
print("voice.py:", "update ho gaya" if v2 != v else "pehle se hai / line nahi mili")
