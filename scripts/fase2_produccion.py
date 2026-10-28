"""fase2_produccion.py - Orquestador de Fase 2 (Chunking + DJ Real)."""
import sys, json, pathlib, datetime, re, subprocess, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
OUT.mkdir(parents=True, exist_ok=True)

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

def _obtener_musica():
    """Devuelve la lista de archivos de música disponibles."""
    musica_dir = ROOT / "output" / "musica_libre"
    musica_dir.mkdir(parents=True, exist_ok=True)
    archivos = [f.name for f in musica_dir.glob("*.mp3")]
    if not archivos:
        return ["lofi_relax.mp3", "cinematic_tension.mp3", "electronic_future.mp3"] # Fallback
    return archivos

def producir_fase2(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    dossier_file = OUT / f"dossier_{fecha}.json"
    if not dossier_file.exists():
        print(f"[fase2] No existe {dossier_file}")
        return None
    
    datos = json.loads(dossier_file.read_text())
    dossier = datos.get("dossier", {})
    guiones_originales = datos.get("guiones", {})
    hooks = guiones_originales.get("hooks_totales", [])
    
    # 1. ESQUELETO Y ARTÍCULO
    print("[fase2] 1/5 Arquitecto + Redactor...", flush=True)
    ctx_art = json.dumps({"dossier": dossier}, ensure_ascii=False)
    esqueleto = _parse_json_seguro(pedir_a_especialista("arquitecto_contenido", "Crea el esqueleto.", contexto=ctx_art[:2000]))
    articulo = pedir_a_especialista("redactor_blog", "Escribe el artículo HTML.", contexto=ctx_art[:2500])
    articulo = re.sub(r'```(?:html)?', '', articulo).replace('```', '').strip()
    
    # 2. GUION CINEMATOGRÁFICO LARGO (Por momentos)
    print("[fase2] 2/5 Guion Cinematográfico (Largo)...", flush=True)
    guion_texto = guiones_originales.get("guion_video_largo", "Análisis del día")
    prompt_guion = """Divide este texto en MOMENTOS audiovisuales. Devuelve SOLO JSON:
    {"guion": [{"tiempo": "00:00", "texto": "string", "mood": "tension/epico/relax/misterio"}, ...]}"""
    guion_cine = _parse_json_seguro(pedir_a_especialista("guionista_cinematografico", prompt_guion, contexto=guion_texto[:1500]))
    time.sleep(1)
    
    # 3. DJ MUSICAL (Descarga la música según el mood)
    print("[fase2] 3/5 DJ Musical (Descargando música)...", flush=True)
    from descargar_musica_dinamica import descargar_por_mood
    
    # Primero, el DJ analiza qué moods necesita el guion
    ctx_dj = f"GUION: {json.dumps(guion_cine.get('guion', []), ensure_ascii=False)[:1000]}"
    prompt_dj = """Analiza el guion y dime qué moods musicales necesita (tension, epico, relax, misterio, inspirador). Devuelve SOLO JSON:
    {"moods": [{"momento": "00:00", "mood": "string"}]}"""
    mood_analysis = _parse_json_seguro(pedir_a_especialista("dj_musical", prompt_dj, contexto=ctx_dj))
    
    # Descargar la música para cada mood
    pistas = []
    moods_vistos = set()
    for m in mood_analysis.get("moods", []):
        mood = m.get("mood", "relax")
        if mood in moods_vistos: 
            continue
        moods_vistos.add(mood)
        descargas = descargar_por_mood(mood, 1)
        if descargas:
            pistas.append({"momento": m.get("momento", "00:00"), "mood": mood, "archivo": descargas[0]["archivo"]})
            print(f"   🎵 {mood}: {descargas[0]['archivo']}")
    
    musica = {"pistas": pistas}
    time.sleep(1)
    
    # 4. SHORTS (En lotes de 2 para no colapsar)
    print("[fase2] 4/5 Selector de Hooks y Guiones de Shorts...", flush=True)
    shorts_finales = []
    for i in range(0, min(len(hooks), 24), 2):
        lote = hooks[i:i+2]
        print(f"   -> Procesando lote {i//2 + 1} (hooks {i+1}-{i+len(lote)})...", flush=True)
        prompt_short = """Convierte estos hooks en guiones de 30s. Devuelve SOLO JSON:
        {"shorts": [{"id": "string", "tipo": "string", "hook": "string", "guion": "string"}]}"""
        res_lote = _parse_json_seguro(pedir_a_especialista("guionista_cinematografico", prompt_short, contexto=json.dumps(lote, ensure_ascii=False)[:1000]))
        if res_lote.get("shorts"):
            shorts_finales.extend(res_lote["shorts"])
        time.sleep(1)
    
    if not guion_cine.get("guion") or len(guion_cine.get("guion")) == 0:
        print("🛑 FATAL: El guion cinematográfico está vacío. Abortando para no guardar basura.")
        return None

    # 5. SEO MAESTRO
    print("[fase2] 5/5 SEO Maestro...", flush=True)
    prompt_seo = """Genera el SEO. Devuelve SOLO JSON:
    {"youtube": {"titulo": "string", "descripcion": "string", "tags": ["string"]}, "tiktok": {"texto": "string"}, "instagram": {"texto": "string"}}"""
    seo = _parse_json_seguro(pedir_a_especialista("seo_maestro", prompt_seo, contexto=f"Tema: {dossier.get('tema_del_dia')}"))

    # GUARDAR
    res = {
        "fecha": fecha,
        "esqueleto": esqueleto,
        "articulo_html": articulo,
        "guion_cinematografico": guion_cine,
        "musica": musica,
        "shorts_finales": shorts_finales,
        "seo": seo,
    }
    out_json = OUT / f"produccion_{fecha}.json"
    # Usar el guion original (1500 palabras) como texto para la voz
    res["texto_voz_largo"] = guiones_originales.get("guion_video_largo", "")

    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase2] ✅ Guardado en {out_json}")
    return res

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    producir_fase2(fecha)
