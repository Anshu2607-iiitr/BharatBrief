# BharatBrief – practice lessons

Pre-hackathon practice code: learning the building blocks (PIB RSS feed, text extraction,
SQLite, LLM summaries in Indian languages, a verifier, and a Telegram bot).

## Setup

```powershell
pip install feedparser requests beautifulsoup4 google-genai python-telegram-bot
$env:GEMINI_API_KEY = "<your Gemini key>"
$env:TELEGRAM_BOT_TOKEN = "<your BotFather token>"
```

Keys are read only from environment variables. Never put them in code or commit them.

## Lessons

| File | Lesson | Run |
| --- | --- | --- |
| `rss_practice.py` | 1. Read the PIB Hindi press-release RSS feed | `python rss_practice.py` |
| `release_text.py` | 2. Extract a release's full text (de-duplicated) | `python release_text.py` |
| `collector.py` | 3. Save releases to SQLite, skip duplicates by PRID | `python collector.py` |
| `summarize.py` | 4. Summary in the user's language (`hi`, `ta`, `bn`, …) | `python summarize.py ta` |
| `verify.py` | 5. Check every date and number against the original; retry once | `python verify.py ta` / `python verify.py ta --test` |
| `bot.py` | 6. Telegram onboarding: role, state, language → `users` table | `python bot.py` |

Data source: PIB RSS, `https://pib.gov.in/RssMain.aspx?ModId=6&Lang=2&Regid=3`.
