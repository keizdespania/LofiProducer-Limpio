"""analista_fase1.py - Análisis con Editor Jefe y Bucle de Investigación Infinito."""
import sys, json, pathlib, datetime, re, time, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def _parse_json(texto):
    if not texto: return {}
    t = re.sub(r'```(?:json)?', '', texto, flags=re.I).replace('```', '').strip()
    try: return json.loads(t)
    except: pass
    for m in sorted(re.findall(r'\{.*?\}', texto, re.DOTALL), key=len, reverse=True):
        try: return json.loads(m)
        except: pass
    return {}

def _procesar_medio(medio, datos, noticia):
    textos = []
    for sec in ("prensa", "agencias"):
        for n in (datos.get(sec) or {}).get(medio, []):
            if isinstance(n, dict) and n.get("titular"): textos.append(n["titular"])
    for sec in ("tv", "radio"):
        for v in (datos.get(sec) or {}).get(medio, []):
            if isinstance(v, dict) and v.get("titulo"): textos.append(v["titulo"])
    
    if not textos: return None
    ctx = f"MEDIO: {medio}\nTITULARES:\n" + "\n".join(textos[:3])
    
    r = pedir_a_especialista("forense_medios", f"Analiza el sesgo de {medio} sobre: {noticia}. Devuelve SOLO JSON.", contexto=ctx[:800], proveedor="auto")
    an = _parse_json(r)
    if not an: return None
    return an

def analizar_fase1(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    rec_json = OUT / f"recoleccion_{fecha}_limpia.json"
    if not rec_json.exists(): rec_json = OUT / f"recoleccion_{fecha}.json"
    if not rec_json.exists(): return None
    datos = json.loads(rec_json.read_text())
    
    # Cargar scrapeado (extractos) si existe
    scrapeada_path = OUT / f"recoleccion_{fecha}_scrapeada.json"
    scrapeado_map = {}
    if scrapeada_path.exists():
        try:
            scr_data = json.loads(scrapeada_path.read_text())
            for item in scr_data.get("pool", []):
                scrapeado_map[item["titular"]] = item.get("extracto", "")
        except: pass

    # 1. DETECTIVE: Top3
    print("[fase1] Detectando Top 3...", flush=True)
    ctx = "TITULARES:\n"
    for medio, noticias in (datos.get("prensa") or {}).items():
        ctx += f"[{medio}]\n"
        for n in noticias:
            if isinstance(n, dict): ctx += f"- {n.get('titular','')}\n"
    prompt_top3 = 'Devuelve SOLO JSON: {"top3": ["noticia 1", "noticia 2", "noticia 3"]}.'
    top3 = _parse_json(pedir_a_especialista("detective_tendencias_v2", prompt_top3, contexto=ctx[:5000], proveedor="auto")).get("top3", ["Actualidad", "Política", "Economía"])

    # 2. EDITOR JEFE (Aprobación garantizada por Python)
    print("[fase1] Llamando al Editor Jefe...", flush=True)
    top16 = []
    vistos = set()
    
    # Recopilar todas las noticias
    pool_noticias = []
    for sec in ("prensa", "agencias"):
        for medio, noticias in (datos.get(sec) or {}).items():
            for n in noticias:
                if isinstance(n, dict) and n.get("titular") and n["titular"] not in vistos:
                    extracto = scrapeado_map.get(n["titular"], "")
                    pool_noticias.append({"titular": n["titular"], "url": n.get("url",""), "medio": medio, "extracto": extracto})
                    vistos.add(n["titular"])

    # Editor Jefe V2 (4 capas: pre-filtro + scoring + LLM rubrica + validacion/fallback)
    print(f"[fase1] Editor Jefe v2. Pool: {len(pool_noticias)} noticias.", flush=True)
    from editor_jefe_v2 import _editor_jefe_v2
    def _pedir_llm(rol, prompt, contexto="", proveedor="auto"):
        return pedir_a_especialista(rol, prompt, contexto=contexto, proveedor=proveedor)
    top16 = _editor_jefe_v2(pool_noticias, _pedir_llm, verbose=True)
    print(f"[fase1] Top16 final: {len(top16)} noticias.", flush=True)

    # 3. ANÁLISIS DE MEDIOS
    print("[fase1] Analizando medios...", flush=True)
    medios = list((datos.get("prensa") or {}).keys()) + list((datos.get("agencias") or {}).keys()) + list((datos.get("tv") or {}).keys()) + list((datos.get("radio") or {}).keys())
    noticia = top3[0] if top3 else "noticias del día"

    todos = {}
    total = len(medios)
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_procesar_medio, m, datos, noticia): m for m in medios}
        for completados, f in enumerate(as_completed(futs), 1):
            try:
                medio, an = futs[f], f.result()
                if an: todos[medio] = [an]
                print(f"  [{completados}/{total}] {'OK' if an else '--'} {medio}", flush=True)
            except: pass

    # 4. GUARDAR
    top3_dict = {f"noticia_{i+1}": n for i, n in enumerate(top3)}
    res = {"fecha": fecha, "top3": top3_dict, "top16": top16, "analisis": todos, "recoleccion": datos}
    (OUT / f"analisis_fase1_{fecha}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase1] ✅ Guardado. Top16: {len(top16)} noticias.", flush=True)

if __name__ == "__main__":
    analizar_fase1(sys.argv[1] if len(sys.argv) > 1 else None)
