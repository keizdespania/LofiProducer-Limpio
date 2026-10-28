"""hack_compartir_tiktok.py - Comparte el short directamente a la app de TikTok."""
import subprocess, pathlib, sys, datetime, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
fecha = datetime.date.today().isoformat()

def compartir_a_tiktok(video_path, texto):
    if not pathlib.Path(video_path).exists():
        print(f"❌ No existe el vídeo: {video_path}")
        return False
    
    try:
        subprocess.run(["termux-clipboard-set", texto], check=False)
        print("📋 Texto copiado al portapapeles.")
    except: pass
    
    print("🚀 Abriendo menú de compartir de Android...")
    try:
        subprocess.run(["termux-share", "-a", "send", "-c", "video/mp4", str(video_path)], check=False)
        print("✅ Menú abierto. Selecciona TikTok en la lista.")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    video = OUT / f"short_{fecha}.mp4"
    redes_file = OUT / f"redes_{fecha}.json"
    
    texto = "Análisis del día. #fyp #parati #medios"
    if redes_file.exists():
        try:
            data = json.loads(redes_file.read_text())
            texto = data.get("tiktok", texto)
        except: pass
    
    if not video.exists():
        videos = sorted(OUT.glob("short_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if videos: video = videos[0]
    
    if video.exists():
        print(f"🎬 Usando vídeo: {video.name}")
        compartir_a_tiktok(video, texto)
    else:
        print("❌ No hay ningún short generado todavía. Lanza el pipeline primero.")
