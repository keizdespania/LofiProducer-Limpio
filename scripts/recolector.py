"""recolector.py - Radar Global (Nacional + Internacional)."""
import sys, json, pathlib, datetime, re, urllib.request, subprocess
from datetime import datetime as dt, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre" / "audios"
OUT.mkdir(parents=True, exist_ok=True)

# === RADAR NACIONAL (Prensa, TV, Radio, Podcasts, YouTube) ===
MEDIOS_RSS = {
    "El Pais": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
    "El Mundo": "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml",
    "ABC": "https://www.abc.es/rss/2.0/portada/",
    "La Vanguardia": "https://www.lavanguardia.com/rss/home.xml",
    "elDiario.es": "https://www.eldiario.es/rss/",
    "El Confidencial": "https://rss.elconfidencial.com/espana/",
    "El Español": "https://www.elespanol.com/rss/",
    "OkDiario": "https://okdiario.com/feed",
    "Vozpopuli": "https://www.vozpopuli.com/rss/",
    "The Objective": "https://theobjective.com/feed/",
    "Publico": "https://www.publico.es/rss/"
}

MEDIOS_TV = {
    "La Sexta": "https://www.youtube.com/@laSexta",
    "Antena 3": "https://www.youtube.com/@antena3",
    "Telemadrid": "https://www.youtube.com/@telemadrid",
    "Cadena SER": "https://www.youtube.com/@cadenaser",
    "Onda Cero": "https://www.youtube.com/@ondacero",
    "The Wild Project": "https://www.youtube.com/@TheWildProject",
    "RTVE": "https://www.youtube.com/@rtve",
    "COPE": "https://www.youtube.com/@COPE_es",
    "esRadio": "https://www.youtube.com/@esradio",
    "Negocios TV": "https://www.youtube.com/@NegociosTV",
    "El Mundo (YT)": "https://www.youtube.com/@elmundo",
    "El País (YT)": "https://www.youtube.com/@elpais",
    "La Vanguardia (YT)": "https://www.youtube.com/@LaVanguardia",
    "Intereconomia": "https://www.youtube.com/@RadioIntereconomia",
    "VisualPolitik": "https://www.youtube.com/@VisualPolitik",
    "Cuatro": "https://www.youtube.com/@cuatro",
    "Telecinco": "https://www.youtube.com/@telecinco"
}

# === RADAR INTERNACIONAL (Para lunes y jueves) ===
MEDIOS_INTL_RSS = {
    "The Guardian": "https://www.theguardian.com/world/spain/rss",
    "Le Monde": "https://www.lemonde.fr/international/rss_full.xml",
    "BBC": "https://feeds.bbci.co.uk/news/world/europe/rss.xml",
    "Deutsche Welle": "https://rss.dw.com/rdf/rss-en-world",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "Reuters": "https://www.reutersagency.com/feed/?best-topics=politics&post_type=best",
    "AP News": "https://apnews.com/apf-topnews?output=rss"
}

MEDIOS_INTL_YT = {
    "France 24": "https://www.youtube.com/@FRANCE24",
    "DW News": "https://www.youtube.com/@DWNews",
    "Sky News": "https://www.youtube.com/@SkyNews",
    "Al Jazeera English": "https://www.youtube.com/@aljazeeraenglish",
    "Bloomberg TV": "https://www.youtube.com/@markets"
}

def _descargar_html(url, timeout=10):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try: return urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', errors='replace')
    except: return ""

def extraer_rss(url, max_n=3):
    html = _descargar_html(url)
    if not html: return []
    items = re.findall(r'<item.*?</item>', html, re.DOTALL)
    noticias = []
    ayer = dt.now(timezone.utc) - timedelta(days=1)
    for it in items:
        pubdate = re.search(r'<pubDate>(.*?)</pubDate>', it, re.DOTALL)
        if pubdate:
            try:
                from email.utils import parsedate_to_datetime
                if parsedate_to_datetime(pubdate.group(1).strip()) < ayer: continue
            except: pass
        titulo = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', it, re.DOTALL)
        link = re.search(r'<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', it, re.DOTALL)
        if titulo:
            noticias.append({"titular": titulo.group(1).strip(), "url": link.group(1).strip() if link else ""})
        if len(noticias) >= max_n: break
    return noticias

def extraer_youtube(url_canal):
    try:
        cmd = ["yt-dlp", "--flat-playlist", "--print", "%(id)s|%(title)s", "-I", "1:3", url_canal]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if r.returncode == 0 and r.stdout:
            videos = []
            for line in r.stdout.splitlines():
                if "|" in line:
                    partes = line.split("|", 1)
                    if len(partes) == 2: videos.append({"id": partes[0], "titulo": partes[1]})
            return videos[:2]
    except Exception as e: pass
    return []

def descargar_audio(video_id, nombre_medio):
    if not video_id: return None
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', nombre_medio)
    salida_base = OUT / f"{safe_name}_{video_id}"
    if salida_base.with_suffix('.mp3').exists(): return str(salida_base.with_suffix('.mp3'))
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", str(salida_base), url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and salida_base.with_suffix('.mp3').exists(): return str(salida_base.with_suffix('.mp3'))
    except Exception as e: pass
    return None

def recolectar():
    print("[recolector] Recogiendo prensa escrita (Nacional)...", flush=True)
    datos = {"prensa": {}, "tv_radio": {}, "internacional": {}, "audios": []}
    
    for medio, url in MEDIOS_RSS.items():
        noticias = extraer_rss(url)
        if noticias: datos["prensa"][medio] = noticias; print(f"  ✅ {medio}: {len(noticias)}", flush=True)
    
    print("\n[recolector] Recogiendo TV/Radio/Podcast/YouTube (Nacional)...", flush=True)
    for medio, url in MEDIOS_TV.items():
        videos = extraer_youtube(url)
        if videos:
            datos["tv_radio"][medio] = videos
            print(f"  ✅ {medio}: {len(videos)} vídeos", flush=True)
            for v in videos[:1]:
                audio = descargar_audio(v["id"], medio)
                if audio:
                    datos["audios"].append({"medio": medio, "video_id": v["id"], "titulo": v["titulo"], "audio": audio})
                    print(f"     🎙️ Audio descargado", flush=True)
                    
    print("\n[recolector] Recogiendo Internacional...", flush=True)
    for medio, url in MEDIOS_INTL_RSS.items():
        noticias = extraer_rss(url)
        if noticias: datos["internacional"][medio] = noticias; print(f"  ✅ {medio}: {len(noticias)}", flush=True)
        
    for medio, url in MEDIOS_INTL_YT.items():
        videos = extraer_youtube(url)
        if videos:
            datos["internacional"][medio] = videos
            print(f"  ✅ {medio}: {len(videos)} vídeos", flush=True)
    
    ts = dt.now().strftime("%Y-%m-%d")
    out_json = ROOT / "output" / "encuadre" / f"recoleccion_{ts}.json"
    out_json.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
    print(f"\n[recolector] ✅ Guardado en {out_json} ({len(datos['audios'])} audios listos)", flush=True)

if __name__ == "__main__":
    recolectar()
