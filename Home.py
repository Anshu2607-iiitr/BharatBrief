# Lesson 13 + 14: Website - khabrein khud update hoti hain

import os
from datetime import datetime

import streamlit as st

from alerts import cached_summary, setup_alert_tables
from auto_updater import UPDATE_MINUTES, start_updater_once, update_once
from collector import setup_db as setup_releases
from trace_log import _conn, simulate_pib_down
from voice import text_to_speech, voice_script

st.set_page_config(page_title="BharatBrief", page_icon="📰", layout="centered")
start_updater_once()                 # background updater (sirf pehli baar shuru hota hai)

LANGS = {"हिन्दी": "hi", "English": "en", "বাংলা": "bn",
         "தமிழ்": "ta", "తెలుగు": "te", "मराठी": "mr"}
ROLES = {"Sabhi khabrein": "sabhi", "Student": "student", "Kisan": "kisan",
         "MSME / dukaan": "msme", "Mahila": "mahila"}


# ---------- Data ----------
def last_fetch_time():
    conn = _conn()
    row = conn.execute("SELECT at FROM events WHERE step='fetch' AND status='ok' "
                       "ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return datetime.fromisoformat(row[0]) if row else None


def latest_releases(n=8):
    conn = setup_releases()
    setup_alert_tables(conn)
    rows = conn.execute("""
        SELECT r.prid, r.title, r.link, p.audience
        FROM releases r LEFT JOIN processed p ON p.prid = r.prid
        WHERE r.full_text != ''
        ORDER BY CAST(r.prid AS INTEGER) DESC LIMIT ?""", (n,)).fetchall()
    conn.close()
    return rows


def get_summary(prid, lang):
    conn = setup_releases()
    setup_alert_tables(conn)
    s = cached_summary(conn, prid, lang)
    conn.close()
    return s


def get_audio(prid, lang, summary):
    path = f"khabar_{prid}_{lang}.wav"
    if os.path.exists(path) or text_to_speech(voice_script(summary, lang), lang, path):
        return path
    return None


# ---------- Page ----------
st.title("BharatBrief")
st.caption("Sarkari khabrein, aapki bhasha mein, aasaan shabdon mein. "
           "Har number aur tareekh original release se check ki jaati hai.")

c1, c2 = st.columns(2)
lang = LANGS[c1.selectbox("Bhasha", list(LANGS))]
role = ROLES[c2.selectbox("Aap kaun hain", list(ROLES))]

if st.button("Abhi update karo"):
    with st.spinner("PIB se nayi khabrein la rahe hain..."):
        update_once()


@st.fragment(run_every=120)          # sirf ye hissa har 2 minute khud refresh hota hai
def news_list(lang, role):
    if simulate_pib_down():
        st.warning("PIB abhi available nahi. Pichhli baar ki khabrein dikh rahi hain.")

    last = last_fetch_time()
    st.caption((f"Last update: {last:%d %b, %H:%M}" if last else "Pehla update chal raha hai...")
               + f" · khud update: har {UPDATE_MINUTES} min")

    shown = 0
    for prid, title, link, audience in latest_releases():
        if role != "sabhi" and audience not in (None, role, "sabhi"):
            continue
        shown += 1

        with st.container(border=True):
            if audience and audience != "unverified":
                st.caption(f"Kiske liye: {audience}")
            st.markdown(f"**{title}**")

            key = f"s_{prid}_{lang}"
            if key not in st.session_state:
                if st.button("Aasaan bhasha mein samjhao", key=f"b_{prid}_{lang}"):
                    with st.spinner("Summary ban rahi hai aur check ho rahi hai (30-60 sec)..."):
                        st.session_state[key] = get_summary(prid, lang) or "fail"
                    st.rerun()

            s = st.session_state.get(key)
            if s == "fail":
                st.error("Ye summary verify nahi ho paayi, isliye nahi dikha rahe. Original padhein.")
            elif s:
                st.write(f"**Kya hua:** {s.get('kya_hua', '')}")
                st.write(f"**Aap pe asar:** {s.get('aap_pe_asar', '')}")
                st.write(f"**Aapko kya karna hai:** {s.get('kya_karna_hai', '')}")
                st.success("✓ Har number aur tareekh original release se check ki gayi")

                akey = f"a_{prid}_{lang}"
                if akey not in st.session_state:
                    with st.spinner("Awaaz ban rahi hai..."):
                        st.session_state[akey] = get_audio(prid, lang, s)
                if st.session_state[akey]:
                    st.caption("AI se bani awaaz")
                    st.audio(st.session_state[akey])

            st.markdown(f"[Original PIB release padhein]({link})")

    if shown == 0:
        st.info("Abhi aapke liye koi nayi khabar nahi hai.")


news_list(lang, role)
