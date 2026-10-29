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
    articulo = pedir_a_especialista("redactor_blog", "Escribe el artículo HTML completo.", contexto=f"ESQUELETO:\n{json.dumps(esqueleto)}\n\nDOSSIER:\n{ctx[:3000]}")
    articulo = _limpiar_html(articulo)
    print("[fase2] Verificando hechos del articulo...")
    verif = _parse_json_seguro(pedir_a_especialista("verificador_factos", "Revisa este articulo", contexto=articulo[:4000]))
    if verif.get("texto_corregido"):
        articulo = verif["texto_corregido"]
        print(f"   ✅ Articulo verificado. Alertas: {len(verif.get('alertas', []))}")
    res["articulo_html"] = articulo
    res["esqueleto"] = esqueleto

    # 2. GUION DE YOUTUBE (18 escenas para montaje cinematografico)
    print("[fase2] 2/5 Guionista: 18 escenas (40% video / 60% imagen)...", flush=True)
    escenas = []
    
    # Intentar con el LLM
    _PROMPT_GUION = (
        'Devuelve EXCLUSIVAMENTE un JSON: {"escenas":[{"id":1,"texto":"NARRACION","concepto_visual":"DESC VISUAL","mood_musical":"tension|epico|inspirador|relax|misterio|electronico","tipo_visual":"imagen"}]}. '
        'ERES UN PROFESOR DE COMUNICACION. Enseñas como los medios usan tecnicas de framing, sesgos y encuadres. '
        'NO acusas, NO haces politica, NO criticas gobiernos. EDUCAS con ejemplos concretos. '
        'ESTRUCTURA por escena: dato/ejemplo -> tecnica usada -> "esto es lo que deberias observar". '
        'TONO: analitico, calmado, profesor universitario. Sin alarmismo. Sin "intriga". Sin "manipulacion" como insulto. '
        'REGLAS: (1) 18 escenas exactas. (2) "texto" = 80-100 palabras de NARRACION PURA (primera persona o impersonal). '
        'PROHIBIDO: "El video abre", "Vemos", "Corte a", "Voz en off dice", descripciones visuales, acotaciones. '
        '(3) "concepto_visual" = descripcion LITERAL para SDXL (ej: "Periodicos franceses apilados, primer plano, luz dramatica"). '
        '(4) Total minimo 1450 palabras. (5) SOLO JSON.'
    )
    try:
        resp = pedir_a_especialista("guionista_youtube_experto", _PROMPT_GUION,
            contexto="ARTICULO:\n" + articulo[:6000])
        d = _parse_json_seguro(resp)
        if isinstance(d, dict) and "escenas" in d:
            escenas = d["escenas"]
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
        texto = re.sub(r'<[^>]+>', ' ', articulo)
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
    viral_raw = pedir_a_especialista("predictor_viralidad",
        'Devuelve EXCLUSIVAMENTE este JSON: {"score": 0-100, "razon": "string", "recomendaciones": ["string"]}. SOLO JSON, sin markdown.',
        contexto=json.dumps({"dossier": dossier, "hooks": hooks[:3]}, ensure_ascii=False)[:3000])
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