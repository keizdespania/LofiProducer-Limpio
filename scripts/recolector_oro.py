"""recolector_oro.py - Saca las 6 noticias top de los medios de la lista blanca."""
import urllib.request, re, json, pathlib, datetime, sys, xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

# Lista de medios de oro (con sus RSS)
MEDIOS_RSS = {
    "El País": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
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
}

def extraer_rss(url, max_n=6):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        xml_data = urllib.request.urlopen(req, timeout=10).read()
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
        noticias = []
        for it in items[:max_n]:
            titulo = it.findtext("title", "").strip()
            link = it.findtext("link", "").strip()
            if titulo and link:
                noticias.append({"titular": titulo, "url": link})
        return noticias
    except Exception as e:
        print(f"Error en {url}: {e}")
        return []

def main():
    print(f"[recolector_oro] Extrayendo noticias top de {len(MEDIOS_RSS)} medios...")
    resultado = {}
    for medio, url in MEDIOS_RSS.items():
        noticias = extraer_rss(url, 6)
        if noticias:
            resultado[medio] = noticias
            print(f"  ✅ {medio}: {len(noticias)} noticias")

    out_file = OUT / f"recoleccion_oro_{FECHA}.json"
    out_file.write_text(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(f"\n✅ Guardadas en {out_file.name}")

if __name__ == "__main__":
    main()
