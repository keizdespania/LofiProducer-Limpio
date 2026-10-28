"""Lector de RSS."""
import requests
import xml.etree.ElementTree as ET

FEEDS = {
    "boe": "https://www.boe.es/rss/boe.php",
    "techcrunch": "https://techcrunch.com/feed/",
    "hackernews": "https://hnrss.org/frontpage",
    "verge": "https://www.theverge.com/rss/index.xml",
}

def leer_feed(fuente="techcrunch", limite=5):
    fuente = fuente.lower()
    if fuente not in FEEDS:
        return "ERROR: Usa: " + ", ".join(FEEDS.keys())
    try:
        r = requests.get(FEEDS[fuente], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = root.findall(".//item")[:limite]
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")[:limite]
        res = ["Feed " + fuente + ":"]
        for it in items:
            title = it.findtext("title") or "?"
            link = it.findtext("link") or ""
            if not link:
                le = it.find("{http://www.w3.org/2005/Atom}link")
                if le is not None:
                    link = le.get("href", "")
            res.append("- " + title + "\n  " + link)
        return "\n".join(res)
    except Exception as e:
        return "ERROR: " + str(e)
