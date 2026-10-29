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

def _descargar_video(concepto, salida):
    try:
        from descargar_videos_stock import buscar_coverr
        res = buscar_coverr(concepto, 1)
        if res:
            archivo = res[0]["archivo"]
            ruta = VIDEOS / archivo
            if ruta.exists():
                shutil.copy2(ruta, salida)
                return True
    except Exception as e:
        print(f"    video fail: {e}")
    return False

def _generar_imagen(concepto, salida):
    try:
        from generar_imagen import generar
        r = generar(concepto + ", cinematic, dark, no text", preset="cinematic", aspect="16:9", canal="encuadre")
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
    for e in escenas:
        num = e["id"]
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
        print("  🖼️ Generando imagen vertical (9:16) para shorts...")
        from generar_imagen import generar
        r = generar("cinematic dark news analysis, vertical composition, dramatic lighting, no text", preset="cinematic", aspect="9:16", canal="encuadre")
        if 'OK: ' in r:
            ruta = r.split('OK: ')[1].split(' ')[0]
            if pathlib.Path(ruta).exists():
                shutil.copy2(ruta, short_bg)
                print("  ✅ Imagen vertical creada")

    prod.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
    print(f"OK {len(escenas)} escenas preparadas")

if __name__ == "__main__":
    preparar(sys.argv[1] if len(sys.argv) > 1 else None)
