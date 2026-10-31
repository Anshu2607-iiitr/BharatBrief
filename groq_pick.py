# Groq ke available models mein se sabse achha model khud chunna

import os

import requests

MODELS_URL = "https://api.groq.com/openai/v1/models"

# Pasand ka order: bade, general models pehle (Hindi + JSON achha)
PREFERRED = ["llama-4-maverick", "llama-4-scout", "qwen", "70b", "gpt-oss-120b", "120b", "gpt-oss"]

# Ye models summary ke kaam ke nahi
SKIP = ("whisper", "guard", "allam", "tts", "playai", "orpheus", "prompt")


def pick_groq_model():
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return ""
    try:
        r = requests.get(MODELS_URL, headers={"Authorization": f"Bearer {key}"}, timeout=15)
        ids = [m["id"] for m in r.json().get("data", [])]
    except Exception as err:
        print("  Groq models list nahi mili:", err)
        return ""

    usable = [i for i in ids if not any(s in i.lower() for s in SKIP)]
    for pattern in PREFERRED:
        for model_id in usable:
            if pattern in model_id.lower():
                return model_id
    return usable[0] if usable else ""


if __name__ == "__main__":
    print("Chuna gaya model:", pick_groq_model() or "koi model nahi mila")
