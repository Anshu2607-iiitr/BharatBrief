with open("Home.py", encoding="utf-8-sig") as f:
    code = f.read()
start = code.find("LABELS = {")
end = code.find("# ---------- Data ----------")
if start == -1 or end == -1:
    print("LABELS ya Data section nahi mila")
else:
    with open("labels.py", "w", encoding="utf-8") as f:
        f.write("# Website ke UI shabd, har bhasha mein\n\n" + code[start:end].rstrip() + "\n")
    print("labels.py ban gayi")
