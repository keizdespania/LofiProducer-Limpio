#!/usr/bin/env python3
"""contexto_verificado.py v3 - Contexto neutral SIN DDG.
Fuentes: Wikipedia API (principal) + RSS agencias (EFE/EuropaPress).
Estable, sin rate-limit, sin API key, sin bloqueos.
"""
import urllib.request, urllib.parse, json, re, sys
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# ─── ALIAS: nombre coloquial → nombre oficial (para Wikipedia) ───
ALIAS_MAP = {
    "ley de nietos": "Ley de Memoria Democrática de España",
    "ley nietos": "Ley de Memoria Democrática de España",
    "ley de la memoria": "Ley de Memoria Democrática de España",
    "amnistía": "Ley de Amnistía de España de 2024",
    "ley de amnistía": "Ley de Amnistía de España de 2024",
    "ley trans": "Ley Trans de España",
    "ley del sí es sí": "Ley Orgánica de Garantía Integral de la Libertad Sexual",
    "ley mordaza": "Ley de Seguridad Ciudadana de España",
    "ley beckham": "Régimen fiscal especial de trabajadores desplazados",
    "ley rider": "Ley Rider de España",
    "ley de vivienda": "Ley por el derecho a la vivienda de España",
    "ley de eutanasia": "Ley Orgánica de Regulación de la Eutanasia",
    "ley del aborto": "Ley Orgánica de Salud Sexual y Reproductiva y de la Interrupción Voluntaria del Embarazo",
}

def _normalizar_tema(tema):
    """Normaliza el tema usando alias si existe."""
    t = tema.lower().strip()
    for alias, oficial in ALIAS_MAP.items():
        if alias in t:
            return oficial
    return tema


# ─── WIKIPEDIA API (100% neutral, sin rate-limit) ───
def _wiki_buscar(query, lang="es", max_results=2):
    """Busca en Wikipedia. Devuelve lista de {titulo, extracto, url}."""
    try:
        # Paso 1: buscar título
        search_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&srlimit={max_results}"
        req = urllib.request.Request(search_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        
        results = data.get("query", {}).get("search", [])
        if not results:
            return []
        
        # Paso 2: obtener extracto del primer resultado
        out = []
        for res in results[:max_results]:
            titulo = res["title"]
            extract_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(titulo)}&format=json&exsentences=5"
            req2 = urllib.request.Request(extract_url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req2, timeout=10) as r2:
                d2 = json.loads(r2.read())
            pages = d2.get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                extracto = page.get("extract", "")[:600]
                if extracto:
                    out.append({
                        "titulo": titulo,
                        "extracto": extracto,
                        "url": f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(titulo.replace(' ', '_'))}",
                    })
        return out
    except Exception as e:
        print(f"      ⚠️ Wikipedia: {e}", flush=True)
        return []

# ─── RSS DE AGENCIAS (EFE, EuropaPress, etc.) ───
def _rss_agencias(query, max_results=3):
    """Busca en RSS de agencias. Filtra por keywords del query."""
    RSS_URLS = [
        ("EFE", "https://www.efe.com/efe/espana/portada/rss"),
        ("EuropaPress", "https://www.europapress.es/rss/rss.aspx"),
        
    ]
    
    query_lower = query.lower()
    keywords = [w for w in query_lower.split() if len(w) > 3][:4]
    if not keywords:
        return []
    
    out = []
    for nombre, rss_url in RSS_URLS:
        try:
            req = urllib.request.Request(rss_url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=8) as r:
                xml = r.read().decode("utf-8", errors="ignore")
            
            # Extraer items (título + description)
            items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL)
            for item in items[:50]:
                titulo = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.DOTALL)
                desc = re.search(r'<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', item, re.DOTALL)
                if not titulo: continue
                titulo_txt = titulo.group(1).strip()
                desc_txt = (desc.group(1).strip() if desc else "")[:300]
                
                # Filtrar por keywords
                contenido = (titulo_txt + " " + desc_txt).lower()
                if any(k in contenido for k in keywords):
                    out.append({
                        "fuente": nombre,
                        "titulo": titulo_txt[:150],
                        "snippet": desc_txt,
                    })
                    if len(out) >= max_results:
                        return out
        except Exception as e:
            print(f"      ⚠️ {nombre} RSS: {str(e)[:60]}", flush=True)
            continue
    
    return out

def buscar_contexto(titular, medio, tema):
    """Contexto neutral: Wikipedia + RSS agencias. Sin DDG.
    Devuelve texto plano para el LLM.
    """
    # Normalizar tema (alias → nombre oficial)
    tema_normalizado = _normalizar_tema(tema)
    tema_corto = " ".join(tema_normalizado.split()[:5])
    partes = []
    
    # 1. Wikipedia (background estable, neutral)
    print(f"      🔍 [Wikipedia] {tema_corto}...", flush=True)
    wiki_results = _wiki_buscar(tema_corto, lang="es", max_results=1)
    if wiki_results:
        partes.append("=== CONTEXTO HISTÓRICO (Wikipedia) ===")
        for w in wiki_results:
            partes.append(f"· {w['titulo']}")
            partes.append(f"  {w['extracto']}")
            partes.append(f"  Fuente: {w['url']}")
            partes.append("")
        print(f"      ✅ Wikipedia OK", flush=True)
    else:
        print(f"      ⚠️ Sin Wikipedia", flush=True)
    
    # 2. RSS agencias (actualidad neutral)
    print(f"      🔍 [Agencias RSS] {tema_corto}...", flush=True)
    rss_results = _rss_agencias(tema_corto, max_results=3)
    if rss_results:
        partes.append("=== ACTUALIDAD EN AGENCIAS ===")
        for r in rss_results:
            partes.append(f"· [{r['fuente']}] {r['titulo']}")
            partes.append(f"  {r['snippet']}")
            partes.append("")
        print(f"      ✅ {len(rss_results)} noticias de agencias", flush=True)
    else:
        print(f"      ⚠️ Sin noticias de agencias", flush=True)
    
    return "\n".join(partes) if partes else ""

if __name__ == "__main__":
    titular = sys.argv[1] if len(sys.argv) > 1 else "López Obrador trato preferente nacionalidad"
    medio = sys.argv[2] if len(sys.argv) > 2 else "The Objective"
    tema = sys.argv[3] if len(sys.argv) > 3 else "ley de nietos"
    
    print(f"=== TEST CONTEXTO VERIFICADO v3 ===")
    print(f"Tema: {tema}")
    print()
    
    ctx = buscar_contexto(titular, medio, tema)
    print()
    print(ctx if ctx else "❌ Sin resultados")
