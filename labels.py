# Website ke UI shabd, har bhasha mein

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


# Lesson 18: sawaal-jawab ke shabd
_QA = {
    "hi": dict(ask_ph="इस खबर के बारे में कुछ पूछें…", ask="पूछें", source="स्रोत: मूल खबर का पैराग्राफ",
               notfound="इस खबर में इसका जवाब नहीं है।", thinking="जवाब ढूंढ रहे हैं…"),
    "en": dict(ask_ph="Ask something about this news…", ask="Ask", source="Source: original release, paragraph",
               notfound="The answer is not in this release.", thinking="Looking for the answer…"),
    "bn": dict(ask_ph="এই খবর সম্পর্কে কিছু জিজ্ঞাসা করুন…", ask="জিজ্ঞাসা করুন", source="সূত্র: মূল খবরের অনুচ্ছেদ",
               notfound="এই খবরে এর উত্তর নেই।", thinking="উত্তর খোঁজা হচ্ছে…"),
    "ta": dict(ask_ph="இந்தச் செய்தி பற்றி ஏதாவது கேளுங்கள்…", ask="கேளுங்கள்", source="ஆதாரம்: மூல செய்தியின் பத்தி",
               notfound="இந்தச் செய்தியில் இதற்கான பதில் இல்லை.", thinking="பதிலைத் தேடுகிறோம்…"),
    "te": dict(ask_ph="ఈ వార్త గురించి ఏదైనా అడగండి…", ask="అడగండి", source="ఆధారం: అసలు వార్తలోని పేరా",
               notfound="ఈ వార్తలో దీనికి సమాధానం లేదు.", thinking="సమాధానం వెతుకుతున్నాం…"),
    "mr": dict(ask_ph="या बातमीबद्दल काहीतरी विचारा…", ask="विचारा", source="स्रोत: मूळ बातमीचा परिच्छेद",
               notfound="या बातमीत याचे उत्तर नाही.", thinking="उत्तर शोधत आहोत…"),
}
for _code, _words in _QA.items():
    LABELS[_code].update(_words)


# Safety: kisi bhasha mein koi shabd na ho to English wala use karo (crash nahi)
for _code in LABELS:
    for _key, _word in LABELS["en"].items():
        LABELS[_code].setdefault(_key, _word)


# Website ke baaki shabd: categories, ticker, 3D heading
CATS = {
    "hi": [("sabhi", "सभी खबरें"), ("student", "छात्र"), ("kisan", "किसान"), ("msme", "दुकान / MSME"), ("mahila", "महिला")],
    "en": [("sabhi", "All news"), ("student", "Students"), ("kisan", "Farmers"), ("msme", "Shops / MSME"), ("mahila", "Women")],
    "bn": [("sabhi", "সব খবর"), ("student", "ছাত্রছাত্রী"), ("kisan", "কৃষক"), ("msme", "দোকান / MSME"), ("mahila", "মহিলা")],
    "ta": [("sabhi", "அனைத்து செய்திகள்"), ("student", "மாணவர்கள்"), ("kisan", "விவசாயிகள்"), ("msme", "கடைகள் / MSME"), ("mahila", "பெண்கள்")],
    "te": [("sabhi", "అన్ని వార్తలు"), ("student", "విద్యార్థులు"), ("kisan", "రైతులు"), ("msme", "దుకాణాలు / MSME"), ("mahila", "మహిళలు")],
    "mr": [("sabhi", "सर्व बातम्या"), ("student", "विद्यार्थी"), ("kisan", "शेतकरी"), ("msme", "दुकान / MSME"), ("mahila", "महिला")],
}
_UI = {
    "hi": dict(hero="आज की बड़ी खबरें", latest="ताज़ा", hint="← घुमाएं · क्लिक करें →"),
    "en": dict(hero="Today's top stories", latest="Latest", hint="← Drag · Click →"),
    "bn": dict(hero="আজকের প্রধান খবর", latest="সর্বশেষ", hint="← ঘোরান · ক্লিক করুন →"),
    "ta": dict(hero="இன்றைய முக்கியச் செய்திகள்", latest="சமீபத்திய", hint="← சுழற்றுங்கள் · கிளிக் செய்யுங்கள் →"),
    "te": dict(hero="నేటి ముఖ్య వార్తలు", latest="తాజా", hint="← తిప్పండి · క్లిక్ చేయండి →"),
    "mr": dict(hero="आजच्या मुख्य बातम्या", latest="ताज्या", hint="← फिरवा · क्लिक करा →"),
}
for _code, _words in _UI.items():
    LABELS[_code].update(_words)

# Safety: kisi bhasha mein koi shabd na ho to English wala (crash nahi)
for _code in LABELS:
    for _key, _word in LABELS["en"].items():
        LABELS[_code].setdefault(_key, _word)


# ---- AI se translate hue UI shabd (make_ui_labels.py) + saari bhashayein dropdown mein ----
import json as _json
import os as _os
from languages import ALL as _ALL_LANGS

if _os.path.exists("ui_labels_auto.json"):
    with open("ui_labels_auto.json", encoding="utf-8") as _f:
        _auto = _json.load(_f)
    for _code, _d in _auto.items():
        LABELS.setdefault(_code, {}).update({k: v for k, v in _d.items() if not k.startswith("cat_")})
        CATS[_code] = [(k, _d.get("cat_" + k, v)) for k, v in CATS["en"]]

LANGS.clear()
for _code, _v in _ALL_LANGS.items():
    if _code in LABELS:
        LANGS[_v["native"]] = _code

for _code in LABELS:
    for _key, _word in LABELS["en"].items():
        LABELS[_code].setdefault(_key, _word)
