# Lesson 23: Awaaz se sawaal - Telegram voice note -> text (Groq Whisper, free)
# Jo log likh nahi paate, wo bolkar pooch sakein.

import os

import requests

URL = "https://api.groq.com/openai/v1/audio/transcriptions"
# Whisper in bhashaon ko pehchanta hai; inke liye bhasha batane se accuracy badhti hai
WHISPER_LANGS = {"hi", "en", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "ur", "ne", "as", "sa", "sd"}


def transcribe(path, lang=None):
    """Audio file (ogg/wav/mp3) -> text. Fail ho to None."""
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        print("  GROQ_API_KEY nahi, awaaz nahi samajh sakte")
        return None
    data = {"model": os.environ.get("WHISPER_MODEL", "whisper-large-v3-turbo"),
            "response_format": "json", "temperature": "0"}
    if lang in WHISPER_LANGS:
        data["language"] = lang
    try:
        with open(path, "rb") as f:
            r = requests.post(URL, headers={"Authorization": f"Bearer {key}"},
                              files={"file": (os.path.basename(path), f)}, data=data, timeout=60)
    except requests.RequestException as err:
        print("  Whisper network problem:", err)
        return None
    if r.status_code != 200:
        print("  Whisper error:", r.status_code, r.text[:200])
        return None
    return (r.json().get("text") or "").strip() or None


if __name__ == "__main__":
    import sys
    print(transcribe(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
