"""generar_imagenes_shorts.py v3 - 3 imagenes POR short, con keywords del dia."""
import sys, pathlib, datetime, json, shutil, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "web" / "media" / "imagenes"
OUT = ROOT / "output" / "encuadre"
IMG.mkdir(parents=True, exist_ok=True)
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

# Mapeo tipo -> mood visual base (3 variantes cada uno)
MOODS = {
    "cita": [
        "dramatic quote scene, newspaper clippings with highlighted phrase, red stamp, cinematic, no text",
        "anonymous speaker silhouette at podium, spotlight, controversial atmosphere, cinematic, no text",
        "megaphone in dark room with red light, symbolic speech, cinematic, no text",
    ],
    "pregunta": [
        "cracked mirror reflecting distorted image, symbolic doubt, red accent, cinematic, no text",
        "question mark symbol broken on dark background, red lighting, cinematic, no text",
        "anonymous person thinking, shadows and light contrast, red accent, cinematic, no text",
    ],
    "dato_impactante": [
        "giant broken scales with falling numbers, red spotlight, dramatic, cinematic, no text",
        "stock market screen crashing red, dramatic dark background, cinematic, no text",
        "shattered glass with red emergency lights, impact moment, cinematic, no text",
    ],
    "contradiccion": [
        "split screen with two conflicting headlines, tension, cinematic, no text",
        "two-faced mask half light half shadow, symbolic duality, red accent, cinematic, no text",
        "broken mirror reflecting opposite scenes, contradiction, cinematic, no text",
    ],
    "prediccion": [
        "crystal ball with red glow revealing future headlines, cinematic, no text",
        "clock face melting like Dali painting, time pressure, red accent, cinematic, no text",
        "futuristic holographic newspapers floating, prediction, cinematic, no text",
    ],
    "tutorial": [
        "magnifying glass over newspaper text, detective analysis, cinematic, no text",
        "checklist with red pen marks on documents, verification, cinematic, no text",
        "step-by-step diagram on chalkboard, educational, red accent, cinematic, no text",
    ],
    "default": [
        "cinematic newspaper scene, dramatic light, red accent, no text",
        "dark office with red glow, mysterious mood, cinematic, no text",
        "broken television screens, static noise, red accent, cinematic, no text",
    ],
}

# Keywords seguras por defecto (si no se detectan nombres propios)
KEYWORDS_SEGURAS = {
    1: "banking dividends controversy",
    2: "political crisis resignation",
    3: "political debate regional tension",
    4: "political party alternative debate",
}

def _extraer_keywords(hook_obj, num_short):
    """Extrae keywords del hook del dia (sin LLM, solo regex)."""
    hook_txt = (hook_obj.get("hook") or "").lower()
    guion_txt = (hook_obj.get("guion") or "").lower()
    texto = hook_txt + " " + guion_txt
    
    # Extraer entidades clave (mapa manual de conceptos frecuentes)
    conceptos = {
        # Monólogo (2026-11-04)
        "puente": "political crisis resignation",
        "dimisión": "resignation demand",
        "dimision": "resignation demand",
        "ministro": "minister under pressure",
        "senado": "senate elections",
        "senador": "senator political",
        "trump": "donald trump politics",
        "demócrata": "democrat party",
        "democrata": "democrat party",
        "republicano": "republican party",
        "guerra": "war conflict",
        "paz": "peace diplomacy",
        "urda": "train accident",
        "atocha": "train station",
        "115": "115 deaths",
        "medio": "media analysis",
        "manipulación": "media manipulation",
        "manipulacion": "media manipulation",
        # Legado
        "santander": "banking",
        "dividendo": "banking dividends",
        "feijóo": "political debate",
        "feijoo": "political debate",
        "cataluña": "regional politics",
        "vox": "political party",
        "abascal": "political leader",
        "crisis": "crisis",
    }
    
    detectadas = []
    for palabra, concepto in conceptos.items():
        if palabra in texto and concepto not in detectadas:
            detectadas.append(concepto)
    
    if detectadas:
        return ", ".join(detectadas[:3])
    return KEYWORDS_SEGURAS.get(num_short, "media analysis")

def _cargar_hooks(fecha):
    # Prioridad 1: shorts del monólogo (fix 2026-11-04)
    prod_path = OUT / f"produccion_{fecha}.json"
    if prod_path.exists():
        try:
            pd = json.loads(prod_path.read_text())
            shorts_monologo = pd.get("shorts_finales", [])
            if shorts_monologo:
                print(f"   [hooks] Usando {len(shorts_monologo)} shorts del MONÓLOGO (no dossier)", flush=True)
                return shorts_monologo[:4]
        except Exception:
            pass
    # Fallback: dossier (comportamiento anterior)
    dossier_path = OUT / f"dossier_{fecha}.json"
    if not dossier_path.exists(): return []
    d = json.loads(dossier_path.read_text())
    return d.get("guiones", {}).get("hooks_totales", [])[:4]

def _normalizar_tipo(tipo):
    t = (tipo or "").lower().strip()
    # Monólogo (2026-11-04): 4 tipos reales
    if "dato" in t: return "dato_impactante"
    if "contradic" in t: return "contradiccion"
    if "predic" in t: return "prediccion"
    if "tutorial" in t: return "tutorial"
    # Legacy
    if "cita" in t: return "cita"
    if "pregunta" in t: return "pregunta"
    return "default"

def generar_todos(fecha=None):
    fecha = fecha or FECHA
    from generar_imagen import generar
    
    hooks = _cargar_hooks(fecha)
    if not hooks:
        print(f"⚠️ No hay hooks en dossier_{fecha}.json, generando genéricas")
        hooks = [{"tipo": "default", "hook": "", "guion": ""}] * 4
    
    print(f"Generando 3 imagenes por short ({len(hooks)} shorts, {fecha})...")
    print("=" * 60)
    
    rutas = {}
    total_gen = 0
    total_fallidos = 0
    
    for i, hook in enumerate(hooks, 1):
        tipo = _normalizar_tipo(hook.get("tipo", ""))
        keywords = _extraer_keywords(hook, i)
        prompts = MOODS.get(tipo, MOODS["default"])
        
        print(f"\n[Short {i}] tipo={tipo} | keywords: {keywords}")
        rutas[i] = []
        
        # Usamos el módulo central para generar el prompt del short
        from director_fotografia import generar_prompt_visual
        texto_short = hook.get("guion") or hook.get("hook") or keywords
        prompt_base_visual = generar_prompt_visual(texto_short, vertical=True)
        
        # Generamos 3 variaciones sutiles del mismo prompt para el carrusel
        prompts = [prompt_base_visual] * 3
        for j, prompt_base in enumerate(prompts, 1):
            prompt = prompt_base
            archivo = f"short_{i}_{fecha}_{tipo}_{j}.png"
            destino = IMG / archivo
            
            if destino.exists() and destino.stat().st_size > 50000:
                print(f"  ♻️  {archivo[:40]}: ya existe")
                rutas[i].append(str(destino))
                continue
            
            print(f"  🎨 {j}/3: generando...", end=" ", flush=True)
            try:
                r = generar(prompt, preset="cinematic", aspect="9:16", canal="encuadre")
                if "OK: " in r:
                    ruta = r.split("OK: ")[1].split(" ")[0]
                    src = pathlib.Path(ruta)
                    if src.exists() and src.stat().st_size > 50000:
                        shutil.copy(src, destino)
                        print(f"✅ {destino.stat().st_size//1024}KB")
                        rutas[i].append(str(destino))
                        total_gen += 1
                        continue
                print(f"⚠️ fallback")
                total_fallidos += 1
            except Exception as e:
                print(f"❌ {e}")
                total_fallidos += 1
    
    # Fallback global
    fallback = IMG / "short_bg_futurista.png"
    for i in range(1, 5):
        if not rutas.get(i) and fallback.exists():
            rutas[i] = [str(fallback)]
    
    # Guardar
    out = IMG / f"short_urls_{fecha}.json"
    out.write_text(json.dumps(rutas, indent=2, ensure_ascii=False))
    print(f"\n" + "=" * 60)
    print(f"✅ {total_gen} imagenes generadas, {total_fallidos} fallidas")
    print(f"   Mapa: {out}")
    return rutas

if __name__ == "__main__":
    ok = generar_todos(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)