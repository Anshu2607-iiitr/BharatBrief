# BharatBrief

**Government press releases, explained in your language, checked number by number, delivered as voice.**

Live website: <LIVE_URL>  
Telegram bot: @<BOT_USERNAME>

## The problem

The Press Information Bureau (PIB) publishes new government announcements every day: scheme deadlines,
rule changes, new benefits. They are written in formal Hindi or English, and most citizens never see them
or cannot act on them. Existing tools answer questions about a fixed list of schemes; none of them watches
the daily releases, explains each one in simple words, and pushes it to the people it affects.

**Who is affected:** farmers, students, small businesses (MSMEs) and women who depend on schemes and
deadlines, especially people who prefer their own language or listening over reading.

## What BharatBrief does

1. **Watches PIB live** every 10 minutes and stores every new release.
2. **Explains each release simply** in 6 Indian languages: what happened, how it affects you, what you should do.
3. **Verifies every number and date** in the summary against the original release. A wrong summary is
   retried once with the error fed back to the model; if it is still wrong, it is **not sent**.
4. **Speaks it**: an AI voice note in the same language, labelled as AI-generated.
5. **Pushes it to the right people** on Telegram (matched by role) and shows it on a public website.

## Architecture

```mermaid
flowchart LR
    PIB[PIB RSS feed<br/>live] --> W[worker.py<br/>every 10 min]
    W --> DB[(SQLite<br/>releases, summaries,<br/>users, events)]
    W --> S[Summary<br/>Gemini, fallback Groq]
    S --> V{Verifier<br/>numbers + dates<br/>match original?}
    V -- no, retry once --> S
    V -- still no --> X[Not sent<br/>logged]
    V -- yes --> DB
    DB --> T[Sarvam TTS<br/>voice note]
    T --> B[Telegram bot<br/>push alerts, /khabar]
    T --> H[Website<br/>Home.py]
    DB --> D[Dashboard<br/>agent trace,<br/>PIB-down toggle]
```

## What makes it robust

| Failure | What the system does |
|---|---|
| Gemini busy / quota over | Retries with backoff, then falls back to Groq automatically |
| A model is retired | Groq model is picked automatically from the live model list |
| AI writes a wrong number or date | Verifier catches it, retries with feedback, blocks it if still wrong |
| PIB is down | Shows the last data with a clear notice; nothing crashes (demo toggle on the dashboard) |
| Any API hangs | Every call has a timeout |
| Same news twice | PRID-based de-duplication and a `sent_log`, so nobody gets a message twice |

## Tech stack

Python · SQLite · Streamlit · python-telegram-bot · Google Gemini · Groq · Sarvam AI (Bulbul TTS) ·
ffmpeg · Docker · Render

**Data source:** PIB press-release RSS (`https://pib.gov.in/RssMain.aspx?ModId=6&Lang=2&Regid=3`) and the
release pages it links to. No mock data: everything shown is fetched live.

## Run it locally

```bash
pip install -r requirements.txt
```

Create a `.env` file (never commit it):

```
GEMINI_API_KEY=...
GROQ_API_KEY=...
SARVAM_API_KEY=...
TELEGRAM_BOT_TOKEN=...
```

Then, in three terminals:

```bash
python worker.py                      # updates every 10 minutes
python bot.py                         # Telegram bot
python -m streamlit run Home.py       # website + dashboard
```

Health check before a demo: `python check_apis.py`

## Project files

| File | Role |
|---|---|
| `collector.py` | PIB feed, release text, posted time, SQLite |
| `summarize.py` | Multilingual summary, Gemini with Groq fallback |
| `groq_pick.py` | Picks a working Groq model automatically |
| `verify.py` | Checks every date and number against the original |
| `voice.py` | Verified summary to Sarvam voice |
| `audio_util.py` | WAV to OGG/Opus for Telegram voice notes |
| `alerts.py` | Audience matching, cache, push alerts |
| `bot.py` | Telegram onboarding, `/khabar`, `/check` |
| `worker.py`, `auto_updater.py` | Background updates every 10 minutes |
| `trace_log.py` | Event log (agent trace) and demo settings |
| `Home.py`, `pages/2_Dashboard.py` | Website and dashboard |
| `check_apis.py` | One-command health check of every API |

## Limitations and roadmap

- The free server's disk is temporary; the next step is a hosted Postgres database.
- More languages (Bhashini for Assamese and others), WhatsApp channel.
- eGazette notifications with clause-level "what changed" alerts.
- An MSME compliance calendar from GST and RBI notices.
