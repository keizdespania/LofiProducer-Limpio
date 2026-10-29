"""director_arte.py - Prepara assets visuales (40% video / 60% imagen) y musica por escena."""
import subprocess
import sys, json, pathlib, shutil, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MERCH = ROOT / "output" / "merch"
MUSICA = ROOT / "output" / "musica_temp"
VIDEOS = ROOT / "output" / "encuadre" / "videos"
for d in [MEDIA, MERCH, MUSICA, VIDEOS]: d.mkdir(parents=True, exist_ok=True)


# Traducción conceptual visual ES->EN (Coverr/Pexels buscan en inglés)
_VISUAL_MAP = {
    "redaccion":"newsroom", "periodico":"newspaper", "periodicos":"newspapers",
    "escritorio":"office", "oficina":"office", "pantalla":"screen", "luces":"lights",
    "ciudad":"city", "noche":"night", "calle":"street", "edificio":"building",
    "gobierno":"government", "politica":"politics", "politico":"politician",
    "justicia":"justice", "tribunal":"courthouse", "juez":"judge",
    "dinero":"money", "economia":"economy", "banco":"bank",
    "policia":"police", "coche":"car", "coches":"cars",
    "manifestacion":"protest", "protesta":"protest", "gente":"people", "multitud":"crowd",
    "papel":"paper", "documento":"document", "datos":"data", "grafico":"chart",
    "cristal":"glass", "roto":"broken", "espejo":"mirror", "sombra":"shadow",
    "vacio":"empty", "oscuridad":"darkness", "tenue":"dim", "brillante":"bright",
    "animacion":"animation", "pastel":"cake", "tarta":"cake", "cuchillo":"knife",
    "silla":"chair", "sala":"room", "experto":"expert", "entrevista":"interview",
    "logotipo":"logo", "texto":"text", "cartel":"sign", "titular":"headline",
    "rompecabezas":"puzzle", "piezas":"puzzle pieces", "numerico":"numeric",
    "frenetico":"frenetic", "frenetica":"frenetic", "desordenado":"messy",
    "intermitente":"flashing", "detalle":"closeup", "primer plano":"closeup",
    "movimiento":"motion", "rapido":"fast", "lento":"slow", "camara":"camera",
    "fondo":"background", "primer":"first", "central":"central",
    "caida":"fall", "sistema":"system", "señal":"signal", "control":"control",
    "ordenador":"computer", "portatil":"laptop", "television":"tv", "microfono":"microphone",
    "audifonos":"headphones", "radio":"radio", "prensa":"press", "medios":"media",
    "masculino":"man", "hombre":"man", "mujer":"woman", "persona":"person",
}

_SUSTANTIVOS_FUERTES = {"redaccion","periodico","periodicos","ciudad","calle","edificio",
    "gobierno","policia","coche","coches","manifestacion","protesta","gente","multitud",
    "documento","datos","cristal","espejo","pastel","tarta","cuchillo","silla","sala",
    "experto","entrevista","logotipo","cartel","titular","rompecabezas","piezas",
    "ordenador","television","microfono","radio","prensa","medios","pantalla",
    "dinero","banco","juez","tribunal","justicia","politico","sombra","vacio","noche"}

def _traducir_visual(concepto):
    """Devuelve 1-2 palabras clave (sustantivos fuertes) para Coverr."""
    c = concepto.lower()
    hits = []
    # 1ª pasada: solo sustantivos fuertes
    for es, en in _VISUAL_MAP.items():
        if es in _SUSTANTIVOS_FUERTES and es in c and en not in hits:
            hits.append(en)
    # 2ª pasada: si <1, cualquier término
    if not hits:
        for es, en in _VISUAL_MAP.items():
            if es in c and en not in hits:
                hits.append(en)
    if not hits:
        palabras = [w for w in c.replace(","," ").split() if len(w) > 5][:2]
        hits = palabras if palabras else ["cinematic"]
    return " ".join(hits[:2])  # máximo 2 palabras para Coverr

_GENERIC_FALLBACK = ["city night", "office people", "dark cinematic", "government building", "money finance", "police cars", "newspaper"]

def _descargar_video(concepto, salida):
    try:
        from descargar_videos_stock import buscar_coverr
        query_en = _traducir_visual(concepto)
        print(f"    traduccion: '{query_en}'", flush=True)
        # Pedir 3 resultados y elegir por matches de tags
        res = buscar_coverr(query_en, 3)
        if res and len(res) > 1:
            # Re-rank por cuántos términos de query están en tags/title
            terms = query_en.lower().split()
            def _score(r):
                blob = (r.get("query","") + " " + str(r.get("titulo",""))).lower()
                return sum(1 for t in terms if t in blob)
            res = sorted(res, key=_score, reverse=True)
            print(f"    rerank: {len(res)} hits -> '{res[0].get('titulo','')}'", flush=True)
        if not res:
            for fb in _GENERIC_FALLBACK:
                print(f"    retry generico: '{fb}'", flush=True)
                res = buscar_coverr(fb, 1)
                if res: break
        if res:
            archivo = res[0]["archivo"]
            ruta = VIDEOS / archivo
            if ruta.exists():
                shutil.copy2(ruta, salida)
                return True
            print(f"    no existe {ruta}", flush=True)
        else:
            print(f"    0 resultados incluso con fallback", flush=True)
    except Exception as e:
        print(f"    video fail: {e}", flush=True)
    return False


def _asegurar_ingles(concepto):
    """Si el concepto tiene castellano residual, lo traduce a inglés con LLM."""
    import re as _re
    # Castellano básico: palabras con ñ, tildes, o palabras comunes
    ES_WORDS = ["periódico", "periodico", "francés", "frances", "ciudadano", "imagen",
                "primer plano", "luz", "dramática", "dramatica", "apilado", "titular",
                "ventana", "calle", "sombra", "gobierno", "político", "politico"]
    es = any(w in concepto.lower() for w in ES_WORDS)
    if not es and not _re.search(r"[ñáéíóú]", concepto.lower()):
        return concepto
    # Traducir con Groq
    try:
        sys.path.insert(0, str(ROOT / "brain"))
        from especialistas import pedir_a_especialista
        r = pedir_a_especialista(
            "traductor_formatos",
            "Traduce al INGLÉS este prompt visual para SDXL. Devuelve SOLO el prompt en inglés, 8-15 palabras, estilo cinematic. Sin comillas, sin explicaciones.",
            contexto=concepto, proveedor="omni")
        r = r.strip().strip('"').strip("'")
        if r and len(r) > 10 and not _re.search(r"[ñáéíóú]", r.lower()):
            print(f"    EN: {r[:80]}", flush=True)
            return r
    except Exception as e:
        print(f"    traduccion fallo: {e}", flush=True)
    return concepto

def _generar_imagen(concepto, salida):
    try:
        from generar_imagen import generar
        concepto_en = _asegurar_ingles(concepto)
        r = generar(concepto_en + ", cinematic, no text, high detail", preset="cinematic", aspect="16:9", canal="encuadre")
        if 'OK: ' in r:
            ruta = r.split('OK: ')[1].split(' ')[0]
            if pathlib.Path(ruta).exists():
                shutil.copy2(ruta, salida)
                return True
    except Exception as e:
        print(f"    img fail: {e}")
    return False

def _descargar_musica(mood, salida):
    try:
        from descargar_musica_dinamica import descargar_por_mood
        res = descargar_por_mood(mood, 1)
        if res:
            nombre = res[0]["archivo"]
            ruta = MUSICA / nombre
            if ruta.exists():
                shutil.copy2(ruta, salida)
                return True
    except Exception as e:
        print(f"    musica fail: {e}")
    return False

def preparar(fecha):
    prod = OUT / f"produccion_{fecha}.json"
    if not prod.exists():
        print("No hay produccion"); return
    datos = json.loads(prod.read_text())
    escenas = datos.get("escenas", [])
    if not escenas:
        print("No hay escenas"); return

    print(f"Director de Arte: {len(escenas)} escenas")
    _SOLO_SDXL = True  # RUTA A: solo imagenes SDXL
    for e in escenas:
        num = e["id"]
        if _SOLO_SDXL: e["tipo_visual"] = "imagen"
        tipo = e.get("tipo_visual", "imagen")
        concepto = e.get("concepto_visual", "abstract")
        mood = e.get("mood_musical", "relax")

        if tipo == "video":
            video = MEDIA / f"escena_{num:02d}.mp4"
            if not video.exists():
                print(f"  [{num}] video: {concepto[:40]}")
                if not _descargar_video(concepto, video):
                    print(f"  [{num}] fallback a imagen")
                    _generar_imagen(concepto, MEDIA / f"escena_{num:02d}.png")
                    e["tipo_visual"] = "imagen"
        else:
            img = MEDIA / f"escena_{num:02d}.png"
            if not img.exists():
                print(f"  [{num}] imagen: {concepto[:40]}")
                _generar_imagen(concepto, img)
                if img.exists():
                    shutil.copy2(img, MERCH / f"merch_{fecha}_{num:02d}.png")

        mus = MUSICA / f"escena_{num:02d}.mp3"
        if not mus.exists():
            print(f"  [{num}] musica: {mood}")
            _descargar_musica(mood, mus)

        time.sleep(0.5)

    # Generar imagen vertical para los shorts (9:16)
    short_bg = MEDIA / "short_bg_01.png"
    if not short_bg.exists():
        print("  Generando short_bg 9:16...")
        ok_bg = False
        try:
            from generar_imagen import generar
            r = generar("cinematic dark news vertical composition, dramatic lighting, no text", preset="cinematic", aspect="9:16", canal="encuadre")
            if "OK: " in r:
                ruta = r.split("OK: ")[1].split(" ")[0]
                if pathlib.Path(ruta).exists():
                    shutil.copy2(ruta, short_bg); ok_bg = True
                    print("  short_bg via SDXL")
        except Exception as e:
            print(f"  SDXL fallback: {e}")
        if not ok_bg or not short_bg.exists():
            subprocess.run(["ffmpeg","-y","-f","lavfi","-i","color=c=0x0a0a0f:s=1080x1920:d=1","-frames:v","1",str(short_bg)], capture_output=True)
            print("  short_bg via FFmpeg (color)")

    prod.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
    print(f"OK {len(escenas)} escenas preparadas")

if __name__ == "__main__":
    preparar(sys.argv[1] if len(sys.argv) > 1 else None)
