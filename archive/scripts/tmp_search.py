import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

def search(query):
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    results = []
    for link in soup.select('a.result__a')[:10]:
        href = link.get('href')
        text = link.get_text(strip=True)
        results.append((text, href))
    return results

for q in [
    "FieldSearchRequest Bloomberg API",
    "Bloomberg FieldInfoRequest example",
    "blpapi field search excludes",
]:
    print(f"\n### {q}\n")
    for title, href in search(q):
        print(title)
        print(href)
