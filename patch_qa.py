def patch(filename, changes):
    with open(filename, encoding="utf-8-sig") as f:
        code = f.read()
    for old, new in changes:
        if new in code:
            print(filename, ": pehle se hai")
        elif code.count(old) == 1:
            code = code.replace(old, new)
            print(filename, ": update ho gaya")
        else:
            print(filename, ": line nahi mili ->", old.strip()[:60])
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)


QA_BLOCK = '''    if isinstance(s, dict):
        with st.form(f"q_{prid}_{lang}", border=False):
            q = st.text_input(L["ask_ph"], key=f"qi_{prid}_{lang}", placeholder=L["ask_ph"],
                              label_visibility="collapsed")
            asked = st.form_submit_button(L["ask"])
        if asked and q.strip():
            with st.spinner(L["thinking"]):
                st.session_state[f"qa_{prid}_{lang}"] = answer_question(prid, q.strip(), lang)
        res = st.session_state.get(f"qa_{prid}_{lang}")
        if res and res.get("ok"):
            nums = ", ".join(str(n) for n, _ in res["paras"])
            quotes = "".join(f'<div style="border-left:3px solid #0E6B50;padding:2px 10px;margin:4px 0;'
                             f'font-size:14px;color:#4A453E">¶{n}: {e(t[:260])}…</div>' for n, t in res["paras"])
            st.markdown(f'<div class="bb-snippet"><b>→</b> {e(res["answer"])}</div>'
                        f'<div class="bb-time">{e(L["source"])} {nums}</div>{quotes}', unsafe_allow_html=True)
        elif res:
            st.info(L["notfound"] if res.get("reason") == "notfound" else L["busy"])
'''

patch("Home.py", [
    ("from hero3d import hero_html\n", "from hero3d import hero_html\nfrom qa import answer_question\n"),
    ("    st.markdown(f'<a class=\"bb-link\" href=\"{e(link)}\" target=\"_blank\">{e(L[\"original\"])} ↗</a>',\n",
     QA_BLOCK + "    st.markdown(f'<a class=\"bb-link\" href=\"{e(link)}\" target=\"_blank\">{e(L[\"original\"])} ↗</a>',\n"),
])

patch("bot.py", [
    ("from alerts import register_alerts\n",
     "from alerts import register_alerts\nfrom qa import answer_question, answer_text_telegram, last_sent_prid\n"),
    ("    await update.message.reply_text(summary_card(title, link, summary),\n",
     "    context.user_data[\"last_prid\"] = prid\n"
     "    await update.message.reply_text(summary_card(title, link, summary),\n"),
    ('async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):\n'
     '    await update.message.reply_text("Main abhi ye samajhta hoon: /khabar, /me, /start")\n',
     'async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):\n'
     '    """Koi bhi likha hua message = aakhri khabar ke baare mein sawaal."""\n'
     '    question = (update.message.text or "").strip()\n'
     '    uid = update.effective_user.id\n'
     '    prid = context.user_data.get("last_prid") or last_sent_prid(uid)\n'
     '    if not prid:\n'
     '        await update.message.reply_text("Pehle /khabar se koi khabar lijiye, phir uske baare mein sawaal poochiye.")\n'
     '        return\n'
     '    row = get_user(uid)\n'
     '    lang = row[2] if row and row[2] else "hi"\n'
     '    await update.message.reply_text("Sawaal mila, khabar mein jawab dhoondh raha hoon...")\n'
     '    res = await asyncio.to_thread(answer_question, prid, question, lang)\n'
     '    await update.message.reply_text(answer_text_telegram(res), parse_mode=ParseMode.HTML,\n'
     '                                    disable_web_page_preview=True)\n'),
])
