# Saari bhashayein ek jagah: English naam, apni lipi mein naam, awaaz hai ya nahi, RTL (daayen se baayen)

ALL = {
    "hi": dict(en="Hindi", native="हिन्दी", voice=True),
    "en": dict(en="English", native="English", voice=True),
    "bn": dict(en="Bengali", native="বাংলা", voice=True),
    "ta": dict(en="Tamil", native="தமிழ்", voice=True),
    "te": dict(en="Telugu", native="తెలుగు", voice=True),
    "mr": dict(en="Marathi", native="मराठी", voice=True),
    "gu": dict(en="Gujarati", native="ગુજરાતી", voice=True),
    "kn": dict(en="Kannada", native="ಕನ್ನಡ", voice=True),
    "ml": dict(en="Malayalam", native="മലയാളം", voice=True),
    "or": dict(en="Odia", native="ଓଡ଼ିଆ", voice=True),
    "pa": dict(en="Punjabi", native="ਪੰਜਾਬੀ", voice=True),
    "as": dict(en="Assamese", native="অসমীয়া"),
    "ur": dict(en="Urdu", native="اردو", rtl=True),
    "ne": dict(en="Nepali", native="नेपाली"),
    "kok": dict(en="Konkani", native="कोंकणी"),
    "mai": dict(en="Maithili", native="मैथिली"),
    "sa": dict(en="Sanskrit", native="संस्कृतम्"),
    "sd": dict(en="Sindhi", native="سنڌي", rtl=True),
    "ks": dict(en="Kashmiri", native="کٲشُر", rtl=True),
    "doi": dict(en="Dogri", native="डोगरी"),
    "brx": dict(en="Bodo", native="बड़ो"),
    "mni": dict(en="Manipuri (Meitei)", native="মণিপুরী"),
    "sat": dict(en="Santali", native="ᱥᱟᱱᱛᱟᱲᱤ"),
}
RTL = {code for code, v in ALL.items() if v.get("rtl")}
