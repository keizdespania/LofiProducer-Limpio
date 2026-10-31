import pathlib
"""recolector.py - Radar Global Definitivo (50+ medios, 15 TV, 15 Radio, Agencias)."""
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'brain'))
from especialistas import pedir_a_especialista
import sys, json, pathlib, datetime, re, urllib.request, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime as dt, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre" / "audios"
OUT.mkdir(parents=True, exist_ok=True)

# === PERIÓDICOS Y DIGITALES (Nacionales) ===
MEDIOS_RSS = {
    # Nacionales
    "El Pais": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
    "El Mundo": "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml",
    "ABC": "https://www.abc.es/rss/2.0/portada/",
    "La Vanguardia": "https://www.lavanguardia.com/rss/home.xml",
    "elDiario.es": "https://www.eldiario.es/rss/",
    "El Confidencial": "https://rss.elconfidencial.com/espana/",
    "El Español": "https://www.elespanol.com/rss/",
    "OkDiario": "https://okdiario.com/feed",
    "The Objective": "https://theobjective.com/feed/",
    "HuffPost Spain": "https://www.huffingtonpost.es/feeds/index.xml",
    "20 Minutos": "https://www.20minutos.es/rss/",
    "Ara": "https://www.ara.cat/rss/",
    "El Independiente": "https://www.elindependiente.com/feed/",
    "Público": "https://www.publico.es/rss/",
    "Vozpópuli": "https://www.vozpopuli.com/feed/",
    "Libertad Digital": "https://www.libertaddigital.com/rss/portada.xml",
    "El Salto": "https://www.elsaltodiario.com/feed/",
    "InfoLibre": "https://www.infolibre.es/rss/",
    "El Periódico": "https://www.elperiodico.com/es/rss/rss_portada.xml",
    "La Razón": "https://www.larazon.es/rss/portada.xml",
    # Económicos
    "El Economista": "https://www.eleconomista.es/rss/rss-portada.php",
    "Expansión": "https://e00-expansion.uecdn.es/rss/portada.xml",
    "Cinco Días": "https://cincodias.elpais.com/rss/portada.xml",
    # Regionales
    "La Voz de Galicia": "https://www.lavozdegalicia.es/rss/portada.xml",
    "El Correo": "https://www.elcorreo.com/rss/portada.xml",
    "Faro de Vigo": "https://www.farodevigo.es/rss/portada.xml",
    "La Nueva España": "https://www.lne.es/rss/portada.xml",
    "Heraldo de Aragon": "https://www.heraldo.es/rss/portada.xml",
    "Levante-EMV": "https://www.levante-emv.com/rss/portada.xml",
    "El Norte de Castilla": "https://www.elnortedecastilla.es/rss/portada.xml",
    # Internacionales
    "The Guardian": "https://www.theguardian.com/world/rss",
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Le Monde": "https://www.lemonde.fr/rss/une.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "NYT World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
}

# === TV (YouTube) ===
MEDIOS_TV = {
    "Antena 3": "https://www.youtube.com/@antena3",
    "laSexta": "https://www.youtube.com/@laSexta",
    "Telecinco": "https://www.youtube.com/@telecinco",
    "RTVE": "https://www.youtube.com/@rtve",
    "Negocios TV": "https://www.youtube.com/@NegociosTV",
    "VisualPolitik": "https://www.youtube.com/@VisualPolitik",
    "El Mundo (YT)": "https://www.youtube.com/@elmundo",
    "Wall Street Wolverine": "https://www.youtube.com/@WallStreetWolverine"
}

# === RADIO (YouTube) ===
MEDIOS_RADIO = {
    "Cadena SER": "https://www.youtube.com/@cadenaser",
    "Onda Cero": "https://www.youtube.com/@OndaCero",
    "COPE": "https://www.youtube.com/@COPE",
    "RNE": "https://www.youtube.com/@RadioNacionaldeEspana",
    "EsRadio": "https://www.youtube.com/@esradio"
}

# === AGENCIAS INTERNACIONALES ===
MEDIOS_AGENCIAS = {
    "Europa Press": "https://www.europapress.es/rss/rss.aspx",
    "EFE": "https://www.efe.com/efe/espana/portada/rss.xml",
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "AP News": "https://apnews.com/index.rss",
    "Bloomberg": "https://feeds.bloomberg.com/markets/news.rss"
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
            return videos[:1] # Solo el primero para no tardar demasiado
    except Exception: pass
    return []

def descargar_audio(video_id, nombre_medio):
    if not video_id: return None
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', nombre_medio)
    salida_base = OUT / f"{safe_name}_{video_id}"
    if salida_base.with_suffix('.mp3').exists(): return str(salida_base.with_suffix('.mp3'))
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", str(salida_base), url, "--no-warnings", "--max-filesize", "30M"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and salida_base.with_suffix('.mp3').exists(): return str(salida_base.with_suffix('.mp3'))
    except Exception: pass
    return None

def _rss_safe(medio_url):
    medio, url = medio_url
    try:
        ns = extraer_rss(url, max_n=3)
        return medio, ns
    except Exception as e:
        return medio, []


def _procesar_youtube(medio, url):
    try:
        videos = extraer_youtube(url)
        audios = []
        for v in videos:
            a = descargar_audio(v["id"], medio)
            if a:
                audios.append({"medio": medio, "video_id": v["id"], "titulo": v["titulo"], "audio": a})
        return medio, videos, audios
    except Exception as e:
        print(f"  X {medio}: {e}", flush=True)
        return medio, [], []


def recolectar(rapido=False):
    print(f"[recolector] Iniciando radar global{' (RAPIDO)' if rapido else ''}...", flush=True)
    datos = {"prensa": {}, "tv": {}, "radio": {}, "agencias": {}, "audios": []}

    # 1. Prensa (paralelo)
    print("[recolector] Prensa escrita (paralelo)...", flush=True)
    medios = list(MEDIOS_RSS.items())
    if rapido: medios = medios[:8]
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(_rss_safe, (m,u)): m for m,u in medios}
        for f in as_completed(futs):
            medio, ns = f.result()
            if ns:
                datos["prensa"][medio] = ns
                print(f"  OK {medio}: {len(ns)}", flush=True)

    # 2. TV (paralelo, salvo rapido)
    if not rapido:
        print("\n[recolector] TV (paralelo)...", flush=True)
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = [ex.submit(_procesar_youtube, m, u) for m,u in MEDIOS_TV.items()]
            for f in as_completed(futs):
                medio, vids, auds = f.result()
                if vids:
                    datos["tv"][medio] = vids
                    datos["audios"].extend(auds)
                    print(f"  OK {medio}: {len(vids)} videos, {len(auds)} audios", flush=True)

        # 3. Radio (paralelo)
        print("\n[recolector] Radio (paralelo)...", flush=True)
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = [ex.submit(_procesar_youtube, m, u) for m,u in MEDIOS_RADIO.items()]
            for f in as_completed(futs):
                medio, vids, auds = f.result()
                if vids:
                    datos["radio"][medio] = vids
                    datos["audios"].extend(auds)
                    print(f"  OK {medio}: {len(vids)} videos, {len(auds)} audios", flush=True)

    # 4. Agencias (paralelo)
    print("\n[recolector] Agencias (paralelo)...", flush=True)
    ags = list(MEDIOS_AGENCIAS.items())
    if rapido: ags = ags[:3]
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_rss_safe, (m,u)): m for m,u in ags}
        for f in as_completed(futs):
            medio, ns = f.result()
            if ns:
                datos["agencias"][medio] = ns
                print(f"  OK {medio}: {len(ns)}", flush=True)

    ts = dt.now().strftime("%Y-%m-%d")
    out_json = ROOT / "output" / "encuadre" / f"recoleccion_{ts}.json"
    out_json.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
    print(f"\n[recolector] OK {out_json} ({len(datos['audios'])} audios)", flush=True)


if __name__ == "__main__":
    rapido = "--rapido" in sys.argv
    recolectar(rapido=rapido)
if __name__ == "__main__":
    recolectar()
