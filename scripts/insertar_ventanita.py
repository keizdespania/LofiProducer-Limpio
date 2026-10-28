"""insertar_ventanita.py - Superpone un clip PiP en el vídeo principal."""
import subprocess, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def extraer_clip(youtube_url, salida, inicio="00:00:10", duracion=3):
    """Descarga solo un fragmento de 3 segundos con yt-dlp (no todo el vídeo)."""
    cmd = [
        "yt-dlp", youtube_url,
        "--download-sections", f"*{inicio}-{inicio}+{duracion}",
        "-f", "bestvideo[height<=720]+bestaudio",
        "-o", str(salida), "--no-playlist"
    ]
    subprocess.run(cmd, capture_output=True)
    return salida if salida.exists() else None

def superponer_ventanita(video_principal, clip_pip, salida, tiempo_inicio=5):
    """Superpone el clip PiP en la esquina superior derecha."""
    # Filtro: el clip se escala a 1/4 y se superpone a partir de 'tiempo_inicio'
    filtro = f"[1:v]scale=480:-1[pip];[0:v][pip]overlay=W-w-20:20:enable='between(t,{tiempo_inicio},{tiempo_inicio+3})'"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_principal), "-i", str(clip_pip),
        "-filter_complex", filtro,
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-c:a", "copy", str(salida)
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return salida if r.returncode == 0 else None

if __name__ == "__main__":
    # Uso: python3 insertar_ventanita.py VIDEO_PRINCIPAL URL_YOUTUBE
    if len(sys.argv) < 3:
        print("Uso: python3 insertar_ventanita.py video_principal.mp4 URL_YOUTUBE")
        sys.exit(1)
    video_principal = sys.argv[1]
    youtube_url = sys.argv[2]
    clip = OUT / "clip_pip.mp4"
    if extraer_clip(youtube_url, clip):
        print("✅ Clip extraído")
        final = superponer_ventanita(video_principal, clip, OUT / "video_con_pip.mp4")
        print(f"✅ Vídeo con ventanita: {final}")
    else:
        print("❌ Fallo al extraer clip")
