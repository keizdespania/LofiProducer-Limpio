#!/usr/bin/env python3
"""contexto_verificado.py - 1 query DDG a 6 fuentes oficiales + Wikipedia fallback.
Extrae 2-3 snippets con contexto neutral para el monólogo."""
import urllib.request, urllib.parse, re, html

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

FUENTES_OFICIALES = "site:efe.com OR site:reuters.com OR site:apnews.com OR site:europapress.es OR site:boe.es OR site:ine.es"

def _ddg(q, max_r=3, timeout=12):
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(q)}"
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "es-ES,es;q=0.9"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8", errors="ignore")
        bloques = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            txt, re.DOTALL
        )
        out = []
        for url_res, tit, snip in bloques[:max_r]:
            tit = re.sub(r'<[^>]+>', '', html.unescape(tit)).strip()[:150]
            snip = re.sub(r'<[^>]+>', '', html.unescape(snip)).strip()[:300]
            out.append({"titulo": tit, "snippet": snip})
        return out
    except Exception:
        return []

def buscar_contexto(titular, medio, tema=None):
    """1 query a fuentes oficiales + fallback Wikipedia."""
    if not tema:
        # Extraer tema del titular (primeras 6 palabras significativas)
        palabras = [w for w in titular.split() if len(w) > 3 and w[0].isupper()]
        tema = " ".join(palabras[:4]) or titular[:60]
    
    print(f"    🔍 Contexto: '{tema[:50]}...'", flush=True)
    
    # Query 1: Fuentes oficiales
    resultados = _ddg(f'"{tema}" ({FUENTES_OFICIALES})', max_r=3)
    
    # Fallback: Wikipedia
    if not resultados:
        print(f"    ⚠️ Sin fuentes oficiales, fallback a Wikipedia", flush=True)
        resultados = _ddg(f"{tema} wikipedia", max_r=2)
    
    if not resultados:
        return ""
    
    lineas = []
    for r in resultados:
        lineas.append(f"· {r['titulo']}")
        if r['snippet']:
            lineas.append(f"  {r['snippet']}")
    
    return "\n".join(lineas)

if __name__ == "__main__":
    import sys
    titular = sys.argv[1] if len(sys.argv) > 1 else "mujer López Obrador trato preferente nacionalidad"
    medio = sys.argv[2] if len(sys.argv) > 2 else "The Objective"
    print(f"=== TEST CONTEXTO VERIFICADO ===")
    print(f"Titular: {titular[:80]}")
    print()
    ctx = buscar_contexto(titular, medio)
    print(ctx)
