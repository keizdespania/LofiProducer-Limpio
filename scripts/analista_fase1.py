"""analista_fase1.py - Cadena de análisis con el Consejo de Inteligencia."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

# Patrones trágicos y de exclusión
CRIT = [
    r"\bmuert", r"\basesin", r"\btiroteo", r"\bsiniestro", r"\btragedia", r"\bse[nñ]alizaci",
    r"\bmorgue\b", r"\bllanto\b", r"\bfuneral", r"\bduelo\b", r"\bvia\s+dolorosa", r"\bcat[aá]strofe",
    r"\bdescarril", r"\bAdif\b", r"\bRenfe\b", r"\bIryo\b", r"\bmaquinista", r"\bAVE\b",
    r"\bherid", r"\btrenes?\b", r"\bchoc", r"\bv[ií]ctimas", r"\bfallecid", r"\bToledo\b",
    r"\bReyes?\b", r"\bReales?\b", r"\burda\b", r"\bcuerpos\b", r"\bdesaparecid", r"delitos?\s+contra\s+la\s+libertad\s+sexual",
    r"\babuso", r"\bmenores", r"\bAlcaraz\b", r"\bNadal\b", r"\bLaLiga\b", r"\bfutbol",
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

def _es_malo(txt):
    s = (txt or "").lower()
    return any(re.search(p, s) for p in CRIT)

def _similares(a, b):
    wa, wb = set(a.lower().split()), set(b.lower().split())
    if not wa or not wb: return False
    return len(wa & wb) / len(wa | wb) > 0.5

def _sanitizar_top3(top3, limpios):
    items = []
    if isinstance(top3, dict):
        for k in sorted(top3.keys()):
            v = top3[k]
            items.append(v if isinstance(v, str) else (v.get("titulo") if isinstance(v, dict) else str(v)))
    elif isinstance(top3, list):
        for it in top3: items.append(it.get("titulo") if isinstance(it, dict) else str(it))

    items = [x for x in items if x and not _es_malo(x)]
    for cand in limpios:
        if len(items) >= 3: break
        if cand and not _es_malo(cand): items.append(cand)

    unicos = []
    for it in items:
        if not any(_similares(it, u) for u in unicos): unicos.append(it)
    for cand in limpios:
        if len(unicos) >= 3: break
        if cand and not _es_malo(cand) and not any(_similares(cand, u) for u in unicos): unicos.append(cand)

    for g in ["Actualidad nacional", "Política", "Economía", "Sociedad", "Internacional"]:
        if len(unicos) >= 3: break
        if not any(_similares(g, u) for u in unicos): unicos.append(g)

    return {f"noticia_{i+1}": t for i, t in enumerate(unicos[:3])}

def _titulares_limpios(datos):
    out = []
    for sec in ("prensa", "agencias"):
        for lst in (datos.get(sec) or {}).values():
            for x in lst:
                if isinstance(x, dict) and x.get("titular") and not _es_malo(x["titular"]):
                    out.append(x["titular"])
    return out

def _build_ctx(datos):
    ctx = "TITULARES Y URLS:\n"
    for medio, noticias in (datos.get("prensa") or {}).items():
        ctx += f"\n[{medio}]\n"
        for n in noticias:
            if isinstance(n, dict):
                ctx += f"- {n.get('titular','')} (URL: {n.get('url','')})\n"
    return ctx

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
    
    # FORZADO A OMNIROUTE PARA EVITAR 429
    r = pedir_a_especialista("forense_medios",
        f"Analiza el sesgo de {medio} sobre: {noticia}. Devuelve SOLO JSON con: nombre, titular_real, titular_traducido, imd_local, framing, palabra_cuchillo, tecnica_principal, omision.",
        contexto=ctx[:800], proveedor="omni")
    an = _parse_json(r)
    if not an: return None
    
    time.sleep(1)
    r_emo = pedir_a_especialista("analista_emocional", f"Analiza emociones de {medio}", contexto=ctx[:2000], proveedor="omni")
    emo = _parse_json(r_emo)
    if emo: an["emociones"] = emo
    
    time.sleep(1)
    r_ses = pedir_a_especialista("detector_sesgos_cognitivos", f"Detecta sesgos en {medio}", contexto=ctx[:2000], proveedor="omni")
    ses = _parse_json(r_ses)
    if ses: an["sesgos_cognitivos"] = ses
    return an


MEDIOS_OK = ["El País", "El Mundo", "ABC", "La Vanguardia", "elDiario.es", "El Confidencial", "El Español", "OkDiario", "The Objective", "HuffPost", "Europa Press", "20 Minutos", "Ara", "El Correo", "Faro de Vigo", "El Independiente"]
BASURA = [
    "futbol", "athletic", "real madrid", "barça", "barcelona", "murcia", "cartagena", "valencia", "gandia", "pucela", "racing",
    "tiempo en", "previsión meteorológica", "el tiempo", "lluvia", "temperatura", "grados", "dgt", "trafico", "tráfico", "driving", "andalucia",
    "porno", "vídeos", "detenido", "pillan", "marroquí", "mueren", "fallece", "accidente", "sucesos", "cuidar", "final de la vida",
    "gato con sombrero", "litera", "xavier", "arrebatador", "ilusion", "msi", "prestige", "he probado", "review",
    "teatro", "cornejo", "colegio de abogados", "valladolid", "litio", "carbono", "bustamante", "chocolatier", "ambulance", "entrenador", "menor"
]

def _limpiar_top16(top16, datos):
    limpios = []
    # Primero filtramos lo que venga del LLM
    for item in top16:
        titulo = item.get("titular", "").lower()
        medio = item.get("medio", "")
        if any(m in medio for m in MEDIOS_OK) and not any(b in titulo for b in BASURA):
            limpios.append(item)
    
    # Si faltan, sacamos del fallback de la recolección
    if len(limpios) < 16:
        for sec in ("prensa", "agencias"):
            for medio, noticias in (datos.get(sec) or {}).items():
                if not any(m in medio for m in MEDIOS_OK): continue
                for n in noticias:
                    if isinstance(n, dict) and n.get("titular") and n.get("url"):
                        t = n["titular"].lower()
                        if not any(b in t for b in BASURA) and not _es_malo(n["titular"]):
                            if not any(x["titular"] == n["titular"] for x in limpios):
                                limpios.append({"titular": n["titular"], "url": n["url"], "medio": medio})
                                if len(limpios) >= 16: break
                    if len(limpios) >= 16: break
                if len(limpios) >= 16: break
            if len(limpios) >= 16: break
            
    return limpios[:16]

def analizar_fase1(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    limpia = OUT / f"recoleccion_{fecha}_limpia.json"
    rec = limpia if limpia.exists() else (OUT / f"recoleccion_{fecha}.json")
    print(f"[fase1] leyendo {rec.name}", flush=True)
    datos = json.loads(rec.read_text())

    # 1. Top3 + Top16
    print("[fase1] Detectando Top 3 (blog) y Top 16 (video)...", flush=True)
    ctx = _build_ctx(datos)
    prompt_det = """Eres un editor jefe experto en manipulación mediática. 
Lee todos los titulares y URLs del contexto.
Tu tarea:
1. Elige el TOP 3 de noticias más importantes del día para el blog.
2. Elige los 16 titulares que tengan el MAYOR POTENCIAL DE MANIPULACIÓN o FRAMING para desmontar en un vídeo. Prioriza medios generalistas (El País, El Mundo, ABC, etc.). Ignora deportes, farándula y sucesos.
Devuelve EXCLUSIVAMENTE este JSON:
{"top3": ["noticia 1", ...], 
 "top16": [{"titular": "titular 1", "url": "https://...", "medio": "El Pais"}, ... 16 items]}"""
    
    top_data = _parse_json(pedir_a_especialista("detective_tendencias_v2", prompt_det, contexto=ctx[:5000], proveedor="omni"))
    
    top3 = top_data.get("top3", {})
    top16 = top_data.get("top16", [])
    top16 = _limpiar_top16(top16, datos)

    if not top3:
        top3 = {"noticia_1": "Actualidad", "noticia_2": "Política", "noticia_3": "Economía"}
    
    limpios = _titulares_limpios(datos)
    top3 = _sanitizar_top3(top3, limpios)
    
    if not top16:
        # Fallback real: sacar 16 titulares CON URL de la recolección
        todos_urls = []
        # Filtro ultra-estricto para no meter basura
        _BASURA = ["futbol", "athletic", "real madrid", "barça", "barcelona", "murcia", "cartagena", "valencia", "gandia",
                   "tiempo en", "previsión meteorológica", "el tiempo", "lluvia", "temperatura", "grados",
                   "porno", "vídeos", "detenido", "pillan", "marroquí", "mueren", "fallece", "accidente", "sucesos",
                   "gato con sombrero", "litera", "xavier", "arrebatador", "ilusion", "pucela", "dgt", "msi", "prestige", "teatro", "colegio de abogados", "driving", "andalucia"]
                   
        for sec in ("prensa", "agencias"):
            for medio, noticias in (datos.get(sec) or {}).items():
                for n in noticias:
                    t = n.get("titular", "").lower()
                    if isinstance(n, dict) and n.get("titular") and n.get("url") and not _es_malo(n["titular"]):
                        if not any(b in t for b in _BASURA):
                            todos_urls.append({"titular": n["titular"], "url": n["url"], "medio": medio})
        
        # Quitar duplicados por titular
        unicos = []
        for t in todos_urls:
            if t["titular"] not in [u["titular"] for u in unicos]:
                unicos.append(t)
        top16 = unicos[:16]
        
    print(f"[fase1] ✅ Top 3: {list(top3.values())}", flush=True)
    print(f"[fase1] ✅ Top 16: {len(top16)} titulares guardados", flush=True)

    # 2. Análisis por medio
    print("[fase1] Analizando medios...", flush=True)
    medios = list((datos.get("prensa") or {}).keys()) + list((datos.get("agencias") or {}).keys()) \
           + list((datos.get("tv") or {}).keys()) + list((datos.get("radio") or {}).keys())
    noticia = list(top3.values())[0]

    from concurrent.futures import ThreadPoolExecutor, as_completed
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

    # 3. Guardar
    res = {"fecha": fecha, "top3": top3, "top16": top16, "analisis": todos, "recoleccion": datos}
    out = OUT / f"analisis_fase1_{fecha}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase1] ✅ Guardado en {out}", flush=True)

if __name__ == "__main__":
    analizar_fase1(sys.argv[1] if len(sys.argv) > 1 else None)
