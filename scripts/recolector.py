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
    "Publico": "https://www.publico.es/rss/",
    "La Razon": "https://www.larazon.es/rss/",
    "20 Minutos": "https://www.20minutos.es/rss/",
    "El Periodico": "https://www.elperiodico.com/es/rss/",
    "La Voz de Galicia": "https://www.lavozdegalicia.es/rss/",
    "El Correo": "https://www.elcorreo.com/rss/2.0/portada/",
    "La Verdad": "https://www.laverdad.es/rss/2.0/portada/",
    "Heraldo de Aragon": "https://www.heraldo.es/rss/",
    "Levante-EMV": "https://www.levante-emv.com/rss/",
    "Las Provincias": "https://www.lasprovincias.es/rss/",
    "Diario Sur": "https://www.diariosur.es/rss/",
    "Ideal": "https://www.ideal.es/rss/",
    "La Nueva España": "https://www.lne.es/rss/",
    "El Norte de Castilla": "https://www.elnortedecastilla.es/rss/2.0/portada/",
    "Diario Vasco": "https://www.diariovasco.com/rss/",
    "El Comercio": "https://www.elcomercio.es/rss/",
    "Faro de Vigo": "https://www.farodevigo.es/rss/",
    "La Informacion": "https://www.lainformacion.com/rss/",
    "El Independiente": "https://www.elindependiente.com/feed/",
    "Libertad Digital": "https://rss.libertaddigital.com/",
    "HuffPost Spain": "https://www.huffingtonpost.es/feeds/index.xml",
    "The Local Spain": "https://feeds.thelocal.com/rss/es",
    "Madrid Metropolitan": "https://madridmetropolitan.com/feed/",
    "Euro Weekly News": "https://euroweeklynews.com/feed/",
    "El Diario de Cantabria": "https://www.eldiariocantabria.es/rss/",
    "Ara": "https://www.ara.cat/rss/",
}

# === TV (YouTube) ===
MEDIOS_TV = {
    "RTVE": "https://www.youtube.com/@rtve",
    "Antena 3": "https://www.youtube.com/@antena3",
    "La Sexta": "https://www.youtube.com/@laSexta",
    "Cuatro": "https://www.youtube.com/@cuatro",
    "Telecinco": "https://www.youtube.com/@telecinco",
    "Telemadrid": "https://www.youtube.com/@telemadrid",
    "Trece TV": "https://www.youtube.com/@trecetv",
    "Dmax": "https://www.youtube.com/@dmax",
    "DKISS": "https://www.youtube.com/@dkiss",
    "Ten": "https://www.youtube.com/@ten",
    "TV3": "https://www.youtube.com/@tv3cat",
    "Real Madrid TV": "https://www.youtube.com/@realmadridtv",
    "Negocios TV": "https://www.youtube.com/@NegociosTV",
    "VisualPolitik": "https://www.youtube.com/@VisualPolitik",
    "El Mundo (YT)": "https://www.youtube.com/@elmundo",
}

# === RADIO (YouTube) ===
MEDIOS_RADIO = {
    "Cadena SER": "https://www.youtube.com/@cadenaser",
    "Onda Cero": "https://www.youtube.com/@ondacero",
    "COPE": "https://www.youtube.com/@COPE_es",
    "RNE": "https://www.youtube.com/@RadioNacionaldeEspana",
    "esRadio": "https://www.youtube.com/@esradio",
    "Radio Intereconomia": "https://www.youtube.com/@RadioIntereconomia",
    "Capital Radio": "https://www.youtube.com/@capitalradio",
    "RAC1": "https://www.youtube.com/@rac1",
    "Cadena Dial": "https://www.youtube.com/@cadenadial",
    "Los40": "https://www.youtube.com/@los40",
    "Europa FM": "https://www.youtube.com/@europafm",
    "Rock FM": "https://www.youtube.com/@rockfm",
    "Melodia FM": "https://www.youtube.com/@melodiafm",
    "Radio Marca": "https://www.youtube.com/@radiomarca",
    "The Wild Project": "https://www.youtube.com/@TheWildProject",
}

# === AGENCIAS INTERNACIONALES ===
MEDIOS_AGENCIAS = {
    "EFE": "https://www.efe.com/efe/espana/1/rss",
    "Europa Press": "https://www.europapress.es/rss/rss.aspx",
    "Servimedia": "https://www.servimedia.es/rss/",
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "Associated Press": "https://apnews.com/hub/ap-top-news?format=rss",
    "AFP": "https://www.afp.com/es/rss",
    "Bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
    "DPA": "https://www.dpa.com/de/rss/",
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
