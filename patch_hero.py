with open("Home.py", encoding="utf-8-sig") as f:
    code = f.read()
changes = [
    ("from labels import AUDIENCE, LABELS, LANGS, ROLES\n",
     "from labels import AUDIENCE, LABELS, LANGS, ROLES\n"
     "import streamlit.components.v1 as components\n"
     "from hero3d import hero_html\n"),
    ("                f'<div class=\"track\">{ticker}</div></div>', unsafe_allow_html=True)\n",
     "                f'<div class=\"track\">{ticker}</div></div>', unsafe_allow_html=True)\n"
     "    components.html(hero_html(rows[:8], lang, L, cached_only, AUDIENCE), height=660)\n"),
]
for old, new in changes:
    if new in code:
        print("pehle se hai")
    elif code.count(old) == 1:
        code = code.replace(old, new)
        print("update ho gaya")
    else:
        print("line nahi mili:", old.strip()[:60])
with open("Home.py", "w", encoding="utf-8") as f:
    f.write(code)
