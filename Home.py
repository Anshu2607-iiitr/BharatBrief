# Website - news website jaisa layout: masthead, ticker, categories, lead story, grid

import html
import json
import os
from datetime import date, datetime

import streamlit as st

from alerts import cached_summary, setup_alert_tables
from auto_updater import UPDATE_MINUTES, start_updater_once, update_once
from collector import setup_db as setup_releases
from labels import AUDIENCE, LABELS, LANGS, ROLES
from trace_log import _conn, simulate_pib_down
from voice import text_to_speech, voice_script

st.set_page_config(page_title="BharatBrief · सरकारी खबरें", page_icon="📰", layout="wide")
start_updater_once()

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
    kicker = AUDIENCE.get((audience or "").strip().lower(), "PIB")
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

    if s is None:
        if st.button(L["explain"], key=f"b_{prid}_{lang}", type="primary", use_container_width=True):
            with st.status(L["working"], expanded=True) as status:
                st.write("1. " + L["s1"])
                s = make_summary(prid, lang)
                status.update(label=L["done"] if s else L["retry"], state="complete" if s else "error",
                              expanded=False)
            st.session_state[key] = s or "fail"
            st.rerun()
    elif s == "fail":
        st.info(L[fail_kind(prid)])
        if st.button(L["retry"], key=f"r_{prid}_{lang}"):
            del st.session_state[key]
            st.rerun()
    else:
        st.markdown(f'<div class="bb-snippet">{e(str(s.get("kya_hua", "")))}</div>'
                    f'<span class="bb-check">{e(L["checked"])}</span>', unsafe_allow_html=True)
        path = f"khabar_{prid}_{lang}.wav"
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

    st.markdown(f'<a class="bb-link" href="{e(link)}" target="_blank">{e(L["original"])} ↗</a>',
                unsafe_allow_html=True)


# ---------- Page ----------
top_l, top_r = st.columns([4, 1])
lang = LANGS[top_r.selectbox("भाषा · Language", list(LANGS), label_visibility="collapsed")]
L = LABELS[lang]

st.markdown(f'<div class="bb-mast"><div class="name">BharatBrief</div>'
            f'<div class="tag">{html.escape(L["tagline"])}</div></div>', unsafe_allow_html=True)

role = ROLES[st.radio("category", list(ROLES), horizontal=True, label_visibility="collapsed")]


@st.fragment(run_every=60)
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

    ticker = "".join(f"<span>● {html.escape(r[1])}</span>" for r in rows[:8])
    st.markdown(f'<div class="bb-ticker"><div class="label">ताज़ा · Latest</div>'
                f'<div class="track">{ticker}</div></div>', unsafe_allow_html=True)

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
