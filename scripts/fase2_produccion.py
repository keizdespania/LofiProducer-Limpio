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
    if len(escenas) < 5:
        print("   Fallback: dividiendo articulo en 18 escenas", flush=True)
        texto = re.sub(r'<[^>]+>', ' ', articulo)
        texto = re.sub(r'\s+', ' ', texto).strip()
        palabras = texto.split()
        
        # Asegurar mínimo 1800 palabras para que salgan 18 escenas de 100 palabras
        if len(palabras) < 1800:
            palabras = palabras * (1800 // max(1, len(palabras)) + 1)
            palabras = palabras[:1800]
            
        chunk = len(palabras) // 18
        moods = ["tension", "misterio", "epico", "inspirador", "electronico", "relax"]
        
        for i in range(18):
            ini = i * chunk
            fin_i = min(len(palabras), (i+1) * chunk)
            if ini >= len(palabras): break
            escenas.append({
                "id": i + 1,
                "texto": " ".join(palabras[ini:fin_i]),
                "concepto_visual": "cinematic dark news analysis, abstract concept " + str(i+1),
                "mood_musical": moods[i % len(moods)],
                "tipo_visual": "video" if i == 0 or i % 3 == 0 else "imagen"
            })

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
