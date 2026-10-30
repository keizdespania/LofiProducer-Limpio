"""fase2_produccion.py - Fábrica de Contenido: Artículo, Guion YouTube, SEO, Shorts y Plan de Montaje."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def _parse_json_seguro(texto):
    if not texto: return {}
    t = re.sub(r'```(?:json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()
    try: return json.loads(t)
    except: pass
    matches = re.findall(r'\{.*?\}', texto, re.DOTALL)
    for m in sorted(matches, key=len, reverse=True):
        try: return json.loads(m)
        except: pass
    return {}

def _limpiar_html(texto):
    if not texto: return ""
    return re.sub(r'```(?:html|json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()


def _analisis_medios_para_guionista():
    import json as _j, pathlib as _p, datetime as _dt
    fecha = _dt.date.today().isoformat()
    af = _p.Path(__file__).resolve().parent.parent / 'output' / 'encuadre' / ('analisis_fase1_' + fecha + '.json')
    if not af.exists(): return ''
    try:
        d = _j.loads(af.read_text())
        lineas = []
        for medio, items in (d.get('analisis') or {}).items():
            for it in items:
                if isinstance(it, dict) and it.get('framing'):
                    tit = it.get('titular_traducido') or it.get('titular_real') or ''
                    lineas.append('[' + medio + '] ' + tit[:80] + ' | framing: ' + it.get('framing','')[:60])
        return chr(10).join(lineas[:35])
    except Exception:
        return ''


def producir_fase2(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    dossier_file = OUT / f"dossier_{fecha}.json"
    if not dossier_file.exists():
        print(f"❌ No existe {dossier_file}"); return None
    
    datos = json.loads(dossier_file.read_text())
    
    # RECUPERAR EL TOP16 DEL ANALISIS (que es donde está realmente)
    af = OUT / f"analisis_fase1_{fecha}.json"
    if af.exists():
        try:
            analisis_data = json.loads(af.read_text())
            datos["top16"] = analisis_data.get("top16", [])
        except Exception as e:
            print(f"⚠️ No se pudo leer el top16 del analisis: {e}")

    dossier = datos.get("dossier", {})
    guiones_base = datos.get("guiones", {})
    hooks = guiones_base.get("hooks_totales", [])
    
    res = {"fecha": fecha, "dossier": dossier}
    ctx = json.dumps({"dossier": dossier, "hooks": hooks[:5]}, ensure_ascii=False)
    
    # 1. ESQUELETO Y ARTÍCULO
    print("[fase2] 1/5 Arquitecto + Redactor...", flush=True)
    esqueleto = _parse_json_seguro(pedir_a_especialista("arquitecto_contenido", "Crea el esqueleto del artículo.", contexto=ctx[:3000]))
    _PROMPT_REDACTOR = (
        'Escribe un artículo periodístico mordaz y directo de 1200-1500 palabras en MARKDOWN PLANO. Usa un tono irónico y callejero, no académico. '
        'PROHIBIDO: HTML, CSS, DOCTYPE, <head>, <style>, <body>, <div>, <p>, <h1>. '
        'Usa SOLO: # para títulos, ## para subtítulos, **negrita**, *cursiva*, > para citas, y párrafos separados por líneas en blanco. '
        'Cita medios reales del dossier. Tono: profesor + periodista irónico. '
        'Devuelve SOLO el texto del artículo, sin explicaciones, sin envolver en bloques de código.'
    )
    articulo = pedir_a_especialista("redactor_blog", _PROMPT_REDACTOR,
        contexto=f"ESQUELETO:\n{json.dumps(esqueleto)}\n\nDOSSIER:\n{ctx[:3000]}")
    articulo = _limpiar_html(articulo)
    # VALIDAR: si tras limpiar hay <500 chars, abortar
    if len(articulo.strip()) < 500:
        print(f"   ⚠️ Articulo demasiado corto tras limpiar ({len(articulo)} chars). Reintentando con prompt simplificado...", flush=True)
        articulo = pedir_a_especialista("redactor_blog",
            "Escribe un artículo periodístico de 1200 palabras. SOLO TEXTO PLANO, sin HTML. Empieza directamente con el título.",
            contexto=f"TEMAS: {list(top3.values())[:3]}")
        articulo = _limpiar_html(articulo)
    print("[fase2] Verificando hechos del articulo...")
    verif = _parse_json_seguro(pedir_a_especialista("verificador_factos", "Revisa este articulo", contexto=articulo[:4000]))
    if verif.get("texto_corregido"):
        _vc = verif["texto_corregido"]
        # Rechazar si el verificador devuelve HTML
        if any(m in _vc.lower() for m in ['<!doctype', '<html', '<style', 'font-family']):
            print(f"   ⚠️ Verificador devolvió HTML, se ignora", flush=True)
        else:
            articulo = _vc
            print(f"   ✅ Articulo verificado. Alertas: {len(verif.get('alertas', []))}")
    res["articulo_html"] = articulo
    res["esqueleto"] = esqueleto

    # 2. GUION DE YOUTUBE (Generación secuencial, 1 por noticia)
    print("[fase2] 2/5 Guionista: 18 escenas (Generación secuencial)...", flush=True)
    
    # Fecha de publicación
    import datetime as _dt2
    _ahora = _dt2.datetime.now()
    _pub = (_dt2.date.today() + _dt2.timedelta(days=1)) if _ahora.hour >= 18 else _dt2.date.today()
    _MESES = {1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"}
    _fecha_str = f"{_pub.day} de {_MESES[_pub.month]} de {_pub.year}"
    print(f"   Fecha publicacion: {_fecha_str}", flush=True)

    top16 = datos.get("top16", [])
    escenas = []

    # PROMPT BASE (System para todas las escenas)
    _SYS_GUION = (
        "Eres un analista mediático mordaz, cercano y para todos los públicos. "
        "Hablas como un amigo inteligente en un bar, usando ironía y sarcasmo. "
        "SOLO NARRACIÓN LOCUTADA. Prohibido HTML, markdown o acotaciones (FADE IN, etc)."
    )

    # FUNCIÓN AUXILIAR PARA GENERAR 1 ESCENA
    def _generar_escena(num, instruccion, contexto_noticia=""):
        prompt = f"Genera la escena {num} del guion. {instruccion} " \
                 "Devuelve SOLO un JSON válido con esta estructura: " \
                 '{"id": ' + str(num) + ', "texto": "Tu narración de 80-100 palabras", "concepto_visual": "English prompt for SDXL", "mood_musical": "tension|epico|inspirador|relax|misterio|electronico", "tipo_visual": "video|imagen"}'
        
        ctx = f"NOTICIA DEL DÍA:\n{contexto_noticia}" if contexto_noticia else ""
        
        for intento in range(3):
            resp = pedir_a_especialista("guionista_youtube_experto", prompt, contexto=ctx, proveedor="auto")
            d = _parse_json_seguro(resp)
            if d and isinstance(d, dict) and "texto" in d and len(d["texto"].split()) > 20:
                return d
            print(f"      Reintento {intento+1}/3 escena {num}...", flush=True)
            time.sleep(2)
        
        # Fallback de emergencia para no romper el vídeo
        return {"id": num, "texto": f"Error generando la escena {num}. Aquí iría el análisis de la noticia.", "concepto_visual": "newspaper abstract, cinematic", "mood_musical": "tension", "tipo_visual": "imagen"}

    # --- ESCENA 1: INTRO ---
    print("   [Escena 1/18] Intro...", flush=True)
    intro_inst = (
        f"Empieza con un saludo único y creativo. Luego di EXACTAMENTE: 'Somos El Encuadre y hoy, {_fecha_str}, os traemos el nuevo análisis definitivo de medios de comunicación masiva del día de hoy'. "
        "Después, suelta una ironía sobre la actualidad en España (ej: 'Mientras los buenos trabajadores se van al extranjero...')."
    )
    escenas.append(_generar_escena(1, intro_inst))

    # --- ESCENAS 2-17: LAS 16 NOTICIAS ---
    for i, noticia in enumerate(top16[:16]):
        num = i + 2
        titular = noticia.get("titular", "Noticia sin titular")
        url = noticia.get("url", "")
        extracto = noticia.get("extracto", "")
        
        # Si no hay extracto (porque el scraper falló), usamos el titular
        ctx_texto = f"Titular: {titular}\nExtracto: {extracto if extracto else 'No disponible, analiza solo el titular.'}"
        
        print(f"   [Escena {num}/18] Noticia {i+1}: {titular[:40]}...", flush=True)
        
        inst = (
            f"Analiza este titular como un tertuliano cabreado en un bar: '{titular}'. "
            "NO uses palabras de robot (ej: 'El medio usa a X como chivo expiatorio'). "
            "En su lugar, usa la fórmula: (1) Señala al malo de la película (el que se come la culpa). "
            "(2) Destapa al beneficiario (el que se ríe de fondo). "
            "(3) Explica la técnica de manipulación con ironía (ej: 'Esto es una cortina de humo de manual'). "
            "Habla con rabia, con chispa, con calle."
        )
        escenas.append(_generar_escena(num, inst, ctx_texto))

    # --- ESCENA 18: CIERRE ---
    print("   [Escena 18/18] Cierre...", flush=True)
    cierre_inst = (
        "Haz un cierre mordaz resumiendo el día. "
        "Termina con una pregunta irónica que invite al espectador a reflexionar sobre cómo los medios construyen la realidad."
    )
    escenas.append(_generar_escena(18, cierre_inst))

    res["escenas"] = escenas
    res["texto_voz_largo"] = " ".join([e.get("texto", "") for e in escenas])
    _palabras = len(res["texto_voz_largo"].split())
    _min_est = _palabras / 130
    print(f"   Validacion duracion: {_palabras} palabras -> {_min_est:.1f} min (objetivo >=10)", flush=True)
    res["duracion_estimada_min"] = round(_min_est, 1)
    res["palabras_totales"] = _palabras

    # 3. DJ MUSICAL
    print("[fase2] 3/5 DJ Musical...", flush=True)
    from descargar_musica_dinamica import descargar_por_mood
    moods = set([e.get("mood_musical", "relax") for e in res["escenas"]])
    for m in moods:
        if m: descargar_por_mood(m, 1)
    res["musica"] = {"pistas": list(moods)}

    # 4. SHORTS (Seleccionando los 4 mejores por score)
    print("[fase2] 4/5 Selector de Hooks: eligiendo los 4 mejores...", flush=True)
    
    # Calcular score heurístico si LLM no lo dio
    for h in hooks:
        if not isinstance(h.get("score"), (int, float)) or h.get("score") == 0:
            _score = 50
            _hook = (h.get("hook") or "").lower()
            _tipo = (h.get("tipo") or "").lower()
            # +20 si empieza por pregunta
            if _hook.startswith("¿") or "?" in _hook[:20]: _score += 15
            # +10 si tiene número
            if any(c.isdigit() for c in _hook): _score += 10
            # +10 si tiene palabras curiosas
            for _p in ["quién", "por qué", "cómo", "qué esconde", "verdad", "mentira", "secreto", "cifra"]:
                if _p in _hook: _score += 5
            # +5 si tipo bueno
            if any(k in _tipo for k in ["cita", "dato", "confront", "psicolog", "irón", "iron"]): _score += 5
            # +5 si hook 40-90 chars (óptimo)
            if 40 <= len(_hook) <= 90: _score += 5
            h["score"] = min(100, _score)
            h["razon_score"] = "heuristico"

    # Ordenar todos los hooks por score (de mayor a menor)
    hooks_ordenados = sorted(hooks, key=lambda x: x.get("score", 0), reverse=True)
    
    # Elegir los 4 mejores, intentando que haya variedad de tipos
    tipos_vistos = set()
    shorts_finales = []
    
    # Primera pasada: uno de cada tipo
    for h in hooks_ordenados:
        tipo = h.get("tipo", "otro")
        if tipo not in tipos_vistos and len(shorts_finales) < 4:
            tipos_vistos.add(tipo)
            shorts_finales.append(h)
    
    # Segunda pasada: rellenar hasta 4 si faltan
    for h in hooks_ordenados:
        if len(shorts_finales) >= 4: break
        if h not in shorts_finales:
            shorts_finales.append(h)
    
    # Asignar IDs
    for i, s in enumerate(shorts_finales):
        s["id"] = f"short_{i+1}"
    
    res["shorts_finales"] = shorts_finales
    print(f"   ✅ {len(shorts_finales)} shorts seleccionados (scores: {[s.get('score', '?') for s in shorts_finales]})", flush=True)

    # 5. SEO MAESTRO
    print("[fase2] 5/5 SEO Maestro...", flush=True)
    prompt_seo = "Genera el SEO. Devuelve SOLO JSON: {\"youtube\": {\"titulo\": \"string\", \"descripcion\": \"string\"}, \"tiktok\": {\"texto\": \"string\"}, \"instagram\": {\"texto\": \"string\"}, \"x\": {\"texto\": \"string\"}}"
    res["seo"] = _parse_json_seguro(pedir_a_especialista("seo_maestro", prompt_seo, contexto=f"Tema: {dossier.get('tema_del_dia')}"))

    # CAPA 4: Gate de Viralidad
    print("[fase2] Calculando score de viralidad...", flush=True)
    # Usar shorts_finales (hooks reales) no la lista hooks (puede estar vacía)
    _hooks_para_puntuar = res.get("shorts_finales", []) or hooks or []
    _ctx_viral = json.dumps({
        "dossier": dossier,
        "hooks": _hooks_para_puntuar[:3],
        "articulo_resumen": (articulo or "")[:500],
    }, ensure_ascii=False)[:3000]
    viral_raw = pedir_a_especialista("predictor_viralidad",
        'Devuelve EXCLUSIVAMENTE este JSON: {"score": 0-100, "razon": "string", "recomendaciones": ["string"]}. SOLO JSON, sin markdown.',
        contexto=_ctx_viral, proveedor="omni")
    viral = _parse_json_seguro(viral_raw)
    if not viral or "score" not in viral:
        import re as _re
        m = _re.search(r'(?:puntuaci[oó]n|score)[^0-9]*?(\d{1,3})\s*(?:/|de)\s*100', viral_raw or "", _re.I)
        if m:
            viral = {"score": int(m.group(1)), "raw": (viral_raw or "")[:300]}
        else:
            viral = {"score": 0, "raw": (viral_raw or "")[:300]}
    res["viralidad"] = viral
    print(f"   ✅ Score de viralidad: {viral.get('score', 'N/A')}/100", flush=True)

    # GUARDAR
    out_json = OUT / f"produccion_{fecha}.json"
    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase2] ✅ Guardado en {out_json}", flush=True)
    return res

if __name__ == "__main__":
    producir_fase2(sys.argv[1] if len(sys.argv) > 1 else None)