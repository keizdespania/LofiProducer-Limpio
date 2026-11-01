"""scraper_articulos.py v2 - Scrapea TODAS las noticias limpias (no solo top16)."""
import trafilatura, json, pathlib, sys
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
FECHA = sys.argv[1] if len(sys.argv) > 1 else "2026-10-30"

def extraer(url, max_chars=800):
    try:
        html = trafilatura.fetch_url(url)
        if not html: return ""
        texto = trafilatura.extract(html, include_comments=False)
        return texto[:max_chars] if texto else ""
    except Exception:
        return ""

def main():
    # Leer recoleccion_limpia (todas las noticias)
    limpia_path = OUT / f"recoleccion_{FECHA}_limpia.json"
    if not limpia_path.exists():
        limpia_path = OUT / f"recoleccion_{FECHA}.json"
    if not limpia_path.exists():
        print("❌ No hay recoleccion"); sys.exit(1)
    
    datos = json.loads(limpia_path.read_text())
    
    # Recopilar todas las noticias con URL
    items = []
    for sec in ("prensa", "agencias"):
        for medio, noticias in (datos.get(sec) or {}).items():
            for n in noticias:
                if isinstance(n, dict) and n.get("titular") and n.get("url"):
                    items.append({"titular": n["titular"], "url": n["url"], "medio": medio})
    
    print(f"[scraper] Scrapeando {len(items)} noticias (pool completo)...", flush=True)
    urls = [it["url"] for it in items]
    
    with ThreadPoolExecutor(max_workers=8) as ex:
        extractos = list(ex.map(extraer, urls))
    
    for i, it in enumerate(items):
        it["extracto"] = extractos[i]
    
    out = {"fecha": FECHA, "pool": items}
    out_path = OUT / f"recoleccion_{FECHA}_scrapeada.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    ok = sum(1 for e in extractos if e)
    print(f"✅ {ok}/{len(extractos)} noticias con extracto → {out_path.name}")

if __name__ == "__main__":
    main()