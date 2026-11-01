# Lesson 5: Verifier - summary ki har tareekh aur number original se check karna

import json
import re
import sys

from summarize import get_release, summarize, LANGUAGES

HINDI_MONTHS = {
    "जनवरी": 1, "फरवरी": 2, "फ़रवरी": 2, "मार्च": 3, "अप्रैल": 4, "मई": 5,
    "जून": 6, "जुलाई": 7, "अगस्त": 8, "सितंबर": 9, "सितम्बर": 9,
    "अक्टूबर": 10, "अक्तूबर": 10, "नवंबर": 11, "नवम्बर": 11,
    "दिसंबर": 12, "दिसम्बर": 12,
}
EN_MONTHS = {
    m: i for i, m in enumerate(
        ["january", "february", "march", "april", "may", "june", "july",
         "august", "september", "october", "november", "december"], start=1)
}
HINDI_NUMBER_WORDS = {
    "एक": "1", "दो": "2", "तीन": "3", "चार": "4", "पांच": "5", "पाँच": "5",
    "छह": "6", "सात": "7", "आठ": "8", "नौ": "9", "दस": "10",
    "ग्यारह": "11", "बारह": "12",
}


def facts_from_original(text):
    """Original text se saari tareekhein (ISO) aur numbers nikalo."""
    text = re.sub(r"(?<=\d),(?=\d)", "", text)      # 2,774 ya 1,25,000 -> bina comma
    dates = set()
    for day, month, year in re.findall(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b", text):
        if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
            dates.add(f"{year}-{int(month):02d}-{int(day):02d}")
            dates.add(f"{int(month):02d}-{int(day):02d}")
    for day, month, year in re.findall(r"(\d{1,2})\s+([^\s\d,।]+)\s*,?\s+(\d{4})", text):
        m = HINDI_MONTHS.get(month) or EN_MONTHS.get(month.lower())
        if m:
            dates.add(f"{year}-{m:02d}-{int(day):02d}")
    for day, month in re.findall(r"(\d{1,2})\s+([^\s\d,।]+)", text):     # "31 अक्टूबर" (bina saal)
        m = HINDI_MONTHS.get(month) or EN_MONTHS.get(month.lower())
        if m and 1 <= int(day) <= 31:
            dates.add(f"{m:02d}-{int(day):02d}")

    numbers = set(re.findall(r"\d+", text))
    for word, digit in HINDI_NUMBER_WORDS.items():
        if re.search(r"(?<!\S)" + word + r"(?!\S)", text):
            numbers.add(digit)
    return dates, numbers


def check(summary, dates, numbers):
    """Summary ki har tareekh aur number original mein hai ya nahi."""
    problems = []
    month_days = {x[-5:] for x in dates}            # bina saal: "10-31"
    for d in summary.get("tareekh_iso", []):
        d = str(d).strip()
        if d in dates:
            continue
        # AI ne saal nahi diya (1900-10-31 / --10-31) ya sirf saal (2026-01-01): din-mahina hi milao
        if d[-5:] in month_days and (d.startswith(("1900", "0000", "-")) or len(d) == 5):
            continue
        if d.endswith("-01-01") and d[:4] in numbers:
            continue
        problems.append(f"date {d} is not in the press release")

    body = " ".join(str(summary.get(k, "")) for k in ("kya_hua", "aap_pe_asar", "kya_karna_hai"))
    body = re.sub(r"(?<=\d),(?=\d)", "", body)

    # Body mein likhi tareekhein (2026-11-03, 03/11/2026, 03.11.2026): original mein hai to theek, number check se hatao
    def _date_ok(m):
        y, mo, d = (m.group(1), m.group(2), m.group(3)) if len(m.group(1)) == 4 else (m.group(3), m.group(2), m.group(1))
        iso = f"{y}-{int(mo):02d}-{int(d):02d}"
        if iso in dates or (iso[5:] in month_days and iso[:4] in numbers):   # saal bhi original mein ho
            return " "
        problems.append(f"date {iso} is not in the press release")
        return " "
    body = re.sub(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", _date_ok, body)
    body = re.sub(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b", _date_ok, body)

    plain = {str(int(x)) for x in numbers if x.isdigit()}          # "03" aur "3" ek hi number
    for n in re.findall(r"\d+", body):
        if n not in numbers and str(int(n)) not in plain:
            problems.append(f"number {n} is not in the press release")
    return problems


def run(lang_code, test_mode=False):
    row = get_release("2330875")
    if not row:
        print("Release DB mein nahi mili.")
        return
    prid, title, text = row
    dates, numbers = facts_from_original(text)
    print("Original ki tareekhein:", sorted(dates))
    print("-" * 50)

    feedback = ""
    for attempt in (1, 2):
        if test_mode and attempt == 1:
            # Jaan-boojh ke galat summary, verifier test karne ke liye
            summary = {"kya_hua": "Chhoot 31 January 2027 tak badhi.",
                       "aap_pe_asar": "", "kya_karna_hai": "",
                       "tareekh_iso": ["2027-01-31"], "sankhya": []}
            print("[TEST] Pehli koshish mein galat summary daali gayi")
        else:
            summary = summarize(title, text + feedback, lang_code)

        if not summary:
            print("Summary nahi bani.")
            return

        problems = check(summary, dates, numbers)
        if not problems:
            print(f"Koshish {attempt}: VERIFIED ✓")
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return

        print(f"Koshish {attempt}: FAIL ✗")
        for p in problems:
            print("   -", p)
        feedback = ("\n\nIMPORTANT: Your previous summary had these errors: "
                    + "; ".join(problems)
                    + ". Rewrite it using ONLY facts from the press release.")

    print("Do baar fail. Ye summary NAHI bheji jaayegi.")


if __name__ == "__main__":
    lang = sys.argv[1] if len(sys.argv) > 1 else "hi"
    run(lang, test_mode="--test" in sys.argv)
