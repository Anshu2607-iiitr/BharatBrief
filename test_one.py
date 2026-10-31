from summarize import get_release, summarize

prid, title, text = get_release("2331036")
print("Title:", title)
print("Text length:", len(text))
s = summarize(title, text[:2000], "hi")
print("Result:", "BANI" if s else "FAIL")
