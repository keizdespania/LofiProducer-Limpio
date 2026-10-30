"""descargar_lofi.py - Descarga 15 min de Lofi CC para el fondo."""
import subprocess, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
OUT.mkdir(parents=True, exist_ok=True)
destino = OUT / "lofi_base.mp3"

# Lofi Girl - "Lofi hip hop radio - beats to relax/study to" (CC)
URL = "https://www.youtube.com/watch?v=jfKfPfyJRdk"

if not destino.exists() or destino.stat().st_size < 1024*1024:
    print("[Lofi] Descargando 15 min de Lofi CC...", flush=True)
    subprocess.run([
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "--download-sections", "*0-900",
        "-o", str(destino), URL, "--no-warnings", "--force-overwrites"
    ], capture_output=True)
    if destino.exists():
        print(f"[Lofi] ✅ Descargado: {destino.stat().st_size//1024//1024}MB", flush=True)
    else:
        print("[Lofi] ❌ Falló la descarga", flush=True)
        sys.exit(1)
else:
    print("[Lofi] Ya existe lofi_base.mp3, saltando descarga", flush=True)
