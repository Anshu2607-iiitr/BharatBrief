with open("Home.py", encoding="utf-8-sig") as f:
    code = f.read()

old = "footer { visibility: hidden; }\n"
new = (
    "footer { visibility: hidden; }\n"
    "/* Theme file na bhi chale, tab bhi light look */\n"
    ".stApp, [data-testid='stAppViewContainer'], [data-testid='stHeader'] { background:#F7F4EE !important; }\n"
    ".stApp p, .stApp label, .stApp li, .stApp span { color:#1F1D1A; }\n"
    "[data-testid='stVerticalBlockBorderWrapper'] { background:#FFFFFF; border-color:#DED8CC !important; }\n"
    "button[kind='primary'], [data-testid='stBaseButton-primary'] "
    "{ background:#0E6B50 !important; border-color:#0E6B50 !important; color:#FFFFFF !important; }\n"
    "button[kind='primary'] p { color:#FFFFFF !important; }\n"
)
if new in code:
    print("pehle se hai")
elif code.count(old) == 1:
    with open("Home.py", "w", encoding="utf-8") as f:
        f.write(code.replace(old, new))
    print("update ho gaya")
else:
    print("line nahi mili")
