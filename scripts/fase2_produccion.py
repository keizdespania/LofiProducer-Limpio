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
    dossier = datos.get("dossier", {})
    guiones_base = datos.get("guiones", {})
    hooks = guiones_base.get("hooks_totales", [])
    
    res = {"fecha": fecha, "dossier": dossier}
    ctx = json.dumps({"dossier": dossier, "hooks": hooks[:5]}, ensure_ascii=False)
    
    # 1. ESQUELETO Y ARTÍCULO
    print("[fase2] 1/5 Arquitecto + Redactor...", flush=True)
    esqueleto = _parse_json_seguro(pedir_a_especialista("arquitecto_contenido", "Crea el esqueleto del artículo.", contexto=ctx[:3000]))
    _PROMPT_REDACTOR = (
        'Escribe un artículo periodístico de 1200-1500 palabras en MARKDOWN PLANO. '
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

    # 2. GUION DE YOUTUBE (18 escenas para montaje cinematografico)
    print("[fase2] 2/5 Guionista: 18 escenas (40% video / 60% imagen)...", flush=True)
    escenas = []
    
    # Intentar con el LLM
    _PROMPT_GUION = (
        'Eres un hibrido entre profesor de comunicacion, periodista de investigacion y columnista ironico. PROHIBIDO responder con HTML, CSS o articulos. Solo JSON con narracion locutada. '
        'OBJETIVO: DEMOSTRAR con datos concretos que los medios usan tecnicas de framing. NO opinas: citas y desmontas. '
        'FORMATO: 18 escenas. '
        'ESTRUCTURA UNIVERSAL POR NOTICIA (CRITICO - IGNORA QUIEN SEA EL PROTAGONISTA): '
        '1. CONTEXTO IRONICO: Empieza con una ironia sobre la actualidad (ej: la economia, los jovenes, los precios). '
        '2. EL TITULAR: Cita el titular exacto de un medio y di quien es el CHIVO EXPIATORIO (el malo de la pelicula). Puede ser un politico, la UE, una empresa, un pais... '
        '3. EL BENEFICIARIO: Explica a quien beneficia este relato (quien se libra de la culpa o quien gana poder/dinero). '
        '4. LA TECNICA: Desmonta que sesgo han usado (cortina de humo, hombre de paja, anclaje...). '
        '5. CIERRE: Pregunta al espectador o ironia final. '
        'ESTRUCTURA: '
        'Escena 1: Intro pactada (saludo + fecha + ironía). '
        'Escenas 2-17: Analiza 16 titulares diferentes (1 escena por titular). Aplica la fórmula: Titular -> Chivo Expiatorio -> Beneficiario -> Técnica. '
        'Escena 18: Cierre mordaz resumiendo el día. '
        'ESCENA 1 (INTRO OBLIGATORIA): '
        'Empieza con un saludo UNICO y CREATIVO dirigido a la audiencia. Ejemplos: "Hola a todos los despiertos", "Buenas, mentes inquietas", "Saludos, buscadores de la verdad", "Hola, observadores del ruido", "Bienvenidos, analistas del framing". NUNCA uses el mismo dos veces. '
        'Despues del saludo, di EXACTAMENTE: "Somos El Encuadre y hoy, [DIA] de [MES] de [AÑO], os traemos el nuevo analisis definitivo de medios de comunicacion masiva del dia de hoy". '
        'Sustituye [DIA] por el numero del dia, [MES] por el mes en castellano, [AÑO] por el ano. '
        'La fecha de publicacion es: __FECHA_PUB__. '
        'Despues del saludo+fecha, continua con el analisis del dia. '
        'REGLAS DE DISTRIBUCION TOP3 (CRITICO): '
        'Las 18 escenas DEBEN cubrir las 3 noticias del TOP3, NO solo una. '
        'NO INVENTES noticias que no esten en el TOP3. '
        'Las 3 noticias del TOP3 estan en el contexto, usalas TAL CUAL. '
        'Si solo tienes 3 noticias, haz 5 escenas de cada una. NO añadas temas nuevos. '
        'Distribucion obligatoria: '
        '  - Escenas 1-2: intro + presentacion breve del TOP3 completo. '
        '  - Escenas 3-7: noticia_1 (5 escenas). '
        '  - Escenas 8-12: noticia_2 (5 escenas). '
        '  - Escenas 13-17: noticia_3 (5 escenas). '
        '  - Escena 18: cierre comparativo de las 3. '
        'Cada noticia debe tener MINIMO 5 escenas propias. '
        'EXCLUIR DEPORTES: NO incluyas noticias de deportes (futbol, tenis, Alcaraz, Nadal, liga, partido, como ver online). Si el TOP3 contiene deportes, sustituyelo por otra noticia de actualidad. '
        'ESTRUCTURA de las escenas 2-18: '
        '(1) CITAS un titular real de un medio del contexto. '
        '(2) DESCOMPONES la tecnica. '
        '(3) CONTRASTAS con otro medio. '
        '(4) CIERRAS con pregunta o ironia fina. '
        'Devuelve EXCLUSIVAMENTE JSON: {"escenas":[{"id":1,"texto":"NARRACION","concepto_visual":"VISUAL DESC EN INGLES","mood_musical":"tension|epico|inspirador|relax|misterio|electronico","tipo_visual":"imagen"}]}. '
        'REGLAS: '
        '(1) EXACTAMENTE 18 escenas (1 intro + 16 titulares + 1 cierre). '
        '(2) texto = SOLO narracion, primera persona o impersonal. PROHIBIDO: El video abre, Vemos, Corte a, Voz en off dice, descripciones visuales. '
        '(3) Cada texto 80-100 palabras. '
        '(4) Cada escena 2-18 cita MINIMO 1 medio real + 1 tecnica + 1 contraste. '
        '(5) concepto_visual EN INGLES, 8-15 palabras, Subject + Action + Environment + Lighting + Style. '
        '(6) Total minimo 1450 palabras. SOLO JSON. '
        'TONO: educado, ironico, autoridad periodistica. Como Inaki Gabilondo con mala leche. '
        'NO acusar de delito. Solo describir tecnicas.'
    )
    # Preparar fecha de publicación (fuera del try)
    import datetime as _dt2
    _ahora = _dt2.datetime.now()
    _pub = (_dt2.date.today() + _dt2.timedelta(days=1)) if _ahora.hour >= 18 else _dt2.date.today()
    _MESES = {1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"}
    _fecha_str = f"{_pub.day} de {_MESES[_pub.month]} de {_pub.year}"
    _prompt_con_fecha = _PROMPT_GUION.replace("__FECHA_PUB__", _fecha_str)
    print(f"   Fecha publicacion: {_fecha_str}", flush=True)
    try:
        # LIMPIAR HTML del artículo (evita que LLM copie CSS)
        import re as _re_clean
        _art_limpio = _re_clean.sub(r'<style[^>]*>.*?</style>', '', articulo, flags=_re_clean.DOTALL|_re_clean.I)
        _art_limpio = _re_clean.sub(r'<script[^>]*>.*?</script>', '', _art_limpio, flags=_re_clean.DOTALL|_re_clean.I)
        _art_limpio = _re_clean.sub(r'<[^>]+>', ' ', _art_limpio)
        _art_limpio = _re_clean.sub(r'\{[^}]*\}', ' ', _art_limpio)  # quitar CSS residual
        _art_limpio = _re_clean.sub(r'\s+', ' ', _art_limpio).strip()
        print(f"   Articulo limpio: {len(_art_limpio)} chars (era {len(articulo)})", flush=True)

        resp = pedir_a_especialista("guionista_youtube_experto", _prompt_con_fecha,
            contexto=("ARTICULO:\n" + _art_limpio[:2000] + "\n\nTOP 16 TITULARES:\n" + json.dumps(datos.get("top16", [])) + "\n\nANALISIS POR MEDIO:\n" + _analisis_medios_para_guionista()[:2000]))
        d = _parse_json_seguro(resp)
        if isinstance(d, dict) and "escenas" in d:
            escenas = d["escenas"]
            # VALIDAR: rechazar escenas con HTML/CSS en texto
            _html_markers = ['body {', 'font-family', '<style', '<html', '<div', '<p>', '<h1', '<h2', 'font-size:', 'margin:', 'padding:', 'color:']
            _escenas_ok = []
            for e in escenas:
                txt = e.get("texto", "")
                if any(m in txt.lower() for m in _html_markers):
                    print(f"   ⚠️ Escena {e.get('id','?')} con HTML detectada, descartada", flush=True)
                    continue
                _escenas_ok.append(e)
            if len(_escenas_ok) < len(escenas):
                print(f"   Filtradas {len(escenas)-len(_escenas_ok)} escenas con HTML", flush=True)
                escenas = _escenas_ok
            # Sanitizer: eliminar frases de montaje que se cuelen
            import re as _re
            _PATRONES_MONTAJE = [
                r'El video (abre|empieza|cierra|termina) con [^.]*\.\s*',
                r'(La c[áa]mara|El plano|La escena|El montaje)[^.]*\.\s*',
                r'Corte a [^.]*\.\s*',
                r'Fundido a [^.]*\.\s*',
                r'(Vemos|Se ve|Se muestra|Se observa) [^.]*\.\s*',
                r'Una voz en off (dice|narra):?\s*[“\"]?',
                r'\[.*?\]', r'\(.*?\)',
                r'^[A-ZÁÉÍÓÚÑ ]{4,}:\s*',
            ]
            for e in escenas:
                t_orig = e.get("texto", "")
                t_clean = t_orig
                for pat in _PATRONES_MONTAJE:
                    t_clean = _re.sub(pat, '', t_clean, flags=_re.MULTILINE)
                t_clean = _re.sub(r'\s+', ' ', t_clean).strip()
                if t_clean and len(t_clean) > 20:
                    e["texto"] = t_clean
            print(f"   sanitizadas {len(escenas)} escenas (montaje→narración)", flush=True)
        elif isinstance(d, list):
            escenas = d
        print(f"   Escenas generadas por LLM: {len(escenas)}", flush=True)
    except Exception as e:
        print(f"   ⚠️ LLM falló: {e}", flush=True)

    # Fallback manual: Dividir el artículo en 18 trozos
    # VALIDACIÓN: si el LLM devolvió menos de 1300 palabras → reintento
    _pal_actual = sum(len(e.get("texto","").split()) for e in escenas)
    if _pal_actual < 1300 and escenas:
        print(f"   LLM devolvio {_pal_actual} palabras (< 1300). Reintentando con enfasis...", flush=True)
        _reintento = pedir_a_especialista("guionista_youtube_experto",
            _PROMPT_GUION + " ATENCION: tu respuesta anterior tenia solo " + str(_pal_actual) + " palabras. Es INACEPTABLE. Amplia cada escena a 70 palabras EXACTAS. Total minimo 1430.",
            contexto="ARTICULO:\n" + articulo[:6000])
        _d2 = _parse_json_seguro(_reintento)
        if isinstance(_d2, dict) and "escenas" in _d2:
            _escenas2 = _d2["escenas"]
            _pal_re = sum(len(e.get("texto","").split()) for e in _escenas2)
            if _pal_re > _pal_actual:
                escenas = _escenas2
                print(f"   Reintento aceptado: {_pal_re} palabras", flush=True)
            else:
                print(f"   Reintento no mejoro ({_pal_re}), mantengo original", flush=True)

    # Si hay pocas escenas, forzar un mínimo de 12-15 para garantizar 10 min
    num_escenas_objetivo = 15 if len(escenas) < 12 else len(escenas)
    if len(escenas) < 12:
        print(f"   ⚠️ Solo {len(escenas)} escenas. Forzando {num_escenas_objetivo} para 10 min...", flush=True)
        # Usar artículo limpio (no el HTML original)
        try:
            texto_fuente = _art_limpio
        except NameError:
            texto_fuente = re.sub(r'<[^>]+>', ' ', articulo)
        # Quitar markdown (#, *, **, >, ---, links) del artículo
        texto = re.sub(r'<[^>]+>', ' ', texto_fuente)
        texto = re.sub(r'^#{1,6}\s+', '', texto, flags=re.MULTILINE)
        texto = re.sub(r'\*\*([^*]+)\*\*', r'\1', texto)
        texto = re.sub(r'\*([^*]+)\*', r'\1', texto)
        texto = re.sub(r'^>\s+', '', texto, flags=re.MULTILINE)
        texto = re.sub(r'---', '', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        palabras = texto.split()
        chunk = max(40, len(palabras) // num_escenas_objetivo) if len(palabras) >= 400 else max(30, len(palabras) // 8)
        num_escenas_objetivo = min(15, max(8, len(palabras) // max(chunk, 40)))
        moods = ["tension", "misterio", "epico", "inspirador", "electronico", "relax"]
        escenas = []
        for i in range(num_escenas_objetivo):
            ini = i * chunk
            fin_i = min(len(palabras), (i+1) * chunk)
            if ini >= len(palabras): break
            escenas.append({
                "id": i + 1,
                "texto": " ".join(palabras[ini:fin_i]),
                "concepto_visual": "cinematic dark news analysis about " + str(dossier.get("tema_del_dia", "analysis")) + ", abstract",
                "mood_musical": moods[i % len(moods)],
                "tipo_visual": "video" if i == 0 or i % 3 == 0 else "imagen"
            })
        print(f"   ✅ {len(escenas)} escenas generadas", flush=True)
    # CAPA 4: Gate de Sentimiento
    print("[fase2] Analizando temperatura emocional...", flush=True)
    sent = _parse_json_seguro(pedir_a_especialista("analista_sentimiento", "Analiza el tono", contexto=ctx[:2000]))
    res["sentimiento"] = sent
    if sent.get("intensidad", 0) > 80:
        print(f"   ⚠️ Tema caliente ({sent.get('emocion_principal')}). Ajustando...", flush=True)

    res["escenas"] = escenas
    res["texto_voz_largo"] = " ".join([e.get("texto", "") for e in escenas])
    print(f"   OK {len(escenas)} escenas guardadas", flush=True)

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