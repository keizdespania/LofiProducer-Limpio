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
    try:
        resp = pedir_a_especialista("guionista_youtube_experto", "Escribe guion de 18 escenas.", contexto="ARTICULO:\n" + articulo[:6000])
        d = _parse_json_seguro(resp)
        if isinstance(d, dict) and "escenas" in d:
            escenas = d["escenas"]
        elif isinstance(d, list):
            escenas = d
        print(f"   Escenas generadas por LLM: {len(escenas)}", flush=True)
    except Exception as e:
        print(f"   ⚠️ LLM falló: {e}", flush=True)

    # Fallback manual: Dividir el artículo en 18 trozos
    # Si hay pocas escenas, forzar un mínimo de 12-15 para garantizar 10 min
    num_escenas_objetivo = 15 if len(escenas) < 12 else len(escenas)
    if len(escenas) < 12:
        print(f"   ⚠️ Solo {len(escenas)} escenas. Forzando {num_escenas_objetivo} para 10 min...", flush=True)
        texto = re.sub(r'<[^>]+>', ' ', articulo)
        texto = re.sub(r'\s+', ' ', texto).strip()
        palabras = texto.split()
        chunk = max(80, len(palabras) // num_escenas_objetivo)
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
    elif len(escenas) < 5:
        print("   Fallback: dividiendo articulo en escenas dinámicas (8-18)", flush=True)
        texto = re.sub(r'<[^>]+>', ' ', articulo)
        texto = re.sub(r'\s+', ' ', texto).strip()
        palabras = texto.split()
        chunk = 150
        num_escenas = max(8, min(18, len(palabras) // chunk))
        moods = ["tension", "misterio", "epico", "inspirador", "electronico", "relax"]
        for i in range(num_escenas):
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
    viral = _parse_json_seguro(pedir_a_especialista("predictor_viralidad", "Puntua este contenido", contexto=json.dumps({"dossier": dossier, "hooks": hooks[:3]}, ensure_ascii=False)[:3000]))
    res["viralidad"] = viral
    print(f"   ✅ Score de viralidad: {viral.get('score', 'N/A')}/100", flush=True)

    # GUARDAR
    out_json = OUT / f"produccion_{fecha}.json"
    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase2] ✅ Guardado en {out_json}", flush=True)
    return res

if __name__ == "__main__":
    producir_fase2(sys.argv[1] if len(sys.argv) > 1 else None)