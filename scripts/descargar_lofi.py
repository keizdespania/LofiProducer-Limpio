"""descargar_lofi.py - Descarga 15 min de Lofi CC aleatorio de YouTube."""
import subprocess, pathlib, sys, random

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
OUT.mkdir(parents=True, exist_ok=True)
destino = OUT / "lofi_base.mp3"

# Lista de directos/vídeos Lofi CC (Lofi Girl, Chillhop, etc.)
URLS_LOFI = [
    "https://www.youtube.com/watch?v=jfKfPfyJRdk", # Lofi Girl
    "https://www.youtube.com/watch?v=5qap5aO4i9A", # Lofi Girl (otro)
    "https://www.youtube.com/watch?v=7NOSDKb0HlU", # Chillhop Music
    "https://www.youtube.com/watch?v=lTRiuFIWV54", # Jazz Hop Cafe
    "https://www.youtube.com/watch?v=DWcJFNfaw9c", # College Music
]

url_hoy = random.choice(URLS_LOFI)
print(f"[Lofi] Descargando track aleatorio: {url_hoy}", flush=True)

if not destino.exists() or destino.stat().st_size < 1024*1024:
    subprocess.run([
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "--download-sections", "*0-900", # 15 minutos exactos
        "-o", str(destino), url_hoy, "--no-warnings", "--force-overwrites"
    ], capture_output=True)
    if destino.exists():
        print(f"[Lofi] ✅ Descargado: {destino.stat().st_size//1024//1024}MB", flush=True)
    else:
        print("[Lofi] ❌ Falló la descarga", flush=True)
        sys.exit(1)
else:
    print("[Lofi] Ya existe lofi_base.mp3, saltando descarga", flush=True)
