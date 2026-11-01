# Lesson 23: Bot ki saari baatein, user ki bhasha mein. Jo bhasha yahan nahi, uske liye English.
# Khabar ke card ke labels (Kya hua / Aap pe asar...) labels.py se aate hain (6 bhashayein).

T = {
    "hi": {
        "choose_lang": "🌐 अपनी भाषा चुनें · Choose your language",
        "role_q": "आप कौन हैं? आपके काम की खबरें पहले भेजेंगे 👇",
        "done": "✅ तैयार! नीचे के बटन से सब कुछ होगा:\n\n"
                "📰 आज की खबर: ज़रूरी सरकारी खबर, आसान भाषा और आवाज़ में\n"
                "🌅 3 बड़ी खबरें: एक आवाज़ में तीन खबरें\n"
                "🎙️ सवाल पूछें: माइक दबाकर बोलिए, जवाब आवाज़ में मिलेगा\n\n"
                "हर सुबह 8 बजे 3 बड़ी खबरें खुद आएँगी। पहली खबर आ रही है…",
        "btn_news": "📰 आज की खबर", "btn_digest": "🌅 3 बड़ी खबरें",
        "btn_ask": "🎙️ सवाल पूछें", "btn_settings": "⚙️ सेटिंग",
        "preparing": "⏳ खबर तैयार हो रही है…",
        "no_more": "आज की सारी खबरें आप देख चुके हैं 👍\nनई खबर आते ही हम खुद भेज देंगे। दोबारा शुरू से देखने के लिए 📰 दबाइए।",
        "next": "➡️ अगली खबर", "share": "📤 WhatsApp पर भेजें", "remind": "⏰ {d} को याद दिलाएँ",
        "ask_hint": "🎙️ माइक का बटन दबाकर बोलिए, या लिखिए। आखिरी खबर के बारे में कुछ भी पूछिए।\n\n"
                    "जैसे: «इसका फायदा किसे मिलेगा?» या «आखिरी तारीख क्या है?»",
        "need_news": "पहले 📰 आज की खबर दबाइए, फिर उसके बारे में पूछिए।",
        "heard": "🎙️ आपने पूछा:", "thinking": "🔎 खबर में जवाब ढूँढ रहे हैं…",
        "not_heard": "माफ़ कीजिए, आवाज़ साफ़ नहीं सुनाई दी। फिर से बोलिए या लिखकर पूछिए।",
        "too_long": "कृपया 1 मिनट से छोटा सवाल बोलिए।",
        "source": "📌 मूल खबर में यहाँ लिखा है:",
        "qa_notfound": "इस खबर में इसका जवाब नहीं है।",
        "qa_busy": "अभी जवाब नहीं बन पाया, 1-2 मिनट बाद पूछिए।",
        "qa_verify": "पक्का जवाब नहीं मिला, इसलिए नहीं बता रहे। मूल खबर पढ़ें।",
        "settings": "⚙️ आपकी सेटिंग", "lang": "भाषा", "role": "आप", "digest": "सुबह 8 बजे की खबरें",
        "on": "चालू ✅", "off": "बंद 🔕",
        "set_lang": "🌐 भाषा बदलें", "set_role": "👤 पहचान बदलें", "set_digest": "🌅 सुबह की खबरें चालू/बंद",
        "saved": "✅ सेव हो गया",
        "remind_ok": "⏰ ठीक है! {when} को याद दिलाएँगे। सारे रिमाइंडर: /yaad",
        "fail": "माफ़ कीजिए, यह खबर अभी जाँच में पास नहीं हुई, इसलिए सारांश नहीं भेज रहे। मूल खबर:",
        "share_from": "ऐसी सरकारी खबरें अपनी भाषा में, आवाज़ में, मुफ़्त:",
        "web_cta_title": "Telegram पर पाइए, आवाज़ में",
        "web_cta_sub": "हर सुबह 3 बड़ी खबरें • बोलकर सवाल पूछिए • तारीख का रिमाइंडर • मुफ़्त",
        "web_cta_btn": "Telegram खोलें",
        "voice": "आवाज़", "female": "👩 महिला", "male": "👨 पुरुष", "set_voice": "🗣️ आवाज़ बदलें",
        "voice_hello": "नमस्ते! अब से आपकी खबरें इस आवाज़ में आएँगी।",
    },
    "en": {
        "choose_lang": "🌐 अपनी भाषा चुनें · Choose your language",
        "role_q": "Who are you? We'll send news that matters to you first 👇",
        "done": "✅ All set! Everything works from the buttons below:\n\n"
                "📰 Today's news: key government news, simple words, with voice\n"
                "🌅 Top 3: three stories in one voice note\n"
                "🎙️ Ask: hold the mic and speak, the answer comes back by voice\n\n"
                "Every morning at 8 the top 3 stories arrive on their own. Your first story is coming…",
        "btn_news": "📰 Today's news", "btn_digest": "🌅 Top 3 stories",
        "btn_ask": "🎙️ Ask a question", "btn_settings": "⚙️ Settings",
        "preparing": "⏳ Preparing the news…",
        "no_more": "You've seen all of today's news 👍\nWe'll send new ones as soon as they come. Tap 📰 to start over.",
        "next": "➡️ Next story", "share": "📤 Share on WhatsApp", "remind": "⏰ Remind me on {d}",
        "ask_hint": "🎙️ Hold the mic button and speak, or type. Ask anything about the last story.\n\n"
                    "e.g. «Who benefits from this?» or «What is the last date?»",
        "need_news": "First tap 📰 Today's news, then ask about it.",
        "heard": "🎙️ You asked:", "thinking": "🔎 Looking for the answer in the release…",
        "not_heard": "Sorry, I couldn't hear that clearly. Please speak again or type.",
        "too_long": "Please keep your question under 1 minute.",
        "source": "📌 The original release says:",
        "qa_notfound": "This release doesn't answer that.",
        "qa_busy": "Couldn't answer right now, please ask again in 1-2 minutes.",
        "qa_verify": "No verified answer, so we won't guess. Please read the original.",
        "settings": "⚙️ Your settings", "lang": "Language", "role": "You are", "digest": "8 AM morning news",
        "on": "On ✅", "off": "Off 🔕",
        "set_lang": "🌐 Change language", "set_role": "👤 Change who I am", "set_digest": "🌅 Morning news on/off",
        "saved": "✅ Saved",
        "remind_ok": "⏰ Done! I'll remind you on {when}. All reminders: /yaad",
        "fail": "Sorry, this story didn't pass our fact check, so no summary. Original release:",
        "share_from": "Government news in your language, by voice, free:",
        "web_cta_title": "Get it on Telegram, by voice",
        "web_cta_sub": "Top 3 stories every morning • Ask by speaking • Date reminders • Free",
        "web_cta_btn": "Open Telegram",
        "voice": "Voice", "female": "👩 Female", "male": "👨 Male", "set_voice": "🗣️ Change voice",
        "voice_hello": "Hello! From now on, your news will come in this voice.",
    },
}


try:                                   # baaki bhashayein: make_bot_text.py se bani, check ki hui
    import json as _json
    import os as _os
    _auto = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "bot_text_auto.json")
    if _os.path.exists(_auto):
        for _lang, _texts in _json.load(open(_auto, encoding="utf-8")).items():
            T.setdefault(_lang, {}).update({k: v for k, v in _texts.items() if k not in T.get(_lang, {})})
except Exception as _err:
    print("bot_text_auto.json load nahi hua:", _err)


def t(lang, key, **kw):
    text = T.get(lang, T["en"]).get(key) or T["en"].get(key, key)
    return text.format(**kw) if kw else text
