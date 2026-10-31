# Lesson 2: Release page se pura text nikalna

import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

LINK = "https://pib.gov.in/PressReleaseIframePage.aspx?PRID=2330875"


def get_prid(link):
    """Link se PRID number nikalta hai. Na mile to None."""
    match = re.search(r"PRID=(\d+)", link)
    return match.group(1) if match else None


def fetch_text(link):
    try:
        resp = requests.get(link, headers=HEADERS, timeout=15)
    except requests.RequestException as err:
        print("Network problem:", err)
        return ""

    if resp.status_code != 200:
        print("Page nahi mila, status:", resp.status_code)
        return ""

    soup = BeautifulSoup(resp.content, "html.parser")

    # Har <p> ka text lo; chhote aur dohraaye gaye paragraphs chhod do
    paras, seen = [], set()
    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if len(text) > 40 and text not in seen:
            seen.add(text)
            paras.append(text)

    return "\n\n".join(paras)


def main():
    print("PRID:", get_prid(LINK))
    text = fetch_text(LINK)
    print("Kitne akshar mile:", len(text))
    print("-" * 50)
    print(text[:1500])


if __name__ == "__main__":
    main()
