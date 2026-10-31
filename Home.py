# Website - user friendly: apni bhasha ka UI, progress steps, awaaz upar

import html
import os
from datetime import datetime

import streamlit as st

from alerts import cached_summary, setup_alert_tables
from auto_updater import UPDATE_MINUTES, start_updater_once, update_once
from collector import setup_db as setup_releases
from trace_log import _conn, simulate_pib_down
from voice import text_to_speech, voice_script

st.set_page_config(page_title="BharatBrief", page_icon="📰", layout="centered")
start_updater_once()

# ---------- Look ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Mukta:wght@400;600;700&display=swap');
p, h1, h2, h3, h4, label, li, a, button, input { font-family: 'Mukta', system-ui, sans-serif !important; }
footer { visibility: hidden; }
.bb-hero { background:#0E6B50; color:#fff; border-radius:16px; padding:20px 22px; margin-bottom:14px; }
.bb-hero h1 { color:#fff; font-size:30px; margin:0; padding:0; }
.bb-hero p { color:#fff; margin:4px 0 0; opacity:.92; font-size:17px; }
.bb-badge { display:inline-block; font-size:13px; font-weight:600; padding:2px 10px;
            border-radius:999px; background:#FBEBCB; color:#5A3A00; }
.bb-title { font-size:19px; font-weight:700; line-height:1.45; margin:8px 0 4px; color:#1F1D1A; }
.bb-sum { background:#fff; border:1px solid #DED8CC; border-radius:12px; padding:12px 14px; margin:8px 0; }
.bb-sum h4 { margin:10px 0 2px; font-size:15px; color:#0A4F3B; }
.bb-sum h4:first-child { margin-top:0; }
.bb-sum p { margin:0; font-size:17px; line-height:1.6; color:#1F1D1A; }
.bb-check { font-size:14px; color:#0A4F3B; background:#E4F2EC; border-radius:8px; padding:6px 10px; margin-top:10px; }
.bb-meta { font-size:13.5px; color:#5F5A52; }
</style>
""", unsafe_allow_html=True)

# ---------- Har bhasha ke UI shabd ----------
LABELS = {
    "hi": dict(tagline="सरकारी खबरें, आपकी भाषा में, आसान शब्दों में।", kya="क्या हुआ", asar="आप पर असर",
               karna="आपको क्या करना है", explain="आसान भाषा में समझाएं", original="मूल खबर पढ़ें (PIB)",
               checked="✓ हर संख्या और तारीख मूल खबर से जांची गई", working="खबर तैयार हो रही है…",
               s1="खबर पढ़कर आसान भाषा में लिख रहे हैं", s2="हर संख्या और तारीख जांच ली", s3="आवाज़ बना रहे हैं",
               done="तैयार है", busy="अभी AI व्यस्त है। 1-2 मिनट बाद फिर कोशिश करें।",
               verify="इस खबर का सारांश जांच में पास नहीं हुआ, इसलिए नहीं दिखा रहे। कृपया मूल खबर पढ़ें।",
               retry="फिर कोशिश करें", none="अभी आपके लिए कोई नई खबर नहीं है।", last="आखिरी अपडेट",
               auto="हर {m} मिनट में अपने आप अपडेट", update="अभी अपडेट करें", listen="🔊 सुनें (AI आवाज़)",
               down="PIB अभी उपलब्ध नहीं है। पिछली खबरें दिख रही हैं।"),
    "en": dict(tagline="Government news in your language, in simple words.", kya="What happened",
               asar="How it affects you", karna="What you should do", explain="Explain in simple words",
               original="Read the original (PIB)", checked="✓ Every number and date checked against the original",
               working="Preparing the news…", s1="Reading the release and writing it simply",
               s2="Checked every number and date", s3="Creating the voice", done="Ready",
               busy="The AI is busy right now. Please try again in 1-2 minutes.",
               verify="This summary did not pass our checks, so we are not showing it. Please read the original.",
               retry="Try again", none="No new news for you right now.", last="Last updated",
               auto="Updates automatically every {m} min", update="Update now", listen="🔊 Listen (AI voice)",
               down="PIB is not available right now. Showing earlier news."),
    "bn": dict(tagline="সরকারি খবর, আপনার ভাষায়, সহজ কথায়।", kya="কী হয়েছে", asar="আপনার উপর প্রভাব",
               karna="আপনার কী করণীয়", explain="সহজ ভাষায় বুঝিয়ে দিন", original="মূল খবর পড়ুন (PIB)",
               checked="✓ প্রতিটি সংখ্যা ও তারিখ মূল খবরের সাথে মিলিয়ে দেখা হয়েছে", working="খবর তৈরি হচ্ছে…",
               s1="খবর পড়ে সহজ ভাষায় লেখা হচ্ছে", s2="প্রতিটি সংখ্যা ও তারিখ যাচাই হয়েছে", s3="কণ্ঠস্বর তৈরি হচ্ছে",
               done="তৈরি", busy="AI এখন ব্যস্ত। 1-2 মিনিট পরে আবার চেষ্টা করুন।",
               verify="এই সারাংশ যাচাইয়ে পাস করেনি, তাই দেখানো হচ্ছে না। মূল খবর পড়ুন।",
               retry="আবার চেষ্টা করুন", none="এখন আপনার জন্য নতুন খবর নেই।", last="শেষ আপডেট",
               auto="প্রতি {m} মিনিটে নিজে থেকে আপডেট", update="এখনই আপডেট করুন", listen="🔊 শুনুন (AI কণ্ঠ)",
               down="PIB এখন পাওয়া যাচ্ছে না। আগের খবর দেখানো হচ্ছে।"),
    "ta": dict(tagline="அரசு செய்திகள், உங்கள் மொழியில், எளிய வார்த்தைகளில்.", kya="என்ன நடந்தது",
               asar="உங்களுக்கு என்ன பாதிப்பு", karna="நீங்கள் என்ன செய்ய வேண்டும்",
               explain="எளிய மொழியில் விளக்குங்கள்", original="மூல செய்தியைப் படிக்கவும் (PIB)",
               checked="✓ ஒவ்வொரு எண்ணும் தேதியும் மூல செய்தியுடன் சரிபார்க்கப்பட்டது",
               working="செய்தி தயாராகிறது…", s1="செய்தியைப் படித்து எளிமையாக எழுதுகிறோம்",
               s2="ஒவ்வொரு எண்ணும் தேதியும் சரிபார்க்கப்பட்டது", s3="குரல் உருவாக்குகிறோம்", done="தயார்",
               busy="AI இப்போது பிஸியாக உள்ளது. 1-2 நிமிடங்களில் மீண்டும் முயற்சிக்கவும்.",
               verify="இந்தச் சுருக்கம் சரிபார்ப்பில் தேறவில்லை, அதனால் காட்டவில்லை. மூல செய்தியைப் படிக்கவும்.",
               retry="மீண்டும் முயற்சிக்கவும்", none="இப்போது உங்களுக்கு புதிய செய்தி இல்லை.",
               last="கடைசி புதுப்பிப்பு", auto="ஒவ்வொரு {m} நிமிடத்திற்கும் தானாக புதுப்பிக்கப்படும்",
               update="இப்போது புதுப்பிக்கவும்", listen="🔊 கேளுங்கள் (AI குரல்)",
               down="PIB இப்போது கிடைக்கவில்லை. முந்தைய செய்திகள் காட்டப்படுகின்றன."),
    "te": dict(tagline="ప్రభుత్వ వార్తలు, మీ భాషలో, సులభమైన మాటల్లో.", kya="ఏం జరిగింది", asar="మీపై ప్రభావం",
               karna="మీరు ఏం చేయాలి", explain="సులభమైన భాషలో వివరించండి", original="అసలు వార్త చదవండి (PIB)",
               checked="✓ ప్రతి సంఖ్య, తేదీ అసలు వార్తతో సరిచూడబడింది", working="వార్త సిద్ధమవుతోంది…",
               s1="వార్త చదివి సులభంగా రాస్తున్నాం", s2="ప్రతి సంఖ్య, తేదీ సరిచూశాం", s3="వాయిస్ తయారు చేస్తున్నాం",
               done="సిద్ధం", busy="AI ప్రస్తుతం బిజీగా ఉంది. 1-2 నిమిషాల తర్వాత మళ్లీ ప్రయత్నించండి.",
               verify="ఈ సారాంశం తనిఖీలో పాస్ కాలేదు, అందుకే చూపడం లేదు. అసలు వార్త చదవండి.",
               retry="మళ్లీ ప్రయత్నించండి", none="ప్రస్తుతం మీకోసం కొత్త వార్తలు లేవు.", last="చివరి అప్‌డేట్",
               auto="ప్రతి {m} నిమిషాలకు ఆటోమేటిక్‌గా అప్‌డేట్", update="ఇప్పుడే అప్‌డేట్ చేయండి",
               listen="🔊 వినండి (AI వాయిస్)", down="PIB ప్రస్తుతం అందుబాటులో లేదు. పాత వార్తలు చూపిస్తున్నాం."),
    "mr": dict(tagline="सरकारी बातम्या, तुमच्या भाषेत, सोप्या शब्दांत.", kya="काय झाले", asar="तुमच्यावर परिणाम",
               karna="तुम्ही काय करावे", explain="सोप्या भाषेत समजावून सांगा", original="मूळ बातमी वाचा (PIB)",
               checked="✓ प्रत्येक आकडा आणि तारीख मूळ बातमीशी तपासली", working="बातमी तयार होत आहे…",
               s1="बातमी वाचून सोप्या भाषेत लिहित आहोत", s2="प्रत्येक आकडा आणि तारीख तपासली", s3="आवाज तयार करत आहोत",
               done="तयार", busy="AI सध्या व्यस्त आहे. 1-2 मिनिटांनी पुन्हा प्रयत्न करा.",
               verify="हा सारांश तपासणीत पास झाला नाही, म्हणून दाखवत नाही. कृपया मूळ बातमी वाचा.",
               retry="पुन्हा प्रयत्न करा", none="सध्या तुमच्यासाठी नवीन बातमी नाही.", last="शेवटचे अपडेट",
               auto="दर {m} मिनिटांनी आपोआप अपडेट", update="आत्ता अपडेट करा", listen="🔊 ऐका (AI आवाज)",
               down="PIB सध्या उपलब्ध नाही. आधीच्या बातम्या दिसत आहेत."),
}

LANGS = {"हिन्दी": "hi", "English": "en", "বাংলা": "bn", "தமிழ்": "ta", "తెలుగు": "te", "मराठी": "mr"}
ROLES = {"सभी खबरें · All": "sabhi", "छात्र · Student": "student", "किसान · Farmer": "kisan",
         "दुकान / MSME": "msme", "महिला · Women": "mahila"}
AUDIENCE = {"sabhi": "सबके लिए · Everyone", "student": "छात्र · Students", "kisan": "किसान · Farmers",
            "msme": "MSME · दुकान", "mahila": "महिला · Women"}


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


def fail_kind(prid):
    conn = _conn()
    row = conn.execute("SELECT step FROM events WHERE prid = ? AND status = 'fail' "
                       "ORDER BY id DESC LIMIT 1", (prid,)).fetchone()
    conn.close()
    return "verify" if row and row[0] == "verify" else "busy"


def summary_html(s, L):
    e = html.escape
    return (f'<div class="bb-sum">'
            f'<h4>{e(L["kya"])}</h4><p>{e(str(s.get("kya_hua", "")))}</p>'
            f'<h4>{e(L["asar"])}</h4><p>{e(str(s.get("aap_pe_asar", "")))}</p>'
            f'<h4>{e(L["karna"])}</h4><p>{e(str(s.get("kya_karna_hai", "")))}</p>'
            f'<div class="bb-check">{e(L["checked"])}</div></div>')


# ---------- Page ----------
c1, c2 = st.columns(2)
lang = LANGS[c1.selectbox("भाषा · Language", list(LANGS))]
role = ROLES[c2.selectbox("आप कौन हैं · Who are you", list(ROLES))]
L = LABELS[lang]

st.markdown(f'<div class="bb-hero"><h1>BharatBrief</h1><p>{html.escape(L["tagline"])}</p></div>',
            unsafe_allow_html=True)


@st.fragment(run_every=120)
def news_list(lang, role, L):
    if simulate_pib_down():
        st.warning(L["down"])

    top_l, top_r = st.columns([3, 1])
    last = last_fetch_time()
    top_l.markdown(f'<div class="bb-meta">{html.escape(L["last"])}: '
                   f'{last:%d %b, %H:%M}' if last else '<div class="bb-meta">…', unsafe_allow_html=True)
    top_l.markdown(f'<div class="bb-meta">{html.escape(L["auto"].format(m=UPDATE_MINUTES))}</div>',
                   unsafe_allow_html=True)
    if top_r.button(L["update"], use_container_width=True):
        with st.spinner(L["working"]):
            update_once()
        st.rerun()

    shown = 0
    for prid, title, link, audience in latest_releases():
        if role != "sabhi" and audience not in (None, role, "sabhi"):
            continue
        shown += 1

        with st.container(border=True):
            badge = AUDIENCE.get(audience or "", "")
            st.markdown((f'<span class="bb-badge">{html.escape(badge)}</span>' if badge else "")
                        + f'<div class="bb-title">{html.escape(title)}</div>', unsafe_allow_html=True)

            key, akey = f"s_{prid}_{lang}", f"a_{prid}_{lang}"
            if key not in st.session_state:
                if st.button(L["explain"], key=f"b_{prid}_{lang}", type="primary", use_container_width=True):
                    with st.status(L["working"], expanded=True) as status:
                        st.write("1. " + L["s1"])
                        s = get_summary(prid, lang)
                        if s:
                            st.write("2. " + L["s2"] + " ✓")
                            st.write("3. " + L["s3"])
                            st.session_state[akey] = get_audio(prid, lang, s)
                            status.update(label=L["done"], state="complete", expanded=False)
                        else:
                            status.update(label=L["retry"], state="error", expanded=False)
                    st.session_state[key] = s or "fail"
                    st.rerun()

            s = st.session_state.get(key)
            if s == "fail":
                st.info(L[fail_kind(prid)])
                if st.button(L["retry"], key=f"r_{prid}_{lang}", use_container_width=True):
                    del st.session_state[key]
                    st.rerun()
            elif s:
                if st.session_state.get(akey):
                    st.markdown(f'<div class="bb-meta">{html.escape(L["listen"])}</div>', unsafe_allow_html=True)
                    st.audio(st.session_state[akey])
                st.markdown(summary_html(s, L), unsafe_allow_html=True)

            st.link_button(L["original"], link, use_container_width=True)

    if shown == 0:
        st.info(L["none"])


news_list(lang, role, L)
