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
    res["articulo_html"] = articulo
    res["esqueleto"] = esqueleto

    # 2. GUION DE YOUTUBE (Experto en retención)
    print("[fase2] 2/5 Guionista YouTube Experto: guion de 10 min...", flush=True)
    guion_youtube = ""
    try:
        prompt_guion = "Escribe un guion completo de YouTube de MÍNIMO 1500 palabras basado en este artículo. Sigue la estructura de retención (hook, open loops, micro-hooks, payoff)."
        guion_youtube = pedir_a_especialista("guionista_youtube_experto", prompt_guion, contexto=f"ARTÍCULO:\n{articulo[:6000]}")
        palabras = len(guion_youtube.split())
        print(f"   ✅ Guion generado: {palabras} palabras (~{palabras//150} min)", flush=True)
    except Exception as e:
        print(f"   ⚠️ Error generando guion: {e}", flush=True)
    
    if len(guion_youtube.split()) < 100:
        print("   ⚠️ El guion es demasiado corto. Usando el artículo como fallback.", flush=True)
        texto_limpio = re.sub(r'<[^>]+>', ' ', articulo)
        guion_youtube = re.sub(r'\s+', ' ', texto_limpio).strip()

    res["guion_cinematografico"] = {"guion": [{"tiempo": "00:00", "texto": guion_youtube, "mood": "tension"}]}
    res["texto_voz_largo"] = guion_youtube # Álvaro leerá esto

    # 3. DJ MUSICAL
    print("[fase2] 3/5 DJ Musical...", flush=True)
    from descargar_musica_dinamica import descargar_por_mood
    moods = set([e.get("mood", "relax") for e in res["guion_cinematografico"]["guion"]])
    for m in moods:
        if m: descargar_por_mood(m, 1)
    res["musica"] = {"pistas": list(moods)}

    # 4. SHORTS
    print("[fase2] 4/5 Selector de Hooks y Guiones de Shorts...", flush=True)
    shorts_finales = []
    for i in range(0, min(len(hooks), 8), 2):
        lote = hooks[i:i+2]
        prompt_short = """Convierte estos hooks en guiones de 30s. Devuelve SOLO JSON: {"shorts": [{"id": "string", "tipo": "string", "hook": "string", "guion": "string"}]}"""
        res_lote = _parse_json_seguro(pedir_a_especialista("guionista_cinematografico", prompt_short, contexto=json.dumps(lote, ensure_ascii=False)))
        
        if res_lote.get("shorts") and isinstance(res_lote["shorts"], list) and len(res_lote["shorts"]) > 0:
            shorts_finales.extend(res_lote["shorts"])
        else:
            # Fallback de emergencia: usar el hook como guion
            print(f"   ⚠️ LLM falló en lote {i}. Usando fallback.", flush=True)
            for j, h in enumerate(lote):
                shorts_finales.append({
                    "id": f"short_{i+j+1}",
                    "tipo": h.get("tipo", "Dato"),
                    "hook": h.get("hook", "Análisis del día"),
                    "guion": h.get("hook", "Análisis del día") + ". Lee el análisis completo en elencuadre.pages.dev"
                })
    res["shorts_finales"] = shorts_finales
    print(f"   ✅ {len(shorts_finales)} shorts generados.")

    # 5. SEO MAESTRO
    print("[fase2] 5/5 SEO Maestro...", flush=True)
    prompt_seo = "Genera el SEO. Devuelve SOLO JSON: {\"youtube\": {\"titulo\": \"string\", \"descripcion\": \"string\"}, \"tiktok\": {\"texto\": \"string\"}, \"instagram\": {\"texto\": \"string\"}, \"x\": {\"texto\": \"string\"}}"
    res["seo"] = _parse_json_seguro(pedir_a_especialista("seo_maestro", prompt_seo, contexto=f"Tema: {dossier.get('tema_del_dia')}"))

    # GUARDAR
    out_json = OUT / f"produccion_{fecha}.json"
    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase2] ✅ Guardado en {out_json}", flush=True)
    return res

if __name__ == "__main__":
    producir_fase2(sys.argv[1] if len(sys.argv) > 1 else None)
