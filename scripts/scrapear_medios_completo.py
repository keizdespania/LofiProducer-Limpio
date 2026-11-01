"""scrapear_medios_completo.py - Scrapea texto COMPLETO de cada medio del desglose."""
import sys, json, pathlib, datetime, re
import trafilatura
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

def _extraer_texto(url, max_chars=4000):
    """Extrae el texto completo de una URL."""
    try:
        html = trafilatura.fetch_url(url)
        if not html: return ""
        texto = trafilatura.extract(html, include_comments=False, include_tables=False)
        if not texto: return ""
        # Limpiar
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto[:max_chars]
    except Exception as e:
        return ""

def _urls_por_medio(fecha):
    """Extrae {medio: {titular, url}} de recoleccion."""
    rec_path = OUT / f"recoleccion_{fecha}.json"
    if not rec_path.exists(): return {}
    rec = json.loads(rec_path.read_text())
    medios = {}
    for cat, items in rec.items():
        if cat == "audios": continue
        if isinstance(items, dict):
            for medio, noticias in items.items():
                if isinstance(noticias, list):
                    for n in noticias:
                        if isinstance(n, dict) and n.get("url"):
                            medios[medio] = {
                                "titular": n.get("titular", ""),
                                "url": n["url"],
                                "categoria": cat,
                            }
                            break
    return medios

def _medios_del_desglose(fecha):
    """Nombres de medios en el desglose_medios."""
    enr = OUT / f"dossier_{fecha}_enriquecido.json"
    d_path = enr if enr.exists() else (OUT / f"dossier_{fecha}.json")
    if not d_path.exists(): return set()
    d = json.loads(d_path.read_text())
    desglose = d.get("dossier", {}).get("desglose_medios", "")
    medios = set()
    for line in desglose.split("\n"):
        m = re.match(r"\*\*([^*]+)\*\*", line)
        if m: medios.add(m.group(1).strip())
    return medios

def main(fecha=None):
    fecha = fecha or FECHA
    print(f"Scrapeando medios completos para {fecha}...")
    print("=" * 60)
    
    urls_por_medio = _urls_por_medio(fecha)
    medios_desglose = _medios_del_desglose(fecha)
    
    print(f"Medios con URL en recoleccion: {len(urls_por_medio)}")
    print(f"Medios en desglose: {len(medios_desglose)}")
    print()
    
    # Filtrar solo medios del desglose que tengan URL
    a_scrapear = []
    for medio in medios_desglose:
        if medio in urls_por_medio:
            a_scrapear.append((medio, urls_por_medio[medio]))
    
    print(f"Medios a scrapear (desglose + URL): {len(a_scrapear)}")
    for medio, info in a_scrapear:
        print(f"  - {medio}: {info['url'][:60]}...")
    print()
    
    if not a_scrapear:
        print("❌ No hay medios para scrapear")
        return False
    
    # Scrapear en paralelo
    print("Scrapeando en paralelo (8 workers)...")
    def scrapear(item):
        medio, info = item
        print(f"  ⬇️  {medio}...", end=" ", flush=True)
        texto = _extraer_texto(info["url"])
        if texto:
            print(f"✅ {len(texto)} chars")
        else:
            print(f"❌ vacío")
        return medio, {
            "titular": info["titular"],
            "url": info["url"],
            "categoria": info["categoria"],
            "texto_completo": texto,
            "chars": len(texto),
        }
    
    with ThreadPoolExecutor(max_workers=8) as ex:
        resultados = dict(ex.map(scrapear, a_scrapear))
    
    # Guardar
    out_path = OUT / f"scrapeado_{fecha}.json"
    out_path.write_text(json.dumps(resultados, indent=2, ensure_ascii=False))
    
    total_ok = sum(1 for r in resultados.values() if r["chars"] > 100)
    print()
    print("=" * 60)
    print(f"✅ Guardado: {out_path}")
    print(f"   {total_ok}/{len(resultados)} medios con texto real")
    print(f"   Total chars: {sum(r['chars'] for r in resultados.values())}")
    
    return True

if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1] if len(sys.argv) > 1 else None) else 1)
