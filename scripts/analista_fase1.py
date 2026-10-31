"""analista_fase1.py - Analiza medios, extrae Top3 (blog) y Top16 (video)."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

# ─── LISTA NEGRA (ADUANA) ───
BASURA = [
    "balón", "balon", "mbappé", "blocus", "futbol", "fútbol", "pucela", "racing", "athletic", "real madrid", "barça",
    "muere", "muerte", "fallece", "fallecimiento", "suicidio", "accidente", "detenido", "detenida", "policía", "policia", "guardia civil", 
    "intocable", "cine", "cineasta", "película", "pelicula", "actor", "actriz", "prensa rosa", "corazón", "corazon", "boda", "divorcio",
    "bustamante", "triguero", "concierto", "música", "musica", "alcalá norte", "dgt", "tráfico", "trafico", "tiempo", "lluvia", "temperatura",
    "urda", "toledo", "tren", "ave", "adif", "renfe", "señaliz", "lzb", "herid", "cuerpo", "desaparecid", "morgue", "llanto"
]

def _parse_json(texto):
    if not texto: return {}
    t = re.sub(r'```(?:json)?', '', texto, flags=re.I).replace('```', '').strip()
    try: return json.loads(t)
    except: pass
    for m in sorted(re.findall(r'\{.*?\}', texto, re.DOTALL), key=len, reverse=True):
        try: return json.loads(m)
        except: pass
    return {}

def _filtrar_basura(noticias):
    """Recibe una lista de dicts y devuelve las 16 mejores sin basura."""
    limpias = []
    vistos = set()
    for n in noticias:
        if not isinstance(n, dict): continue
        tit = n.get("titular", "").lower()
        if any(b in tit for b in BASURA): continue
        if tit in vistos: continue
        vistos.add(tit)
        limpias.append(n)
        if len(limpias) >= 16: break
    return limpias

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
    
    r = pedir_a_especialista("forense_medios",
        f"Analiza el sesgo de {medio} sobre: {noticia}. Devuelve SOLO JSON con: nombre, titular_real, titular_traducido, imd_local, framing, palabra_cuchillo, tecnica_principal, omision.",
        contexto=ctx[:800], proveedor="auto")
    an = _parse_json(r)
    if not an: return None
    
    time.sleep(1)
    r_emo = pedir_a_especialista("analista_emocional", f"Analiza emociones de {medio}", contexto=ctx[:2000], proveedor="auto")
    emo = _parse_json(r_emo)
    if emo: an["emociones"] = emo
    
    time.sleep(1)
    r_ses = pedir_a_especialista("detector_sesgos_cognitivos", f"Detecta sesgos en {medio}", contexto=ctx[:2000], proveedor="auto")
    ses = _parse_json(r_ses)
    if ses: an["sesgos_cognitivos"] = ses
    return an

def analizar_fase1(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    rec_json = OUT / f"recoleccion_{fecha}_limpia.json"
    if not rec_json.exists(): rec_json = OUT / f"recoleccion_{fecha}.json"
    if not rec_json.exists():
        print(f"❌ No existe {rec_json}"); return None
    
    print(f"[fase1] leyendo {rec_json.name}", flush=True)
    datos = json.loads(rec_json.read_text())

    # 1. DETECTIVE: Pedir Top3 + Top40
    print("[fase1] Detectando Top 3 y Top 40 (materia prima)...", flush=True)
    ctx = "TITULARES Y URLS:\n"
    for medio, noticias in (datos.get("prensa") or {}).items():
        ctx += f"\n[{medio}]\n"
        for n in noticias:
            if isinstance(n, dict): ctx += f"- {n.get('titular','')} (URL: {n.get('url','')})\n"

    prompt_det = """Devuelve SOLO JSON: 
{"top3": ["noticia 1", "noticia 2", "noticia 3"], 
 "top40": [{"titular": "titular 1", "url": "https://...", "medio": "El Pais"}, ... 40 items]}
Usa los titulares y URLs del contexto. Descarta tragedias y deportes."""
    
    top_data = _parse_json(pedir_a_especialista("detective_tendencias_v2", prompt_det, contexto=ctx[:5000], proveedor="auto"))
    
    top3 = top_data.get("top3", {"noticia_1": "Actualidad", "noticia_2": "Política", "noticia_3": "Economía"})
    top40 = top_data.get("top40", [])
    
    # 2. ADUANA: Filtrar la basura de las 40 noticias y quedarnos con 16
    top16 = _filtrar_basura(top40)
    
    # Si el LLM ha fallado y no hay 16, sacamos de la recolección directamente
    if len(top16) < 10:
        print("[fase1] ⚠️ Pocas noticias del LLM. Usando fallback de recolección...", flush=True)
        fallback = []
        for sec in ("prensa", "agencias"):
            for medio, noticias in (datos.get(sec) or {}).items():
                for n in noticias:
                    if isinstance(n, dict) and n.get("titular"):
                        fallback.append({"titular": n["titular"], "url": n.get("url",""), "medio": medio})
        top16 = _filtrar_basura(fallback)
        
    print(f"[fase1] ✅ Top 3: {list(top3.values())}", flush=True)
    print(f"[fase1] ✅ Top 16: {len(top16)} noticias limpias", flush=True)

    # 3. ANÁLISIS DE MEDIOS
    print("[fase1] Analizando medios...", flush=True)
    medios = list((datos.get("prensa") or {}).keys()) + list((datos.get("agencias") or {}).keys()) \
           + list((datos.get("tv") or {}).keys()) + list((datos.get("radio") or {}).keys())
    noticia = list(top3.values())[0] if isinstance(top3, dict) else "noticias del día"

    todos = {}
    total = len(medios)
    print(f"[fase1] {total} medios (3 en paralelo)...", flush=True)
    completados = 0
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(_procesar_medio, m, datos, noticia): m for m in medios}
        for f in as_completed(futs):
            completados += 1
            try:
                medio, an = futs[f], f.result()
                if an:
                    todos[medio] = [an]
                    print(f"  [{completados}/{total}] OK {medio}", flush=True)
                else:
                    print(f"  [{completados}/{total}] -- {medio}", flush=True)
            except Exception as e:
                print(f"  [{completados}/{total}] X {e}", flush=True)

    # 4. GUARDAR
    res = {"fecha": fecha, "top3": top3, "top16": top16, "analisis": todos, "recoleccion": datos}
    out = OUT / f"analisis_fase1_{fecha}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase1] ✅ Guardado en {out}", flush=True)

if __name__ == "__main__":
    analizar_fase1(sys.argv[1] if len(sys.argv) > 1 else None)
