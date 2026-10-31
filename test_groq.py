from summarize import GROQ_MODEL, call_groq

print("Groq model:", GROQ_MODEL or "KHAALI (model nahi chuna gaya)")
raw = call_groq('Reply ONLY with JSON: {"ok": "haan"}')
print("Groq jawab:", raw)
