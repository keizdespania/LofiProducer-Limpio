"""scraper_articulos.py - Extrae el texto de los 16 titulares para el guion."""
import trafilatura, json, pathlib, sys
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
FECHA = sys.argv[1] if len(sys.argv) > 1 else "2026-10-30"

def extraer(url):
    try:
        html = trafilatura.fetch_url(url)
        if not html: return ""
        texto = trafilatura.extract(html, include_comments=False)
        # Devolvemos los primeros 800 caracteres (los más jugosos)
        return texto[:800] if texto else ""
    except Exception as e:
        return ""

def main():
    af = OUT / f"analisis_fase1_{FECHA}.json"
    if not af.exists(): print("No hay analisis fase1"); sys.exit(1)
    d = json.loads(af.read_text())
    
    top16 = d.get("top16", [])
    if not top16: print("No hay top16 en analisis"); sys.exit(1)
    
    print(f"[scraper] Extrayendo texto de {len(top16)} articulos...", flush=True)
    urls = [t.get("url") if isinstance(t, dict) else t for t in top16]
    
    with ThreadPoolExecutor(max_workers=8) as ex:
        extractos = list(ex.map(extraer, urls))
        
    for i, t in enumerate(top16):
        if isinstance(t, dict):
            t["extracto"] = extractos[i]
            
    d["top16"] = top16
    af.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    print(f"✅ {sum(1 for e in extractos if e)}/{len(extractos)} articulos enriquecidos con texto")

if __name__ == "__main__":
    main()
