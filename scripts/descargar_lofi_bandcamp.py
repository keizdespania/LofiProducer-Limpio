"""descargar_lofi_bandcamp.py - Descarga 1 track CC0 de HoliznaCC0 (Bandcamp) y lo buclea a 15 min."""
import subprocess, pathlib, sys, random, glob

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
OUT.mkdir(parents=True, exist_ok=True)
destino = OUT / "lofi_base.mp3"

# Lista de tracks de HoliznaCC0 en Bandcamp (CC0)
TRACKS = [
    "https://holiznacc0.bandcamp.com/track/tokyo-sunset",
    "https://holiznacc0.bandcamp.com/track/lofi-dreams",
    "https://holiznacc0.bandcamp.com/track/chill-vibes",
    "https://holiznacc0.bandcamp.com/track/midnight-coffee",
    "https://holiznacc0.bandcamp.com/track/rainy-day",
    "https://holiznacc0.bandcamp.com/track/sunset-drive",
    "https://holiznacc0.bandcamp.com/track/late-night-study",
    "https://holiznacc0.bandcamp.com/track/tranquil-mindset",
]

def descargar_track():
    url = random.choice(TRACKS)
    print(f"[Bandcamp] Descargando track CC0: {url}", flush=True)
    
    tmp_dir = OUT / "bandcamp_tmp"
    tmp_dir.mkdir(exist_ok=True)
    
    try:
        subprocess.run([
            "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
            "-o", str(tmp_dir / "%(id)s.%(ext)s"), url, "--no-warnings", "--force-overwrites"
        ], check=True, timeout=180, capture_output=True)
        
        mp3s = list(tmp_dir.glob("*.mp3"))
        if not mp3s:
            print("[Bandcamp] ❌ No se descargó ningún MP3", flush=True)
            return False
        
        track_original = mp3s[0]
        print(f"[Bandcamp] ✅ Descargado: {track_original.name}", flush=True)
        
        # Repetir el track hasta llegar a 15 minutos (900s)
        print(f"[Bandcamp] Repitiendo el track para llegar a 15 min...", flush=True)
        lista = tmp_dir / "concat.txt"
        with open(lista, "w") as f:
            for _ in range(15): # 15 repeticiones (suficiente para cualquier track)
                f.write(f"file '{track_original.absolute()}'\n")
        
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(lista),
            "-t", "900", "-c:a", "libmp3lame", "-b:a", "192k", str(destino)
        ], check=True, timeout=120)
        
        # Limpiar temporales
        for m in mp3s: m.unlink(missing_ok=True)
        lista.unlink(missing_ok=True)
        
        if destino.exists() and destino.stat().st_size > 100000:
            print(f"[Bandcamp] ✅ Guardado en {destino} ({destino.stat().st_size//1024//1024}MB)", flush=True)
            return True
    except Exception as e:
        print(f"[Bandcamp] ❌ Fallo: {e}", flush=True)
    return False

if __name__ == "__main__":
    if destino.exists() and destino.stat().st_size > 1024*1024:
        print("[Bandcamp] Ya existe lofi_base.mp3, saltando."); sys.exit(0)
    if not descargar_track():
        print("[Bandcamp] ❌ Fallo total. Generando silencio de 15 min.", flush=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "900", "-c:a", "libmp3lame", str(destino)], check=True)
        sys.exit(1)
