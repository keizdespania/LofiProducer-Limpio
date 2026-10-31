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
        "Eres el CONTRAMEDIO de 'El Encuadre'. Tu misión NO es contar la noticia, sino AUDITAR la manipulación. "
        "Señalas cómo el medio utiliza el titular para manipular al lector. "
        "Eres irónico, mordaz y directo. No hablas como un periodista oficial, hablas como alguien que ha descubierto la trampa. "
        "SOLO NARRACIÓN LOCUTADA."
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
        f"Empieza con un golpe de efecto brutal (ej: 'Hoy los medios han vuelto a intentar manipularnos, y lo han hecho con tu permiso'). "
        f"Luego di: 'Somos El Encuadre y hoy, {_fecha_str}, abrimos la cloaca mediática'. "
        "Suelta una promesa de lo que van a aprender (ej: 'Te voy a enseñar las 3 técnicas que han usado hoy para que no pienses'). "
        "Cierra la escena diciendo: 'Quedate, porque esto te va a volar la cabeza'."
    )
    escenas.append(_generar_escena(1, intro_inst))

    # --- ESCENAS 2-17: 4 BLOQUES TEMÁTICOS ---
    # Agrupamos las noticias en 4 bloques de 4 (si sobran, se ignoran, si faltan, el bloque es más pequeño)
    bloques = [top16[i:i + 4] for i in range(0, len(top16), 4)]
    
    num = 2
    for idx_bloque, bloque in enumerate(bloques):
        if len(bloque) == 0: continue
        
        # Unir todos los titulares del bloque en un solo contexto
        ctx_bloque = "\n".join([
            f"Medio: {n.get('medio', '?')} | Titular: {n.get('titular', '?')} | Extracto: {n.get('extracto', '')[:200]}"
            for n in bloque
        ])
        
        # 1 escena de "Intro del bloque"
        print(f"   [Escena {num}/18] Intro Bloque {idx_bloque+1}...", flush=True)
        inst_intro = (
            f"Estás empezando el bloque {idx_bloque+1} de 4. "
            f"Tienes estas noticias: {ctx_bloque[:500]}. "
            "Haz una introducción que conecte todas estas noticias bajo un mismo hilo conductor de MANIPULACIÓN mediática. "
            "Explica cómo los medios usan este bloque temático para construir un relato. "
            "Habla como el contramedio."
        )
        escenas.append(_generar_escena(num, inst_intro, ctx_bloque))
        num += 1
        
        # 2 o 3 escenas de "Análisis de las noticias del bloque"
        for j, noticia in enumerate(bloque):
            if num >= 18: break
            titular = noticia.get("titular", "Noticia")
            print(f"   [Escena {num}/18] Bloque {idx_bloque+1}, noticia {j+1}: {titular[:30]}...", flush=True)
            
            ctx_noticia = f"Medio: {noticia.get('medio', '?')}\nTitular: {titular}\nExtracto: {noticia.get('extracto', 'No disponible.')}"
            inst_analisis = (
                f"Analiza este titular: '{titular}'. "
                "No repitas la estructura A+B+C+D. Varía el ritmo: a veces empieza por la conclusión, a veces por una pregunta, a veces por una anécdota. "
                "Expón la manipulación de forma directa, sin sonar a profesor."
            )
            escenas.append(_generar_escena(num, inst_analisis, ctx_noticia))
            num += 1

    # --- ESCENA 18: CIERRE ---
    print("   [Escena 18/18] Cierre...", flush=True)
    cierre_inst = (
        "Haz un cierre épico y demoledor. "
        "No resumas lo que ya has dicho. En su lugar, haz una arenga: 'Mañana, los mismos medios volverán a intentarlo. "
        "Volverán a insultar tu inteligencia. La única diferencia es que ahora ya sabes lo que están haciendo'. "
        "Termina con un llamado a la acción brutal: 'Dale a like, suscríbete, o comparte este video con ese amigo que todavía se cree la tele. Nos vemos en el siguiente desmontaje'."
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