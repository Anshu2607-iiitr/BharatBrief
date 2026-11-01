# Website - news website jaisa layout: masthead, ticker, categories, lead story, grid

import dbfix  # noqa: F401  (SQLite: WAL + 30s wait, sabse pehle)
import html
import json
import os
from datetime import date, datetime

import streamlit as st

from alerts import cached_summary, setup_alert_tables
from auto_updater import UPDATE_MINUTES, start_updater_once, update_once
from collector import setup_db as setup_releases
from labels import AUDIENCE, CATS, LABELS, LANGS, ROLES
from translate import translated_titles
from jobqueue import enqueue, job_status, start_queue_once
import streamlit.components.v1 as components
from hero3d import hero_html
from qa import answer_question
from reminders import bot_username, future_dates, ics_file
from trace_log import _conn, simulate_pib_down
from voice import text_to_speech, voice_file, voice_script

st.set_page_config(page_title="BharatBrief · सरकारी खबरें", page_icon="📰", layout="wide")
if not os.environ.get("BB_WORKER"):       # server pe worker hi update karta hai
    start_updater_once()
if not os.environ.get("BB_WORKER"):      # server pe queue worker.py chalata hai
    start_queue_once()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+Devanagari:wght@600;800&family=Mukta:wght@400;600;700&display=swap');
.stApp, [data-testid='stAppViewContainer'], [data-testid='stHeader'] { background:#FBFAF7 !important; }
.block-container { max-width:1120px; padding-top:1.2rem; }
p, label, li, a, button, input, span { font-family:'Mukta', system-ui, sans-serif; }
.stApp p, .stApp label, .stApp li, .stApp span { color:#1F1D1A; }
footer { visibility:hidden; }
button[kind='primary'], [data-testid='stBaseButton-primary'] { background:#0E6B50 !important; border-color:#0E6B50 !important; }
button[kind='primary'] p { color:#FFFFFF !important; }
[data-testid='stVerticalBlockBorderWrapper'] { background:#FFFFFF; border-color:#E4DFD3 !important; }

.bb-mast { text-align:center; border-bottom:4px double #1F1D1A; padding-bottom:8px; margin-bottom:6px; }
.bb-mast .name { font-family:'Noto Serif Devanagari', Georgia, serif; font-size:56px; font-weight:800;
                 letter-spacing:-1px; line-height:1.1; color:#1F1D1A; }
.bb-mast .tag { font-size:16px; color:#5F5A52; margin-top:2px; }
.bb-dateline { display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; font-size:13.5px;
               color:#5F5A52; border-bottom:1px solid #1F1D1A; padding:6px 0; margin-bottom:10px; }

.bb-ticker { display:flex; align-items:center; overflow:hidden; background:#FFFFFF;
             border:1px solid #E4DFD3; border-radius:6px; margin:8px 0 18px; }
.bb-ticker .label { background:#B42318; color:#FFFFFF; font-weight:700; padding:7px 14px; white-space:nowrap; z-index:1; }
.bb-ticker .track { white-space:nowrap; display:inline-block; padding:7px 0; color:#1F1D1A;
                    animation:bb-scroll 70s linear infinite; }
.bb-ticker .track span { margin-right:48px; }
@keyframes bb-scroll { from { transform:translateX(30%); } to { transform:translateX(-100%); } }
@media (prefers-reduced-motion: reduce) { .bb-ticker .track { animation:none; } }

.bb-kicker { font-size:12.5px; font-weight:700; letter-spacing:.05em; text-transform:uppercase; color:#B42318; }
.bb-lead-title { font-family:'Noto Serif Devanagari', Georgia, serif; font-size:32px; font-weight:800;
                 line-height:1.35; margin:6px 0; color:#1F1D1A; }
.bb-card-title { font-family:'Noto Serif Devanagari', Georgia, serif; font-size:20px; font-weight:700;
                 line-height:1.45; margin:4px 0; color:#1F1D1A; }
.bb-time { font-size:13px; color:#6B655C; }
.bb-snippet { font-size:17px; line-height:1.65; color:#33302B; margin:6px 0; }
.bb-lead .bb-snippet { font-size:19px; }
.bb-check { display:inline-block; font-size:13px; color:#0A4F3B; background:#E4F2EC; border-radius:6px; padding:3px 8px; }
.bb-sub { font-size:14px; font-weight:700; color:#0A4F3B; margin-top:8px; }
.bb-link { font-size:14px; color:#0E6B50 !important; font-weight:600; text-decoration:none; }
.bb-section { font-family:'Noto Serif Devanagari', Georgia, serif; font-size:22px; font-weight:800;
              border-top:3px solid #1F1D1A; padding-top:6px; margin:22px 0 10px; }
.bb-foot { text-align:center; font-size:13px; color:#6B655C; border-top:1px solid #DED8CC; margin-top:30px; padding-top:12px; }
</style>
""", unsafe_allow_html=True)

HINDI_DAYS = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
HINDI_MONTHS = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई",
                "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]


# ---------- Data ----------
def last_fetch_time():
    conn = _conn()
    row = conn.execute("SELECT at FROM events WHERE step='fetch' AND status='ok' ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return datetime.fromisoformat(row[0]) if row else None


def latest_releases(n=21):
    conn = setup_releases()
    setup_alert_tables(conn)
    rows = conn.execute("""
        SELECT r.prid, r.title, r.link, NULLIF(r.posted_at, 'unknown'), r.fetched_at,
               json_extract(s.json, '$.kiske_liye')
        FROM releases r LEFT JOIN summaries s ON s.prid = r.prid AND s.lang = 'hi'
        WHERE r.full_text != ''
        ORDER BY COALESCE(NULLIF(r.posted_at, 'unknown'), r.fetched_at) DESC LIMIT ?""", (n,)).fetchall()
    conn.close()
    return rows


def cached_only(prid, lang):
    conn = setup_releases()
    setup_alert_tables(conn)
    row = conn.execute("SELECT json FROM summaries WHERE prid = ? AND lang = ?", (prid, lang)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def original_excerpt(prid, chars=320):
    """Summary banne tak: original release ki shuru ki lines."""
    conn = setup_releases()
    row = conn.execute("SELECT full_text FROM releases WHERE prid = ?", (prid,)).fetchone()
    conn.close()
    text = " ".join(p.strip() for p in (row[0] if row else "").split("\n") if len(p.strip()) > 40)
    return text[:chars].rsplit(" ", 1)[0] + "…" if len(text) > chars else text


def make_summary(prid, lang):
    conn = setup_releases()
    setup_alert_tables(conn)
    s = cached_summary(conn, prid, lang)
    conn.close()
    return s


def fail_kind(prid):
    conn = _conn()
    row = conn.execute("SELECT step FROM events WHERE prid = ? AND status = 'fail' ORDER BY id DESC LIMIT 1",
                       (prid,)).fetchone()
    conn.close()
    return "verify" if row and row[0] == "verify" else "busy"


def nice_time(posted, fetched):
    when = datetime.fromisoformat(posted or fetched)
    t = when.strftime("%I:%M %p")
    if not posted:
        t = "~" + t
    return t if when.date() == date.today() else f"{when:%d %b} · {t}"


def dateline(lang):
    d = date.today()
    if lang == "hi":
        return f"{HINDI_DAYS[d.weekday()]}, {d.day} {HINDI_MONTHS[d.month - 1]} {d.year}"
    return d.strftime("%A, %d %B %Y")


# ---------- Ek khabar ----------
def story(row, lang, L, lead=False):
    prid, title, link, posted, fetched, audience = row
    e = html.escape
    kicker = dict(CATS.get(lang, CATS["en"])).get((audience or "").strip().lower(), "PIB")
    title_cls = "bb-lead-title" if lead else "bb-card-title"
    st.markdown(f'<div class="{"bb-lead" if lead else ""}"><div class="bb-kicker">{e(kicker)}</div>'
                f'<div class="{title_cls}">{e(title)}</div>'
                f'<div class="bb-time">🕒 {e(nice_time(posted, fetched))} · PIB</div></div>',
                unsafe_allow_html=True)

    key = f"s_{prid}_{lang}"
    if key not in st.session_state:
        cached = cached_only(prid, lang)
        if cached:
            st.session_state[key] = cached
    s = st.session_state.get(key)

    if s is None or s == "fail":
        st.session_state.pop(key, None)
        excerpt = original_excerpt(prid)
        if excerpt:                                   # card kabhi khaali nahi: original ki pehli lines
            st.markdown(f'<div class="bb-snippet">{e(excerpt)}</div>'
                        f'<span class="bb-time">PIB · original</span>', unsafe_allow_html=True)
        if job_status(prid, lang) == "failed":
            st.caption(L["verify"])
        else:
            enqueue(prid, lang)                       # khud queue mein, user ko kuch nahi dabana
            st.caption("⏳ " + L["working"])
    else:
        st.markdown(f'<div class="bb-snippet">{e(str(s.get("kya_hua", "")))}</div>'
                    f'<span class="bb-check">{e(L["checked"])}</span>', unsafe_allow_html=True)
        path = voice_file(prid, lang)
        if lead and os.path.exists(path):
            st.audio(path)
        with st.expander(f'{L["asar"]} · {L["karna"]}', expanded=lead):
            st.markdown(f'<div class="bb-sub">{e(L["asar"])}</div><div class="bb-snippet">{e(str(s.get("aap_pe_asar", "")))}</div>'
                        f'<div class="bb-sub">{e(L["karna"])}</div><div class="bb-snippet">{e(str(s.get("kya_karna_hai", "")))}</div>',
                        unsafe_allow_html=True)
            if os.path.exists(path):
                if not lead:
                    st.audio(path)
            elif st.button(L["listen"], key=f"l_{prid}_{lang}"):
                with st.spinner(L["s3"]):
                    text_to_speech(voice_script(s, lang), lang, path)
                st.rerun()

    if isinstance(s, dict):
        for due in future_dates(s):
            d = date.fromisoformat(due)
            st.markdown(f'<div class="bb-sub">⏰ {e(L.get("rem_title", "आने वाली तारीख · Upcoming date"))}: {d:%d %b %Y}</div>', unsafe_allow_html=True)
            c_a, c_b = st.columns(2)
            c_a.download_button(L.get("cal", "📅 Calendar"), ics_file(prid, title, link, d), file_name=f"bharatbrief_{prid}_{due}.ics",
                                mime="text/calendar", key=f"ics_{prid}_{due}_{lang}", use_container_width=True)
            bot = bot_username()
            if bot:
                c_b.link_button(L.get("tg", "⏰ Telegram reminder"), f"https://t.me/{bot}?start=rem_{prid}_{d:%Y%m%d}", use_container_width=True)
    if isinstance(s, dict):
        with st.form(f"q_{prid}_{lang}", border=False):
            q = st.text_input(L.get("ask_ph", "Ask about this news…"), key=f"qi_{prid}_{lang}", placeholder=L.get("ask_ph", "Ask about this news…"),
                              label_visibility="collapsed")
            asked = st.form_submit_button(L.get("ask", "Ask"))
        if asked and q.strip():
            with st.spinner(L.get("thinking", "…")):
                st.session_state[f"qa_{prid}_{lang}"] = answer_question(prid, q.strip(), lang)
        res = st.session_state.get(f"qa_{prid}_{lang}")
        if res and res.get("ok"):
            nums = ", ".join(str(n) for n, _ in res["paras"])
            quotes = "".join(f'<div style="border-left:3px solid #0E6B50;padding:2px 10px;margin:4px 0;'
                             f'font-size:14px;color:#4A453E">¶{n}: {e(t[:260])}…</div>' for n, t in res["paras"])
            st.markdown(f'<div class="bb-snippet"><b>→</b> {e(res["answer"])}</div>'
                        f'<div class="bb-time">{e(L.get("source", "Source: paragraph"))} {nums}</div>{quotes}', unsafe_allow_html=True)
        elif res:
            st.info(L.get("notfound", "Not in this release.") if res.get("reason") == "notfound" else L["busy"])
    st.markdown(f'<a class="bb-link" href="{e(link)}" target="_blank">{e(L["original"])} ↗</a>',
                unsafe_allow_html=True)


# ---------- Page ----------
# ---- Bhasha-patti: sabse upar, saari bhashayein, URL mein yaad (?lang=ta) ----
_names = {c: n for n, c in LANGS.items()}
_codes = list(_names)
_start = st.query_params.get("lang", "hi")
_start = _start if _start in _names else "hi"
st.markdown('<div class="bb-langbar">🌐 भाषा चुनें · Choose your language</div>', unsafe_allow_html=True)
if hasattr(st, "pills"):
    lang = st.pills("lang", _codes, format_func=lambda c: _names[c], default=_start,
                    selection_mode="single", label_visibility="collapsed") or _start
else:
    lang = st.radio("lang", _codes, index=_codes.index(_start), format_func=lambda c: _names[c],
                    horizontal=True, label_visibility="collapsed")
if st.query_params.get("lang") != lang:
    st.query_params["lang"] = lang
st.markdown("""<style>
.bb-langbar { font-size:14px; font-weight:700; color:#0A4F3B; margin:0 0 4px; }
[data-testid='stPills'] button, [data-testid='stButtonGroup'] button { border-radius:999px !important; }
</style>""", unsafe_allow_html=True)
L = LABELS[lang]
from languages import RTL
if lang in RTL:
    st.markdown('<style>.bb-snippet,.bb-card-title,.bb-lead-title,.bb-sub,.bb-mast .tag'
                '{direction:rtl;text-align:right}</style>', unsafe_allow_html=True)

st.markdown(f'<div class="bb-mast"><div class="name">BharatBrief</div>'
            f'<div class="tag">{html.escape(L["tagline"])}</div></div>', unsafe_allow_html=True)

# ---- Asli product Telegram bot hai: website se seedha wahan bhejo ----
_bot = bot_username()
if _bot:
    from bot_text import t as _bt
    st.markdown(f"""
<a href="https://t.me/{html.escape(_bot)}?start=web" target="_blank" style="text-decoration:none">
<div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;background:linear-gradient(120deg,#229ED9,#1C7FB0);
            border-radius:14px;padding:16px 22px;margin:6px 0 14px;box-shadow:0 6px 18px rgba(34,158,217,.25)">
  <div style="font-size:40px;line-height:1">✈️</div>
  <div style="flex:1;min-width:220px">
    <div style="color:#fff;font-size:21px;font-weight:700">{html.escape(_bt(lang, "web_cta_title"))}</div>
    <div style="color:#E6F4FB;font-size:15px;margin-top:2px">{html.escape(_bt(lang, "web_cta_sub"))}</div>
  </div>
  <div style="background:#fff;color:#1C7FB0;font-weight:700;border-radius:999px;padding:10px 20px;font-size:16px">
    {html.escape(_bt(lang, "web_cta_btn"))} →</div>
</div></a>""", unsafe_allow_html=True)

cats = dict(CATS.get(lang, CATS["en"]))
role = st.radio("category", list(cats), format_func=lambda c: cats[c], horizontal=True,
                label_visibility="collapsed")


@st.fragment(run_every=30)
def front_page(lang, role, L):
    last = last_fetch_time()
    st.markdown(f'<div class="bb-dateline"><span>{html.escape(dateline(lang))}</span>'
                f'<span>{html.escape(L["last"])}: {last.strftime("%I:%M %p") if last else "…"} · '
                f'{html.escape(L["auto"].format(m=UPDATE_MINUTES))}</span></div>', unsafe_allow_html=True)
    if simulate_pib_down():
        st.warning(L["down"])

    rows = [r for r in latest_releases()
            if role == "sabhi" or (r[5] or "").strip().lower() in ("", role, "sabhi")]
    if not rows:
        st.info(L["none"])
        return
    try:
        tr = translated_titles(rows, lang)             # title bhi user ki bhasha mein
    except Exception as err:                       # translation na mile to original title, page kabhi na toote
        print('[home] title translate skip:', err)
        tr = {}
    rows = [(r[0], tr.get(r[0], r[1])) + tuple(r[2:]) for r in rows]

    ticker = "".join(f"<span>● {html.escape(r[1])}</span>" for r in rows[:8])
    st.markdown(f'<div class="bb-ticker"><div class="label">{html.escape(L.get("latest", "Latest"))}</div>'
                f'<div class="track">{ticker}</div></div>', unsafe_allow_html=True)
    st.iframe(hero_html(rows[:8], lang, L, cached_only, dict(CATS.get(lang, CATS["en"]))), height=660)

    with st.container(border=True):
        story(rows[0], lang, L, lead=True)

    rest = rows[1:]
    for i in range(0, len(rest), 2):
        cols = st.columns(2)
        for col, row in zip(cols, rest[i:i + 2]):
            with col:
                with st.container(border=True):
                    story(row, lang, L)

    if st.button(L["update"]):
        with st.spinner(L["working"]):
            update_once(force=True, who="button")
        st.rerun()


front_page(lang, role, L)

st.markdown('<div class="bb-foot">Source: Press Information Bureau (PIB), Government of India · '
            'Summaries are AI-generated and every number and date is checked against the original release.</div>',
            unsafe_allow_html=True)
