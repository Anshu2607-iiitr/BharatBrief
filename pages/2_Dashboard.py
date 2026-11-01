# Lesson 12: Dashboard - aaj ki releases, agent trace, PIB down toggle

import dbfix  # noqa: F401  (SQLite: WAL + 30s wait, sabse pehle)
import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

from trace_log import set_pib_down, simulate_pib_down, _conn

st.set_page_config(page_title="BharatBrief dashboard", layout="wide")


def q(sql, args=()):
    conn = _conn()                       # events/settings tables bhi ban jaati hain
    try:
        return pd.read_sql_query(sql, conn, params=args)
    except Exception:
        return pd.DataFrame()           # koi table abhi nahi bani to khaali
    finally:
        conn.close()


st.title("BharatBrief · Sarkari khabar agent")

# ---------- PIB status + demo toggle ----------
last_fetch = q("SELECT at FROM events WHERE step='fetch' AND status='ok' ORDER BY id DESC LIMIT 1")
last = last_fetch["at"][0] if not last_fetch.empty else "abhi tak nahi"

down = st.toggle("Demo: PIB down karo", value=simulate_pib_down())
if down != simulate_pib_down():
    set_pib_down(down)
if down:
    st.warning(f"PIB abhi available nahi (demo). Last update {last} ka data dikh raha hai. "
               "Naye summaries ruk gaye hain, app chal rahi hai.")
else:
    st.success(f"PIB feed live · last fetch: {last}")

# ---------- KPIs ----------
today = date.today().isoformat()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Aaj ki releases", int(q("SELECT COUNT(*) n FROM releases WHERE fetched_at LIKE ?", (today + "%",))["n"][0]))
c2.metric("Verified summaries", int(q("SELECT COUNT(*) n FROM events WHERE step='verify' AND status='ok'")["n"].get(0, 0)))
c3.metric("Verifier ne pakdi galtiyan", int(q("SELECT COUNT(*) n FROM events WHERE step='verify' AND status='fail'")["n"].get(0, 0)))
c4.metric("Alerts bheje", int(q("SELECT COUNT(*) n FROM sent_log")["n"].get(0, 0)) if not q("SELECT name FROM sqlite_master WHERE name='sent_log'").empty else 0)

# ---------- Releases + trace ----------
left, right = st.columns([3, 2])

releases = q("""
    SELECT r.prid, r.title, r.fetched_at, p.audience
    FROM releases r LEFT JOIN processed p ON p.prid = r.prid
    ORDER BY CAST(r.prid AS INTEGER) DESC LIMIT 20""")

with left:
    st.subheader("Releases")
    if releases.empty:
        st.info("Abhi koi release nahi. Bot pe /check chalao.")
    else:
        st.dataframe(releases.rename(columns={"prid": "PRID", "title": "Title",
                                              "fetched_at": "Fetch time", "audience": "Kiske liye"}),
                     hide_index=True, use_container_width=True)

with right:
    st.subheader("Agent trace")
    if releases.empty:
        st.write("Release chuno")
    else:
        options = {f"{row.prid} · {str(row.title)[:45]}": row.prid for row in releases.itertuples()}
        picked = options[st.selectbox("Release", list(options))]
        steps = q("SELECT at, step, status, detail FROM events WHERE prid = ? ORDER BY id", (picked,))
        if steps.empty:
            st.write("Is release pe abhi koi step log nahi hua.")
        for s in steps.itertuples():
            icon = "✅" if s.status == "ok" else "❌"
            st.markdown(f"{icon} **{s.step}** · {s.detail}  \n<small>{s.at}</small>",
                        unsafe_allow_html=True)

st.button("Refresh")
