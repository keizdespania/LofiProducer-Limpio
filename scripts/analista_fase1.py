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
    "urda", "toledo", "tren", "ave", "adif", "renfe", "señaliz", "lzb", "herid", "cuerpo", "desaparecid", "morgue", "llanto",
    "recoletas", "baloncesto", "metal", "psicología", "psicologia", "deporte", "liga", "fichaje", "partido", "entrenador", "jugador",
    "receta", "cocina", "viajes", "turismo", "moda", "tendencias", "horóscopo", "celebridades"
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

def _filtrar_noticias_serias(noticias):
    """ANTIFILTRO: Solo deja pasar noticias de Politica, Economia, Geopolitica o Sociedad."""
    PALABRAS_SERIAS = [
        # Política
        "gobierno", "sanchez", "feijoo", "psoe", "pp", "vox", "sumar", "congreso", "senado", "elecciones", "partido", "ministro", "presidente", "diputado", "senador", "politica", "política", "ley", "reforma", "corrupcion", "corrupción", "dimision", "dimisión", "oposicion", "oposición", "monarquia", "monarquía", "rey", "felipe", "parlament", "parlamento", "jueces", "constitucional", "justicia", "fiscal", "abogado", "tribunal",
        # Economía
        "economia", "economía", "inflacion", "inflación", "banco", "pension", "pensión", "presupuesto", "impuesto", "hacienda", "deuda", "pib", "empleo", "paro", "empresa", "sueldo", "salario", "precio", "vivienda", "alquiler", "hipoteca", "bolsa", "ibex", "euribor", "bce", "interes", "interés", "arancel", "comercio", "industria",
        # Geopolítica / Internacional
        "rusia", "ucrania", "zelenski", "putin", "eeuu", "ee uu", "trump", "biden", "china", "taiwan", "israel", "gaza", "palestina", "hamas", "iran", "irak", "siria", "onu", "ue", "union europea", "unión europea", "bruselas", "otan", "macron", "francia", "alemania", "reino unido", "europa", "venezuela", "machado", "maduro", "america latina", "américa latina", "mexico", "méxico", "argentina", "milei", "brasil", "lula", "diplomacia", "guerra", "conflicto", "sanciones", "embajada",
        # Sociedad (temas serios)
        "educacion", "educación", "sanidad", "salud", "hospital", "medico", "médico", "colegio", "instituto", "universidad", "inmigracion", "inmigración", "patera", "frontera", "refugiado", "desigualdad", "pobreza", "violencia", "machismo", "feminicidio", "medio ambiente", "clima", "sequia", "sequía", "energia", "energía", "nuclear", "renovable",
        # Medios
        "medio", "prensa", "periodista", "television", "televisión", "radio", "titular", "manipulacion", "manipulación", "desinformacion", "desinformación", "fake news", "bulos", "propaganda", "censura"
    ]
    limpias = []
    vistos = set()
    for n in noticias:
        if not isinstance(n, dict): continue
        tit = (n.get("titular", "") + " " + n.get("extracto", "")).lower()
        # 1. Debe tener alguna palabra de la lista blanca
        if not any(p in tit for p in PALABRAS_SERIAS): continue
        # 2. No puede ser tragedia/suceso
        if any(b in tit for b in ["muere", "muerte", "accidente", "suicidio", "fallece", "detenido", "asesinato", "herido"]): continue
        
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
    
    if not textos: 
        # Si no hay titulares, intentar coger transcripción o extracto
        for a in datos.get("audios", []):
            if a.get("medio") == medio and a.get("transcripcion"):
                textos.append(a["transcripcion"][:500])
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
    
    # LLM solo para el top3 (es rápido)
    prompt_top3 = 'Devuelve SOLO JSON: {"top3": ["noticia 1", "noticia 2", "noticia 3"]}. Usa los titulares del contexto.'
    top3_data = _parse_json(pedir_a_especialista("detective_tendencias_v2", prompt_top3, contexto=ctx[:5000], proveedor="auto"))
    top3 = top3_data.get("top3", ["Actualidad", "Política", "Economía"])
    
    # top40 lo sacamos de la recolección
    top40_raw = []
    for sec in ("prensa", "agencias"):
        for medio, noticias in (datos.get(sec) or {}).items():
            for n in noticias:
                if isinstance(n, dict) and n.get("titular"):
                    top40_raw.append({"titular": n["titular"], "url": n.get("url",""), "medio": medio})
    
    # 2. AGENTE EDITOR JEFE (Filtro Semántico con Bucle de Relleno)
    print("[fase1] Llamando al Editor Jefe para seleccionar noticias...", flush=True)
    import random
    
    def pedir_a_editor(noticias):
        ctx_ed = "\n".join([f"[{n['medio']}] {n['titular']} (URL: {n['url']})" for n in noticias])
        prompt = "Selecciona 16 noticias lógicas. RECHAZA ensaladas, jamón, famosos, deportes y loterías. EVITA redundancias. Devuelve SOLO JSON: {\"aprobadas\": [{\"titular\":\"\",\"medio\":\"\",\"url\":\"\"}], \"descartadas\": [\"\"]}"
        r = pedir_a_especialista("editor_jefe", prompt, contexto=ctx_ed[:8000], proveedor="auto")
        return _parse_json(r)

    resultado_ed = pedir_a_editor(top40_raw)
    top16 = resultado_ed.get("aprobadas", [])
    
    # BUCLE DE RELLENO
    intentos = 0
    while len(top16) < 16 and intentos < 3:
        faltan = 16 - len(top16)
        print(f"[fase1] ⚠️ Faltan {faltan} noticias. Lanzando mini-investigación (Intento {intentos+1})...", flush=True)
        try:
            # Llamar al recolector de oro para traer más noticias
            subprocess.run(["python3", "scripts/recolector_oro.py", fecha], check=True, capture_output=True, timeout=300)
            oro = json.loads((OUT / f"recoleccion_oro_{fecha}.json").read_text())
            
            # Extraer noticias nuevas
            noticias_nuevas = []
            ya_vistas = [t["titular"] for t in top16]
            for medio, ns in oro.items():
                for n in ns:
                    if n["titular"] not in ya_vistas:
                        noticias_nuevas.append({"titular": n["titular"], "url": n.get("url",""), "medio": medio})
            
            if not noticias_nuevas: break
            
            # Pasar las nuevas + las que ya teníamos al editor
            resultado_relleno = pedir_a_editor(noticias_nuevas[:40])
            top16.extend(resultado_relleno.get("aprobadas", []))
            
            # Quitar duplicados de la lista final
            vistos = set()
            top16 = [t for t in top16 if not (t["titular"] in vistos or vistos.add(t["titular"]))]
            
        except Exception as e:
            print(f"[fase1] Fallo en mini-investigación: {e}", flush=True)
        intentos += 1

    # Fallback final por si acaso (nunca debería llegar aquí)
    if len(top16) < 10:
        print("[fase1] ⚠️ Editor Jefe falló. Usando fallback antiguo...", flush=True)
        top16 = _filtrar_noticias_serias(top40_raw)
    
    # Si el LLM ha fallado y no hay 16, sacamos de la recolección directamente
    if len(top16) < 10:
        print("[fase1] ⚠️ Pocas noticias limpias. Ampliando fallback...", flush=True)
        fallback = []
        for sec in ("prensa", "agencias"):
            for medio, noticias in (datos.get(sec) or {}).items():
                for n in noticias:
                    if isinstance(n, dict) and n.get("titular"):
                        fallback.append({"titular": n["titular"], "url": n.get("url",""), "medio": medio})
        top16 = _filtrar_noticias_serias(fallback)
        
    print(f"[fase1] ✅ Top 3: {top3}", flush=True)
    print(f"[fase1] ✅ Top 16: {len(top16)} noticias limpias", flush=True)

    # 3. ANÁLISIS DE MEDIOS
    print("[fase1] Analizando medios...", flush=True)
    medios = list((datos.get("prensa") or {}).keys()) + list((datos.get("agencias") or {}).keys()) \
           + list((datos.get("tv") or {}).keys()) + list((datos.get("radio") or {}).keys())
    noticia = top3[0] if isinstance(top3, list) and top3 else "noticias del día"

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
    top3_dict = {f"noticia_{i+1}": n for i, n in enumerate(top3)}
    res = {"fecha": fecha, "top3": top3_dict, "top16": top16, "analisis": todos, "recoleccion": datos}
    out = OUT / f"analisis_fase1_{fecha}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase1] ✅ Guardado en {out}", flush=True)

if __name__ == "__main__":
    analizar_fase1(sys.argv[1] if len(sys.argv) > 1 else None)
