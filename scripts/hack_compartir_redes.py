"""hack_compartir_redes.py - Comparte vídeo y copia texto para todas las redes."""
import subprocess, pathlib, sys, datetime, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
fecha = datetime.date.today().isoformat()

def compartir_red(red, video_path, texto):
    if not pathlib.Path(video_path).exists():
        print(f"❌ No existe el vídeo: {video_path}")
        return False
    
    try:
        subprocess.run(["termux-clipboard-set", texto], check=False)
        print(f"📋 Texto para {red.capitalize()} copiado al portapapeles.")
    except: pass
    
    if red == "youtube_comunidad":
        print("🚀 Abriendo YouTube Comunidad...")
        try:
            subprocess.run(["termux-open-url", "https://www.youtube.com/@SomosElEncuadre/community"], check=False)
        except Exception as e:
            print(f"❌ Error: {e}")
        return True
    
    print(f"🚀 Abriendo menú de compartir para {red.capitalize()}...")
    try:
        subprocess.run(["termux-share", "-a", "send", "-c", "video/mp4", str(video_path)], check=False)
        print(f"✅ Selecciona {red.capitalize()} en la lista de apps.")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/hack_compartir_redes.py [tiktok|instagram|x|threads|youtube_comunidad]")
        sys.exit(1)
    
    red = sys.argv[1].lower()
    if red == "twitter": red = "x"
    
    if red not in ("tiktok", "instagram", "x", "threads", "youtube_comunidad"):
        print("❌ Red no válida.")
        sys.exit(1)

    video = OUT / f"short_1_{fecha}.mp4"
    if not video.exists():
        videos = sorted(OUT.glob("short_1_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if videos: video = videos[0]
    
    texto = "Análisis del día en Somos El Encuadre."
    redes_file = OUT / f"redes_{fecha}.json"
    
    if redes_file.exists():
        try:
            data = json.loads(redes_file.read_text())
            if "shorts" in data and len(data["shorts"]) > 0:
                short_1 = data["shorts"][0]
                if red == "youtube_comunidad":
                    yt = short_1.get("youtube", {})
                    texto = f"📢 Nuevo análisis: {yt.get('titulo', '')}\n\n{yt.get('descripcion', '')}\n\nLee el análisis completo en: https://elencuadre.pages.dev"
                else:
                    red_data = short_1.get(red, {})
                    if isinstance(red_data, dict):
                        texto = red_data.get("texto", texto)
                        if red_data.get("hashtags"):
                            texto += " " + red_data["hashtags"]
                    elif isinstance(red_data, str):
                        texto = red_data
        except Exception as e:
            print(f"⚠️ Error leyendo JSON: {e}")
    
    if video.exists():
        print(f"🎬 Usando vídeo: {video.name}")
        compartir_red(red, video, texto)
    else:
        print("❌ No hay ningún short generado.")

if __name__ == "__main__":
    main()
